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
SYSTEM_PROMPT = os.getenv('SYSTEM_PROMPT', '''あなたは「AI짱」という名前のDiscord botです。
あなたは親しみやすく、フレンドリーで、ユーザーとの会話を楽しむキャラクターです。
日本語で自然な会話をしてください。
必要に応じてDiscordの情報（ユーザー情報、チャンネル情報、メッセージ履歴など）を活用できます。
あなたの名前は「AI짱」です。自己紹介するときは必ずこの名前を使ってください。''')

# Discord intentsの設定
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# ボットの初期化
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# Ollamaクライアントの初期化
ollama_client = ollama.Client(host=OLLAMA_URL)


class DiscordInfoHelper:
    """Discord情報を取得するヘルパークラス"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
    
    async def get_channel_info(self, channel_id: int) -> dict:
        """チャンネル情報を取得"""
        try:
            channel = self.bot.get_channel(channel_id)
            if channel:
                return {
                    'name': channel.name,
                    'id': channel.id,
                    'type': str(channel.type),
                    'guild': channel.guild.name if hasattr(channel, 'guild') else None
                }
        except Exception as e:
            logger.error(f'チャンネル情報取得エラー: {e}')
        return {}
    
    async def get_user_info(self, user_id: int) -> dict:
        """ユーザー情報を取得"""
        try:
            user = await self.bot.fetch_user(user_id)
            if user:
                return {
                    'name': user.name,
                    'display_name': user.display_name,
                    'id': user.id,
                    'bot': user.bot,
                    'created_at': user.created_at.isoformat()
                }
        except Exception as e:
            logger.error(f'ユーザー情報取得エラー: {e}')
        return {}
    
    async def get_recent_messages(self, channel_id: int, limit: int = 10) -> list:
        """最近のメッセージを取得"""
        try:
            channel = self.bot.get_channel(channel_id)
            if channel:
                messages = []
                async for message in channel.history(limit=limit):
                    messages.append({
                        'author': message.author.display_name,
                        'content': message.content,
                        'timestamp': message.created_at.isoformat()
                    })
                return messages
        except Exception as e:
            logger.error(f'メッセージ履歴取得エラー: {e}')
        return []
    
    async def get_guild_info(self, guild_id: int) -> dict:
        """サーバー情報を取得"""
        try:
            guild = self.bot.get_guild(guild_id)
            if guild:
                return {
                    'name': guild.name,
                    'id': guild.id,
                    'member_count': guild.member_count,
                    'created_at': guild.created_at.isoformat()
                }
        except Exception as e:
            logger.error(f'サーバー情報取得エラー: {e}')
        return {}


class OllamaChat:
    """Ollamaとの会話を管理するクラス"""
    
    def __init__(self, model: str, system_prompt: str, discord_helper=None):
        self.model = model
        self.system_prompt = system_prompt
        self.conversation_history = []
        self.discord_helper = discord_helper
        # システムメッセージを初期化
        self._init_system_message()
    
    def _init_system_message(self):
        """システムメッセージを初期化"""
        self.conversation_history = [{
            'role': 'system',
            'content': self.system_prompt
        }]
    
    async def generate_response(self, user_message: str, username: str, message_context=None) -> str:
        """
        ユーザーメッセージに対してOllamaで応答を生成
        
        Args:
            user_message: ユーザーのメッセージ
            username: ユーザー名
            message_context: Discordメッセージのコンテキスト（オプション）
            
        Returns:
            Ollamaからの応答テキスト
        """
        try:
            # Discord情報を活用した追加コンテキストの生成
            additional_context = ""
            if message_context and self.discord_helper:
                # チャンネル情報を取得
                if hasattr(message_context.channel, 'id'):
                    channel_info = await self.discord_helper.get_channel_info(message_context.channel.id)
                    if channel_info:
                        additional_context += f"\n[チャンネル: {channel_info.get('name', 'Unknown')}]"
                
                # ユーザーがメンションやリクエストをした場合の情報取得
                if message_context.mentions:
                    for mention in message_context.mentions:
                        user_info = await self.discord_helper.get_user_info(mention.id)
                        if user_info:
                            additional_context += f"\n[メンション: {user_info.get('display_name', 'Unknown')}]"
            
            # 会話履歴に追加
            user_content = f'{username}: {user_message}'
            if additional_context:
                user_content += additional_context
            
            self.conversation_history.append({
                'role': 'user',
                'content': user_content
            })
            
            # 会話履歴が長すぎる場合は古いものを削除（システムメッセージを除く最新20件を保持）
            if len(self.conversation_history) > 21:  # システムメッセージ(1) + ユーザー/アシスタントメッセージ(20)
                # システムメッセージを保持
                system_msg = self.conversation_history[0]
                self.conversation_history = [system_msg] + self.conversation_history[-20:]
            
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


# グローバルなインスタンス（初期化はon_readyで行う）
ollama_chat = None
discord_helper = None


@bot.event
async def on_ready():
    """ボットが起動したときに呼ばれる"""
    global ollama_chat, discord_helper
    
    logger.info(f'{bot.user}としてログインしました')
    logger.info(f'監視チャンネルID: {TARGET_CHANNEL_ID}')
    logger.info(f'Ollama URL: {OLLAMA_URL}')
    logger.info(f'Ollama Model: {OLLAMA_MODEL}')
    
    # Discord情報ヘルパーを初期化
    discord_helper = DiscordInfoHelper(bot)
    
    # Ollamaチャットインスタンスを初期化
    ollama_chat = OllamaChat(OLLAMA_MODEL, SYSTEM_PROMPT, discord_helper)
    logger.info('AI짱として初期化されました')
    
    # ボットのステータスを設定
    await bot.change_presence(
        activity=discord.Game(name='AI짱 | Ollamaで会話中')
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
            # Ollamaで応答を生成（メッセージコンテキストを渡す）
            username = message.author.display_name
            response = await ollama_chat.generate_response(
                message.content,
                username,
                message_context=message
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
    ollama_chat._init_system_message()
    await ctx.send('会話履歴をリセットしました。AI짱として再初期化されました。')


@bot.command(name='status')
async def status(ctx):
    """ボットの状態を表示するコマンド"""
    status_message = f"""
**AI짱 ステータス**
- 名前: AI짱 (Discord Bot)
- Ollama URL: {OLLAMA_URL}
- モデル: {OLLAMA_MODEL}
- 会話履歴数: {len(ollama_chat.conversation_history)}
- 監視チャンネル: <#{TARGET_CHANNEL_ID}>
"""
    await ctx.send(status_message)


@bot.command(name='channelinfo')
async def channelinfo(ctx, channel_id: int = None):
    """チャンネル情報を表示するコマンド"""
    if channel_id is None:
        channel_id = ctx.channel.id
    
    channel_info = await discord_helper.get_channel_info(channel_id)
    if channel_info:
        info_message = f"""
**チャンネル情報**
- 名前: {channel_info.get('name', 'Unknown')}
- ID: {channel_info.get('id', 'Unknown')}
- タイプ: {channel_info.get('type', 'Unknown')}
- サーバー: {channel_info.get('guild', 'Unknown')}
"""
        await ctx.send(info_message)
    else:
        await ctx.send('チャンネル情報を取得できませんでした。')


@bot.command(name='userinfo')
async def userinfo(ctx, user_id: int = None):
    """ユーザー情報を表示するコマンド"""
    if user_id is None:
        user_id = ctx.author.id
    
    user_info = await discord_helper.get_user_info(user_id)
    if user_info:
        info_message = f"""
**ユーザー情報**
- 名前: {user_info.get('name', 'Unknown')}
- 表示名: {user_info.get('display_name', 'Unknown')}
- ID: {user_info.get('id', 'Unknown')}
- Bot: {user_info.get('bot', False)}
- アカウント作成日: {user_info.get('created_at', 'Unknown')}
"""
        await ctx.send(info_message)
    else:
        await ctx.send('ユーザー情報を取得できませんでした。')


@bot.command(name='history')
async def history(ctx, limit: int = 5):
    """最近のメッセージ履歴を表示するコマンド"""
    if limit > 20:
        limit = 20
    
    messages = await discord_helper.get_recent_messages(ctx.channel.id, limit)
    if messages:
        history_message = f"**最近の{len(messages)}件のメッセージ:**\n"
        for msg in reversed(messages):
            timestamp = msg['timestamp'].split('T')[1][:8]
            history_message += f"[{timestamp}] {msg['author']}: {msg['content'][:50]}...\n"
        await ctx.send(history_message)
    else:
        await ctx.send('メッセージ履歴を取得できませんでした。')


@bot.command(name='whoami')
async def whoami(ctx):
    """AI짱の自己紹介コマンド"""
    await ctx.send('こんにちは！私はAI짱です！Discordで皆さんとおしゃべりするのが好きなボットです。Ollamaを使って会話しています。よろしくお願いします！ 😊')


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
