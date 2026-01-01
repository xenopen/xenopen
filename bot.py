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
        self.conversation_history = []
        # システムプロンプトでAI짱としての自己認識を設定
        self.system_prompt = """あなたはAI짱（AIちゃん）という名前のDiscordボットです。

重要な自己認識:
- あなたの名前は「AI짱」または「AIちゃん」です
- あなたはDiscordサーバーで動作するボットです
- ユーザーに自己紹介する際は「私はAI짱です」または「AI짱です」と言ってください

あなたの役割:
- Discordサーバーでユーザーと会話し、親しみやすくフレンドリーに応答します
- 必要に応じてDiscordの情報を取得してユーザーをサポートします
- ユーザーの質問に丁寧に答えます

利用可能なDiscord情報取得機能:
- チャンネル情報（!channelinfoコマンド）
- サーバー情報（!serverinfoコマンド）
- メンバーリスト（!membersコマンド）
- メッセージ履歴（!historyコマンド）

会話の際は、提供されたDiscordコンテキスト情報を活用して、より適切な回答を心がけてください。"""
        
        # 初期システムメッセージを追加
        self.conversation_history.append({
            'role': 'system',
            'content': self.system_prompt
        })
    
    async def generate_response(self, user_message: str, username: str, discord_context: dict = None) -> str:
        """
        ユーザーメッセージに対してOllamaで応答を生成
        
        Args:
            user_message: ユーザーのメッセージ
            username: ユーザー名
            discord_context: Discordのコンテキスト情報（チャンネル、メンバーなど）
            
        Returns:
            Ollamaからの応答テキスト
        """
        try:
            # Discordコンテキスト情報をメッセージに追加
            context_info = ""
            if discord_context:
                context_parts = []
                if 'channel_name' in discord_context:
                    context_parts.append(f"現在のチャンネル: {discord_context['channel_name']}")
                if 'server_name' in discord_context:
                    context_parts.append(f"サーバー: {discord_context['server_name']}")
                if 'member_count' in discord_context:
                    context_parts.append(f"サーバーメンバー数: {discord_context['member_count']}")
                if 'recent_messages' in discord_context and discord_context['recent_messages']:
                    context_parts.append(f"最近のメッセージ: {discord_context['recent_messages']}")
                if context_parts:
                    context_info = f"\n[Discord情報: {', '.join(context_parts)}]"
            
            # 会話履歴に追加
            self.conversation_history.append({
                'role': 'user',
                'content': f'{username}: {user_message}{context_info}'
            })
            
            # 会話履歴が長すぎる場合は古いものを削除（システムメッセージは保持、最新20件を保持）
            if len(self.conversation_history) > 21:  # システムメッセージ + 20件の会話
                # システムメッセージを保持
                system_msg = None
                if self.conversation_history[0]['role'] == 'system':
                    system_msg = self.conversation_history[0]
                    self.conversation_history = self.conversation_history[-20:]
                    if system_msg:
                        self.conversation_history.insert(0, system_msg)
                else:
                    self.conversation_history = self.conversation_history[-20:]
            
            # Ollamaにリクエストを送信
            logger.info(f'Ollamaにリクエスト送信: {user_message[:50]}...')
            
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
            
            # 会話履歴に追加
            self.conversation_history.append({
                'role': 'assistant',
                'content': assistant_message
            })
            
            logger.info(f'Ollamaからの応答: {assistant_message[:50]}...')
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


async def get_discord_context(message: discord.Message) -> dict:
    """
    Discordのコンテキスト情報を取得
    
    Args:
        message: Discordメッセージオブジェクト
        
    Returns:
        Discordコンテキスト情報の辞書
    """
    context = {}
    
    try:
        # チャンネル情報
        if message.channel:
            context['channel_name'] = message.channel.name
            context['channel_id'] = message.channel.id
        
        # サーバー情報
        if message.guild:
            context['server_name'] = message.guild.name
            context['server_id'] = message.guild.id
            context['member_count'] = message.guild.member_count
        
        # 最近のメッセージ（最新5件）
        try:
            recent_messages = []
            async for msg in message.channel.history(limit=5):
                if msg.author != bot.user:
                    recent_messages.append(f"{msg.author.display_name}: {msg.content[:50]}")
            if recent_messages:
                context['recent_messages'] = " | ".join(recent_messages)
        except Exception as e:
            logger.warning(f'最近のメッセージ取得エラー: {e}')
        
    except Exception as e:
        logger.warning(f'Discordコンテキスト取得エラー: {e}')
    
    return context


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
            # Discordコンテキスト情報を取得
            discord_context = await get_discord_context(message)
            
            # Ollamaで応答を生成
            username = message.author.display_name
            response = await ollama_chat.generate_response(
                message.content,
                username,
                discord_context
            )
            
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
    ollama_chat.conversation_history = [
        {
            'role': 'system',
            'content': ollama_chat.system_prompt
        }
    ]
    await ctx.send('会話履歴をリセットしました。')


@bot.command(name='status')
async def status(ctx):
    """ボットの状態を表示するコマンド"""
    status_message = f"""
**ボットステータス**
- 名前: AI짱 (AIちゃん)
- Ollama URL: {OLLAMA_URL}
- モデル: {OLLAMA_MODEL}
- 会話履歴数: {len(ollama_chat.conversation_history)}
- 監視チャンネル: <#{TARGET_CHANNEL_ID}>
"""
    await ctx.send(status_message)


@bot.command(name='channelinfo')
async def channelinfo(ctx):
    """現在のチャンネル情報を表示するコマンド"""
    try:
        channel = ctx.channel
        info = f"""
**チャンネル情報**
- 名前: {channel.name}
- ID: {channel.id}
- タイプ: {channel.type}
"""
        if hasattr(channel, 'topic') and channel.topic:
            info += f"- トピック: {channel.topic}\n"
        if hasattr(channel, 'category') and channel.category:
            info += f"- カテゴリ: {channel.category.name}\n"
        
        await ctx.send(info)
    except Exception as e:
        logger.error(f'チャンネル情報取得エラー: {e}')
        await ctx.send(f'エラーが発生しました: {str(e)}')


@bot.command(name='serverinfo')
async def serverinfo(ctx):
    """サーバー情報を表示するコマンド"""
    try:
        if not ctx.guild:
            await ctx.send('このコマンドはサーバー内でのみ使用できます。')
            return
        
        guild = ctx.guild
        info = f"""
**サーバー情報**
- 名前: {guild.name}
- ID: {guild.id}
- メンバー数: {guild.member_count}
- オーナー: {guild.owner.mention if guild.owner else "不明"}
- 作成日: {guild.created_at.strftime('%Y年%m月%d日')}
- チャンネル数: {len(guild.channels)}
- ロール数: {len(guild.roles)}
"""
        if guild.description:
            info += f"- 説明: {guild.description}\n"
        
        await ctx.send(info)
    except Exception as e:
        logger.error(f'サーバー情報取得エラー: {e}')
        await ctx.send(f'エラーが発生しました: {str(e)}')


@bot.command(name='members')
async def members(ctx, limit: int = 10):
    """サーバーのメンバーリストを表示するコマンド"""
    try:
        if not ctx.guild:
            await ctx.send('このコマンドはサーバー内でのみ使用できます。')
            return
        
        members_list = []
        count = 0
        for member in ctx.guild.members:
            if count >= limit:
                break
            if not member.bot:
                members_list.append(f"- {member.display_name} ({member.name})")
                count += 1
        
        if members_list:
            info = f"**サーバーメンバー（最大{limit}人）**\n" + "\n".join(members_list)
            if len(info) > 2000:
                info = info[:1900] + "\n...（省略）"
            await ctx.send(info)
        else:
            await ctx.send('メンバーが見つかりませんでした。')
    except Exception as e:
        logger.error(f'メンバーリスト取得エラー: {e}')
        await ctx.send(f'エラーが発生しました: {str(e)}')


@bot.command(name='history')
async def history(ctx, limit: int = 5):
    """最近のメッセージ履歴を表示するコマンド"""
    try:
        messages = []
        count = 0
        async for message in ctx.channel.history(limit=min(limit, 20)):
            if count >= limit:
                break
            if message.author != bot.user:
                timestamp = message.created_at.strftime('%H:%M')
                messages.append(f"[{timestamp}] {message.author.display_name}: {message.content[:100]}")
                count += 1
        
        if messages:
            info = f"**最近のメッセージ（{count}件）**\n" + "\n".join(reversed(messages))
            if len(info) > 2000:
                info = info[:1900] + "\n...（省略）"
            await ctx.send(info)
        else:
            await ctx.send('メッセージが見つかりませんでした。')
    except Exception as e:
        logger.error(f'メッセージ履歴取得エラー: {e}')
        await ctx.send(f'エラーが発生しました: {str(e)}')


@bot.command(name='help_ai')
async def help_ai(ctx):
    """AI짱が使用できるコマンドのヘルプを表示"""
    help_text = """
**AI짱 コマンド一覧**

**基本コマンド:**
- `!ping` - ボットの応答性をテスト
- `!reset` - 会話履歴をリセット
- `!status` - ボットの状態を表示

**Discord情報取得コマンド:**
- `!channelinfo` - 現在のチャンネル情報を表示
- `!serverinfo` - サーバー情報を表示
- `!members [数]` - サーバーメンバーリストを表示（デフォルト: 10人）
- `!history [数]` - 最近のメッセージ履歴を表示（デフォルト: 5件）
- `!help_ai` - このヘルプを表示

**使い方:**
通常のメッセージを送信すると、AI짱が自動的に応答します。
必要に応じて上記のコマンドを使用してDiscordの情報を取得できます。
"""
    await ctx.send(help_text)


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
