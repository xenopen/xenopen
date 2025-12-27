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
    
    async def generate_response(self, user_message: str, username: str) -> str:
        """
        ユーザーメッセージに対してOllamaで応答を生成
        
        Args:
            user_message: ユーザーのメッセージ
            username: ユーザー名
            
        Returns:
            Ollamaからの応答テキスト
        """
        try:
            # 会話履歴に追加
            self.conversation_history.append({
                'role': 'user',
                'content': f'{username}: {user_message}'
            })
            
            # 会話履歴が長すぎる場合は古いものを削除（最新20件を保持）
            if len(self.conversation_history) > 20:
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
            username = message.author.display_name
            response = await ollama_chat.generate_response(
                message.content,
                username
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
    ollama_chat.conversation_history = []
    await ctx.send('会話履歴をリセットしました。')


@bot.command(name='status')
async def status(ctx):
    """ボットの状態を表示するコマンド"""
    status_message = f"""
**ボットステータス**
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
