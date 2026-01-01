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
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set

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

# データディレクトリの設定
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
TRAINING_DATA_FILE = DATA_DIR / 'training_data.jsonl'
LAST_MESSAGE_ID_FILE = DATA_DIR / 'last_message_id.txt'


class ConversationHistoryManager:
    """会話履歴の取得、保存、読み込みを管理するクラス"""
    
    def __init__(self, data_file: Path, last_message_id_file: Path):
        self.data_file = data_file
        self.last_message_id_file = last_message_id_file
        self.processed_message_ids: Set[int] = self._load_processed_ids()
    
    def _load_processed_ids(self) -> Set[int]:
        """処理済みメッセージIDを読み込む"""
        processed_ids = set()
        try:
            if self.last_message_id_file.exists():
                with open(self.last_message_id_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                processed_ids.add(int(line))
                            except ValueError:
                                pass
        except Exception as e:
            logger.warning(f'処理済みID読み込みエラー: {e}')
        return processed_ids
    
    def _save_processed_id(self, message_id: int):
        """処理済みメッセージIDを保存"""
        try:
            with open(self.last_message_id_file, 'a', encoding='utf-8') as f:
                f.write(f'{message_id}\n')
            self.processed_message_ids.add(message_id)
        except Exception as e:
            logger.error(f'処理済みID保存エラー: {e}')
    
    async def fetch_channel_history(self, channel: discord.TextChannel, limit: Optional[int] = None) -> List[discord.Message]:
        """チャンネルの会話履歴を取得"""
        messages = []
        try:
            logger.info(f'チャンネル履歴を取得中... (limit: {limit or "無制限"})')
            async for message in channel.history(limit=limit, oldest_first=True):
                messages.append(message)
            logger.info(f'{len(messages)}件のメッセージを取得しました')
        except Exception as e:
            logger.error(f'履歴取得エラー: {e}')
        return messages
    
    def save_message(self, message: discord.Message, is_assistant: bool = False):
        """メッセージを学習データとして保存"""
        if message.id in self.processed_message_ids:
            return  # 既に処理済み
        
        try:
            author = "assistant" if is_assistant else message.author.display_name
            data = {
                "timestamp": message.created_at.isoformat(),
                "author": author,
                "content": message.content,
                "message_id": str(message.id)
            }
            
            with open(self.data_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
            
            self._save_processed_id(message.id)
            logger.debug(f'メッセージを保存: {message.id}')
        except Exception as e:
            logger.error(f'メッセージ保存エラー: {e}')
    
    def save_conversation_pair(self, user_message: str, assistant_message: str, user_name: str, timestamp: Optional[datetime] = None):
        """会話ペアを学習データとして保存"""
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            # ユーザーメッセージ
            user_data = {
                "timestamp": timestamp.isoformat(),
                "author": user_name,
                "content": user_message,
                "message_id": f"user_{timestamp.timestamp()}"
            }
            
            # アシスタントメッセージ
            assistant_data = {
                "timestamp": timestamp.isoformat(),
                "author": "assistant",
                "content": assistant_message,
                "message_id": f"assistant_{timestamp.timestamp()}"
            }
            
            with open(self.data_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(user_data, ensure_ascii=False) + '\n')
                f.write(json.dumps(assistant_data, ensure_ascii=False) + '\n')
            
            logger.debug('会話ペアを保存しました')
        except Exception as e:
            logger.error(f'会話ペア保存エラー: {e}')
    
    def load_history_for_context(self, max_messages: int = 50) -> List[Dict[str, str]]:
        """会話コンテキスト用に履歴を読み込む"""
        history = []
        try:
            if not self.data_file.exists():
                return history
            
            # ファイルの最後から読み込む（最新の会話を優先）
            lines = []
            with open(self.data_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 最新のメッセージから順に処理
            recent_lines = lines[-max_messages * 2:] if len(lines) > max_messages * 2 else lines
            
            for line in recent_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    role = 'assistant' if data.get('author') == 'assistant' else 'user'
                    content = data.get('content', '')
                    if content:
                        history.append({
                            'role': role,
                            'content': content
                        })
                except json.JSONDecodeError:
                    continue
            
            logger.info(f'{len(history)}件の履歴を読み込みました')
        except Exception as e:
            logger.error(f'履歴読み込みエラー: {e}')
        
        return history
    
    def get_statistics(self) -> Dict[str, int]:
        """保存済みデータの統計を取得"""
        stats = {
            'total_messages': 0,
            'user_messages': 0,
            'assistant_messages': 0
        }
        
        try:
            if not self.data_file.exists():
                return stats
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        stats['total_messages'] += 1
                        if data.get('author') == 'assistant':
                            stats['assistant_messages'] += 1
                        else:
                            stats['user_messages'] += 1
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f'統計取得エラー: {e}')
        
        return stats


class OllamaChat:
    """Ollamaとの会話を管理するクラス"""
    
    def __init__(self, model: str, history_manager: ConversationHistoryManager):
        self.model = model
        self.conversation_history = []
        self.history_manager = history_manager
    
    async def generate_response(self, user_message: str, username: str, use_saved_history: bool = True) -> str:
        """
        ユーザーメッセージに対してOllamaで応答を生成
        
        Args:
            user_message: ユーザーのメッセージ
            username: ユーザー名
            
        Returns:
            Ollamaからの応答テキスト
        """
        try:
            # 保存済み履歴を読み込んでコンテキストに追加
            messages_for_ollama = []
            if use_saved_history:
                saved_history = self.history_manager.load_history_for_context(max_messages=30)
                messages_for_ollama.extend(saved_history)
            
            # 現在の会話履歴を追加
            messages_for_ollama.extend(self.conversation_history)
            
            # 新しいユーザーメッセージを追加
            messages_for_ollama.append({
                'role': 'user',
                'content': f'{username}: {user_message}'
            })
            
            # 会話履歴が長すぎる場合は古いものを削除（最新50件を保持）
            if len(messages_for_ollama) > 50:
                # 保存済み履歴は保持し、現在の会話履歴を削減
                saved_count = len(saved_history) if use_saved_history else 0
                keep_count = min(saved_count, 30)
                messages_for_ollama = messages_for_ollama[:keep_count] + messages_for_ollama[-(50-keep_count):]
            
            # Ollamaにリクエストを送信
            logger.info(f'Ollamaにリクエスト送信: {user_message[:50]}...')
            
            # 非同期でOllama APIを呼び出す
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: ollama_client.chat(
                    model=self.model,
                    messages=messages_for_ollama
                )
            )
            
            assistant_message = response['message']['content']
            
            # 会話履歴に追加
            self.conversation_history.append({
                'role': 'user',
                'content': f'{username}: {user_message}'
            })
            self.conversation_history.append({
                'role': 'assistant',
                'content': assistant_message
            })
            
            # 会話履歴が長すぎる場合は古いものを削除（最新20件を保持）
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            logger.info(f'Ollamaからの応答: {assistant_message[:50]}...')
            return assistant_message
            
        except Exception as e:
            logger.error(f'Ollama API呼び出しエラー: {e}')
            return f'エラーが発生しました: {str(e)}'


# 会話履歴マネージャーの初期化
history_manager = ConversationHistoryManager(TRAINING_DATA_FILE, LAST_MESSAGE_ID_FILE)

# グローバルなOllamaチャットインスタンス
ollama_chat = OllamaChat(OLLAMA_MODEL, history_manager)


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
    
    # チャンネル履歴を取得して保存（毎回実行）
    try:
        channel_messages = await history_manager.fetch_channel_history(message.channel)
        for msg in channel_messages:
            if msg.id not in history_manager.processed_message_ids:
                history_manager.save_message(msg, is_assistant=(msg.author == bot.user))
    except Exception as e:
        logger.error(f'履歴取得・保存エラー: {e}')
    
    # AI짱チェック: メッセージに「AI짱」が含まれるか、ボットへのメンションがあるか
    is_mentioned = bot.user in message.mentions
    contains_trigger = 'AI짱' in message.content
    
    if not (is_mentioned or contains_trigger):
        return  # AI짱と呼ばれていない場合は応答しない
    
    # タイピングインジケーターを表示
    async with message.channel.typing():
        try:
            # メッセージから「AI짱」を除去してクリーンなメッセージを取得
            clean_message = message.content.replace('AI짱', '').strip()
            if not clean_message and not is_mentioned:
                clean_message = message.content  # メンションのみの場合は元のメッセージを使用
            
            # Ollamaで応答を生成
            username = message.author.display_name
            response = await ollama_chat.generate_response(
                clean_message,
                username,
                use_saved_history=True
            )
            
            # 応答を学習データとして保存
            history_manager.save_conversation_pair(
                clean_message,
                response,
                username,
                message.created_at
            )
            
            # 応答を送信（Discordのメッセージ長制限を考慮）
            if len(response) > 2000:
                # 長い場合は分割して送信
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                for chunk in chunks:
                    sent_message = await message.channel.send(chunk)
                    # ボットの応答も保存
                    history_manager.save_message(sent_message, is_assistant=True)
            else:
                sent_message = await message.channel.send(response)
                # ボットの応答も保存
                history_manager.save_message(sent_message, is_assistant=True)
                
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
    stats = history_manager.get_statistics()
    status_message = f"""
**ボットステータス**
- Ollama URL: {OLLAMA_URL}
- モデル: {OLLAMA_MODEL}
- 会話履歴数: {len(ollama_chat.conversation_history)}
- 監視チャンネル: <#{TARGET_CHANNEL_ID}>
- 保存済みメッセージ数: {stats['total_messages']}件
  - ユーザー: {stats['user_messages']}件
  - アシスタント: {stats['assistant_messages']}件
"""
    await ctx.send(status_message)


@bot.command(name='history')
async def history(ctx):
    """保存済み会話履歴の統計を表示するコマンド"""
    stats = history_manager.get_statistics()
    history_message = f"""
**会話履歴統計**
- 総メッセージ数: {stats['total_messages']}件
- ユーザーメッセージ: {stats['user_messages']}件
- アシスタントメッセージ: {stats['assistant_messages']}件
- データファイル: `{TRAINING_DATA_FILE}`
- 処理済みメッセージID数: {len(history_manager.processed_message_ids)}件
"""
    await ctx.send(history_message)


@bot.command(name='export')
async def export(ctx):
    """学習データをエクスポートするコマンド（統計情報を表示）"""
    stats = history_manager.get_statistics()
    
    if stats['total_messages'] == 0:
        await ctx.send('保存されている学習データがありません。')
        return
    
    file_size = 0
    if TRAINING_DATA_FILE.exists():
        file_size = TRAINING_DATA_FILE.stat().st_size
    
    export_message = f"""
**学習データエクスポート情報**
- データファイル: `{TRAINING_DATA_FILE}`
- ファイルサイズ: {file_size / 1024:.2f} KB
- 総メッセージ数: {stats['total_messages']}件
- ユーザーメッセージ: {stats['user_messages']}件
- アシスタントメッセージ: {stats['assistant_messages']}件

データは既に `{TRAINING_DATA_FILE}` にJSONL形式で保存されています。
このファイルをそのままモデルの学習に使用できます。
"""
    await ctx.send(export_message)


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
