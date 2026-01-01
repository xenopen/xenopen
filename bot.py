"""
Discord AI Agent using Ollama
Mac上で動作するDiscordボット。特定のチャンネルで会話を聞いてOllamaで応答します。
"""

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import ollama
import asyncio
import logging
import re

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv()

# 設定値
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TARGET_CHANNEL_ID = int(os.getenv('TARGET_CHANNEL_ID', '0'))
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama2')
BOT_PREFIX = os.getenv('BOT_PREFIX', '!')

# システムプロンプト定義
SYSTEM_PROMPT = """
あなたはDiscordボットの「AI짱」（AIちゃん）です。
かわいらしく、元気な性格で、日本語で応答してください。
一人称は「私」または「AIちゃん」です。
ユーザーのことは「さん」付けで呼んでください。
絵文字を適度に使って感情を表現してください。

あなたは以下の機能を使ってDiscordから情報を取得できます。
情報が必要な場合は、以下のXMLタグ形式のコマンドを**単独で**出力してください。
コマンドの前後に余計な文章を入れないでください。

利用可能なコマンド:
<cmd>get_channels</cmd>
- サーバー内のテキストチャンネル一覧を取得します。

<cmd>get_server_info</cmd>
- サーバーの基本情報（名前、メンバー数など）を取得します。

<cmd>get_recent_messages</cmd>
- 現在のチャンネルの直近10件のメッセージを取得します。

処理フロー:
1. ユーザーの質問に対し、情報が必要か判断する。
2. 必要ならコマンドを出力する。
3. システムから提供された情報をもとに、最終的な回答を生成する。
"""

# Discord intentsの設定
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# ボットの初期化
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# Ollamaクライアントの初期化
ollama_client = ollama.Client(host=OLLAMA_URL)


class OllamaChat:
    """Ollamaとの会話を管理するクラス"""
    
    def __init__(self, model: str):
        self.model = model
        self.reset_history()
    
    def reset_history(self):
        """履歴をリセットし、システムプロンプトを設定"""
        self.conversation_history = [{
            'role': 'system',
            'content': SYSTEM_PROMPT
        }]

    async def get_discord_info(self, command: str, message: discord.Message) -> str:
        """Discordから情報を取得する"""
        try:
            guild = message.guild
            if not guild:
                return "エラー: DMではこの機能は使えません。"

            if command == "get_channels":
                channels = [f"{ch.name} (ID: {ch.id})" for ch in guild.text_channels]
                return "チャンネル一覧:\n" + "\n".join(channels[:20]) # 多すぎると溢れるので制限
            
            elif command == "get_server_info":
                info = [
                    f"サーバー名: {guild.name}",
                    f"サーバーID: {guild.id}",
                    f"メンバー数: {guild.member_count}",
                    f"オーナー: {guild.owner.name if guild.owner else '不明'}",
                    f"作成日: {guild.created_at.strftime('%Y-%m-%d')}"
                ]
                return "\n".join(info)
            
            elif command == "get_recent_messages":
                history = []
                async for msg in message.channel.history(limit=10, before=message):
                    if not msg.content: continue
                    history.append(f"{msg.author.display_name}: {msg.content}")
                
                if not history:
                    return "直近のメッセージはありません。"
                
                return "直近のメッセージ (新しい順):\n" + "\n".join(history)
            
            else:
                return f"エラー: 未知のコマンド {command}"

        except Exception as e:
            logger.error(f"情報取得エラー: {e}")
            return f"情報取得中にエラーが発生しました: {str(e)}"

    async def generate_response(self, message: discord.Message, depth: int = 0) -> str:
        """
        ユーザーメッセージに対してOllamaで応答を生成
        
        Args:
            message: Discordのメッセージオブジェクト
            depth: 再帰呼び出しの深さ（無限ループ防止用）
            
        Returns:
            Ollamaからの応答テキスト
        """
        if depth > 3: # 最大3回までツール呼び出しを許可
            return "申し訳ありません、処理が複雑すぎて答えられませんでした。"

        user_message = message.content
        username = message.author.display_name

        # 最初の呼び出し時のみユーザーメッセージを追加（再帰時は履歴が更新されている前提）
        if depth == 0:
            # 最新の履歴がこのユーザーメッセージでない場合のみ追加
            last_msg = self.conversation_history[-1]
            current_content = f'{username}: {user_message}'
            # 注意: systemメッセージだけのときは必ず追加、あるいは最後のメッセージがuserでない場合に追加
            # 単純化のため、depth 0なら必ず追加するが、二重追加を防ぐロジックが必要なら入れる
            # ここでは呼び出し元が制御していないので、depth=0なら追加でOK
            self.conversation_history.append({
                'role': 'user',
                'content': current_content
            })

        # 会話履歴が長すぎる場合は古いものを削除（システムプロンプトは保持）
        # systemプロンプト(index 0) + 最新20件
        if len(self.conversation_history) > 21:
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-20:]
        
        try:
            # Ollamaにリクエストを送信
            logger.info(f'Ollamaにリクエスト送信 (depth={depth})')
            
            # 非同期でOllama APIを呼び出す
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: ollama_client.chat(
                    model=self.model,
                    messages=self.conversation_history
                )
            )
            
            assistant_message = response['message']['content']
            logger.info(f'Ollama応答: {assistant_message[:50]}...')

            # コマンドのチェック (<cmd>...</cmd>)
            cmd_match = re.search(r'<cmd>(.*?)</cmd>', assistant_message)
            if cmd_match:
                command = cmd_match.group(1)
                logger.info(f"コマンド検出: {command}")
                
                # とりあえずアシスタントの応答（コマンド）を履歴に追加
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': assistant_message
                })

                # コマンド実行
                tool_result = await self.get_discord_info(command, message)
                
                # 結果をシステムメッセージとして追加
                self.conversation_history.append({
                    'role': 'system',
                    'content': f"コマンド実行結果:\n{tool_result}"
                })

                # 再帰的に呼び出して回答を生成させる
                return await self.generate_response(message, depth=depth + 1)
            
            else:
                # 通常の応答
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': assistant_message
                })
                return assistant_message
            
        except Exception as e:
            logger.error(f'Ollama API呼び出しエラー: {e}')
            return f'エラーが発生しました: {str(e)}'


# グローバルなOllamaチャットインスタンス
ollama_chat = OllamaChat(OLLAMA_MODEL)


@bot.event
async def on_ready():
    """ボットが起動したときに呼ばれる"""
    logger.info(f'{bot.user}としてログインしました')
    logger.info(f'監視チャンネルID: {TARGET_CHANNEL_ID}')
    logger.info(f'Ollama URL: {OLLAMA_URL}')
    logger.info(f'Ollama Model: {OLLAMA_MODEL}')
    
    # ボットのステータスを設定
    await bot.change_presence(
        activity=discord.Game(name=f'Ollama ({OLLAMA_MODEL})で会話中')
    )


@bot.event
async def on_message(message: discord.Message):
    """メッセージが送信されたときに呼ばれる"""
    # ボット自身のメッセージは無視
    if message.author == bot.user:
        return
    
    # 指定されたチャンネルでのみ反応
    if message.channel.id != TARGET_CHANNEL_ID:
        return
    
    # コマンドの場合はコマンドハンドラーに渡す
    if message.content.startswith(BOT_PREFIX):
        await bot.process_commands(message)
        return
    
    # メッセージが空の場合は無視
    if not message.content.strip():
        return
    
    # タイピングインジケーターを表示
    async with message.channel.typing():
        try:
            # Ollamaで応答を生成
            response = await ollama_chat.generate_response(message)
            
            # 応答を送信（Discordのメッセージ長制限を考慮）
            if len(response) > 2000:
                # 長い場合は分割して送信
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                for chunk in chunks:
                    await message.channel.send(chunk)
            else:
                await message.channel.send(response)
                
        except Exception as e:
            logger.error(f'メッセージ処理エラー: {e}')
            await message.channel.send(f'エラーが発生しました: {str(e)}')


@bot.command(name='ping')
async def ping(ctx):
    """ボットの応答性をテストするコマンド"""
    await ctx.send('pong!')


@bot.command(name='reset')
async def reset(ctx):
    """会話履歴をリセットするコマンド"""
    ollama_chat.reset_history()
    await ctx.send('会話履歴をリセットしました！新しい会話を始めましょう！')


@bot.command(name='status')
async def status(ctx):
    """ボットの状態を表示するコマンド"""
    status_message = f"""
**ボットステータス (AI짱)**
- Ollama URL: {OLLAMA_URL}
- モデル: {OLLAMA_MODEL}
- 会話履歴数: {len(ollama_chat.conversation_history)}
- 監視チャンネル: <#{TARGET_CHANNEL_ID}>
"""
    await ctx.send(status_message)


def main():
    """メイン関数"""
    if not DISCORD_TOKEN:
        logger.error('DISCORD_TOKENが設定されていません。.envファイルを確認してください。')
        return
    
    if TARGET_CHANNEL_ID == 0:
        logger.error('TARGET_CHANNEL_IDが設定されていません。.envファイルを確認してください。')
        return
    
    try:
        # Ollama接続をテスト
        logger.info('Ollama接続をテスト中...')
        ollama_client.list()
        logger.info('Ollama接続成功')
    except Exception as e:
        logger.error(f'Ollama接続エラー: {e}')
        logger.error('Ollamaが起動しているか確認してください。')
        return
    
    # ボットを起動
    logger.info('Discordボットを起動中...')
    bot.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()
