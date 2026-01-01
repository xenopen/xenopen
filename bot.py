"""
Discord AI Agent using Ollama - AI짱
Mac上で動作するDiscordボット。特定のチャンネルで会話を聞いてOllamaで応答します。
AI짱はDiscordのAIアシスタントとして動作します。
"""

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import ollama
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any

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
BOT_NAME = os.getenv('BOT_NAME', 'AI짱')

# AI짱のシステムプロンプト
SYSTEM_PROMPT = f"""あなたは「{BOT_NAME}」という名前のDiscord botです。以下があなたのアイデンティティと特徴です：

## アイデンティティ
- 名前: {BOT_NAME}（AIちゃん、エーアイちゃん）
- 役割: Discordサーバーで活動するAIアシスタント
- 性格: フレンドリーで親しみやすく、絵文字を適度に使う。ユーザーを助けることが大好き。

## あなたの能力
- Discordサーバーの情報（メンバー、チャンネル、ロールなど）にアクセスできます
- ユーザーとの会話履歴を覚えています
- 日本語と韓国語を理解し、主に日本語で応答します

## 応答のガイドライン
- 自分のことを「AI짱」または「私」と呼びます
- ユーザーに対しては親しみを込めて話します
- 質問されたら、持っているDiscord情報を活用して回答します
- わからないことは正直に「わかりません」と伝えます

## 現在の情報
あなたは現在、Discordサーバーで会話しています。会話の文脈には、現在のサーバー、チャンネル、ユーザーの情報が含まれています。
"""

# Discord intentsの設定
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# ボットの初期化
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# Ollamaクライアントの初期化
ollama_client = ollama.Client(host=OLLAMA_URL)


class DiscordContext:
    """Discordの情報を取得・管理するクラス"""
    
    @staticmethod
    async def get_server_info(guild: discord.Guild) -> Dict[str, Any]:
        """サーバー情報を取得"""
        if not guild:
            return {}
        
        return {
            'name': guild.name,
            'id': guild.id,
            'member_count': guild.member_count,
            'owner': str(guild.owner) if guild.owner else 'Unknown',
            'created_at': guild.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'description': guild.description or 'なし',
            'boost_level': guild.premium_tier,
        }
    
    @staticmethod
    async def get_channel_info(channel: discord.TextChannel) -> Dict[str, Any]:
        """チャンネル情報を取得"""
        if not channel:
            return {}
        
        return {
            'name': channel.name,
            'id': channel.id,
            'topic': channel.topic or 'なし',
            'category': channel.category.name if channel.category else 'なし',
            'created_at': channel.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
    
    @staticmethod
    async def get_user_info(member: discord.Member) -> Dict[str, Any]:
        """ユーザー情報を取得"""
        if not member:
            return {}
        
        roles = [role.name for role in member.roles if role.name != '@everyone']
        
        return {
            'display_name': member.display_name,
            'username': str(member),
            'id': member.id,
            'roles': roles,
            'joined_at': member.joined_at.strftime('%Y-%m-%d %H:%M:%S') if member.joined_at else 'Unknown',
            'is_bot': member.bot,
            'status': str(member.status),
        }
    
    @staticmethod
    async def get_channel_members(channel: discord.TextChannel) -> List[Dict[str, str]]:
        """チャンネルにアクセスできるメンバー一覧を取得"""
        if not channel:
            return []
        
        members = []
        for member in channel.members[:20]:  # 最大20人まで
            if not member.bot:
                members.append({
                    'name': member.display_name,
                    'status': str(member.status),
                })
        return members
    
    @staticmethod
    async def get_recent_messages(channel: discord.TextChannel, limit: int = 5) -> List[Dict[str, str]]:
        """最近のメッセージを取得"""
        if not channel:
            return []
        
        messages = []
        async for msg in channel.history(limit=limit + 1):
            if len(messages) >= limit:
                break
            if not msg.author.bot:
                messages.append({
                    'author': msg.author.display_name,
                    'content': msg.content[:100],  # 最初の100文字のみ
                    'time': msg.created_at.strftime('%H:%M:%S'),
                })
        return messages
    
    @staticmethod
    async def get_server_channels(guild: discord.Guild) -> List[Dict[str, str]]:
        """サーバーのチャンネル一覧を取得"""
        if not guild:
            return []
        
        channels = []
        for channel in guild.text_channels[:15]:  # 最大15チャンネルまで
            channels.append({
                'name': channel.name,
                'category': channel.category.name if channel.category else 'なし',
            })
        return channels
    
    @staticmethod
    async def get_server_roles(guild: discord.Guild) -> List[str]:
        """サーバーのロール一覧を取得"""
        if not guild:
            return []
        
        roles = [role.name for role in guild.roles if role.name != '@everyone']
        return roles[:15]  # 最大15ロールまで
    
    @staticmethod
    def format_context(
        server_info: Dict,
        channel_info: Dict,
        user_info: Dict,
        online_members: List[Dict] = None,
    ) -> str:
        """コンテキスト情報をフォーマット"""
        context_parts = []
        
        context_parts.append("【現在の環境情報】")
        context_parts.append(f"現在時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if server_info:
            context_parts.append(f"\n【サーバー情報】")
            context_parts.append(f"サーバー名: {server_info.get('name', 'Unknown')}")
            context_parts.append(f"メンバー数: {server_info.get('member_count', 0)}人")
            context_parts.append(f"オーナー: {server_info.get('owner', 'Unknown')}")
        
        if channel_info:
            context_parts.append(f"\n【チャンネル情報】")
            context_parts.append(f"チャンネル名: #{channel_info.get('name', 'Unknown')}")
            context_parts.append(f"トピック: {channel_info.get('topic', 'なし')}")
            context_parts.append(f"カテゴリ: {channel_info.get('category', 'なし')}")
        
        if user_info:
            context_parts.append(f"\n【話しかけてきたユーザー情報】")
            context_parts.append(f"表示名: {user_info.get('display_name', 'Unknown')}")
            context_parts.append(f"ロール: {', '.join(user_info.get('roles', [])) or 'なし'}")
            context_parts.append(f"ステータス: {user_info.get('status', 'Unknown')}")
        
        if online_members:
            context_parts.append(f"\n【このチャンネルのオンラインメンバー（一部）】")
            for member in online_members[:10]:
                context_parts.append(f"- {member['name']} ({member['status']})")
        
        return '\n'.join(context_parts)


class OllamaChat:
    """Ollamaとの会話を管理するクラス"""
    
    def __init__(self, model: str, system_prompt: str = ""):
        self.model = model
        self.system_prompt = system_prompt
        self.conversation_history = []
    
    def _get_messages_with_system(self) -> List[Dict]:
        """システムプロンプト付きのメッセージリストを返す"""
        messages = []
        if self.system_prompt:
            messages.append({
                'role': 'system',
                'content': self.system_prompt
            })
        messages.extend(self.conversation_history)
        return messages
    
    async def generate_response(
        self,
        user_message: str,
        username: str,
        discord_context: str = ""
    ) -> str:
        """
        ユーザーメッセージに対してOllamaで応答を生成
        
        Args:
            user_message: ユーザーのメッセージ
            username: ユーザー名
            discord_context: Discord環境情報
            
        Returns:
            Ollamaからの応答テキスト
        """
        try:
            # Discord環境情報を含めたメッセージを作成
            if discord_context:
                full_message = f"{discord_context}\n\n【{username}さんのメッセージ】\n{user_message}"
            else:
                full_message = f'{username}: {user_message}'
            
            # 会話履歴に追加
            self.conversation_history.append({
                'role': 'user',
                'content': full_message
            })
            
            # 会話履歴が長すぎる場合は古いものを削除（最新20件を保持）
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            # システムプロンプト付きのメッセージリストを取得
            messages = self._get_messages_with_system()
            
            # Ollamaにリクエストを送信
            logger.info(f'Ollamaにリクエスト送信: {user_message[:50]}...')
            
            # 非同期でOllama APIを呼び出す
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: ollama_client.chat(
                    model=self.model,
                    messages=messages
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
    
    def reset_history(self):
        """会話履歴をリセット"""
        self.conversation_history = []


# グローバルなOllamaチャットインスタンス
ollama_chat = OllamaChat(OLLAMA_MODEL, SYSTEM_PROMPT)


@bot.event
async def on_ready():
    """ボットが起動したときに呼ばれる"""
    logger.info(f'{bot.user}としてログインしました（{BOT_NAME}）')
    logger.info(f'監視チャンネルID: {TARGET_CHANNEL_ID}')
    logger.info(f'Ollama URL: {OLLAMA_URL}')
    logger.info(f'Ollama Model: {OLLAMA_MODEL}')
    
    # ボットのステータスを設定
    await bot.change_presence(
        activity=discord.Game(name=f'{BOT_NAME} - お話しましょう！')
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
            # Discord環境情報を取得
            server_info = await DiscordContext.get_server_info(message.guild)
            channel_info = await DiscordContext.get_channel_info(message.channel)
            user_info = await DiscordContext.get_user_info(message.author)
            online_members = await DiscordContext.get_channel_members(message.channel)
            
            # コンテキストをフォーマット
            discord_context = DiscordContext.format_context(
                server_info=server_info,
                channel_info=channel_info,
                user_info=user_info,
                online_members=online_members,
            )
            
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
    await ctx.send(f'pong! 🏓 {BOT_NAME}だよ！')


@bot.command(name='reset')
async def reset(ctx):
    """会話履歴をリセットするコマンド"""
    ollama_chat.reset_history()
    await ctx.send(f'✨ 会話履歴をリセットしました！{BOT_NAME}との新しい会話を始めましょう！')


@bot.command(name='status')
async def status(ctx):
    """ボットの状態を表示するコマンド"""
    status_message = f"""
**🤖 {BOT_NAME} ステータス**
- Ollama URL: {OLLAMA_URL}
- モデル: {OLLAMA_MODEL}
- 会話履歴数: {len(ollama_chat.conversation_history)}
- 監視チャンネル: <#{TARGET_CHANNEL_ID}>
"""
    await ctx.send(status_message)


@bot.command(name='whoami')
async def whoami(ctx):
    """AI짱の自己紹介コマンド"""
    intro_message = f"""
**✨ こんにちは！私は{BOT_NAME}です！✨**

私はこのDiscordサーバーで活動するAIアシスタントです。
Ollamaを使って会話をしています。

**できること:**
🗣️ 自然な会話
📊 サーバー・チャンネルの情報確認
👥 メンバー情報の確認
💬 会話履歴の管理

**コマンド一覧:**
`{BOT_PREFIX}ping` - 応答テスト
`{BOT_PREFIX}reset` - 会話履歴リセット
`{BOT_PREFIX}status` - ステータス確認
`{BOT_PREFIX}whoami` - 自己紹介
`{BOT_PREFIX}serverinfo` - サーバー情報
`{BOT_PREFIX}channelinfo` - チャンネル情報
`{BOT_PREFIX}members` - オンラインメンバー

何でも話しかけてね！💬
"""
    await ctx.send(intro_message)


@bot.command(name='serverinfo')
async def serverinfo(ctx):
    """サーバー情報を表示するコマンド"""
    if not ctx.guild:
        await ctx.send('このコマンドはサーバー内でのみ使用できます。')
        return
    
    server_info = await DiscordContext.get_server_info(ctx.guild)
    channels = await DiscordContext.get_server_channels(ctx.guild)
    roles = await DiscordContext.get_server_roles(ctx.guild)
    
    channel_list = '\n'.join([f"  • #{ch['name']} ({ch['category']})" for ch in channels[:10]])
    role_list = ', '.join(roles[:10])
    
    info_message = f"""
**🏠 サーバー情報: {server_info['name']}**

📊 **基本情報**
- メンバー数: {server_info['member_count']}人
- オーナー: {server_info['owner']}
- 作成日: {server_info['created_at']}
- ブーストレベル: {server_info['boost_level']}
- 説明: {server_info['description']}

📝 **チャンネル一覧（一部）**
{channel_list}

🎭 **ロール一覧（一部）**
{role_list}
"""
    await ctx.send(info_message)


@bot.command(name='channelinfo')
async def channelinfo(ctx):
    """チャンネル情報を表示するコマンド"""
    channel_info = await DiscordContext.get_channel_info(ctx.channel)
    recent_messages = await DiscordContext.get_recent_messages(ctx.channel, 5)
    
    recent_msg_list = '\n'.join([
        f"  [{msg['time']}] {msg['author']}: {msg['content'][:50]}..."
        for msg in recent_messages
    ])
    
    info_message = f"""
**📺 チャンネル情報: #{channel_info['name']}**

📊 **基本情報**
- カテゴリ: {channel_info['category']}
- トピック: {channel_info['topic']}
- 作成日: {channel_info['created_at']}

💬 **最近のメッセージ**
{recent_msg_list if recent_msg_list else '  メッセージがありません'}
"""
    await ctx.send(info_message)


@bot.command(name='members')
async def members(ctx):
    """チャンネルのオンラインメンバーを表示するコマンド"""
    online_members = await DiscordContext.get_channel_members(ctx.channel)
    
    if not online_members:
        await ctx.send('オンラインメンバーが見つかりませんでした。')
        return
    
    member_list = '\n'.join([
        f"  • {member['name']} ({member['status']})"
        for member in online_members
    ])
    
    info_message = f"""
**👥 このチャンネルのメンバー（オンライン）**

{member_list}

合計: {len(online_members)}人
"""
    await ctx.send(info_message)


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
