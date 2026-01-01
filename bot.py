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
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set, Union

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
HISTORY_AFTER = os.getenv('HISTORY_AFTER')  # 日付基準で履歴を取得する開始日時

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


def parse_date_string(date_str: str) -> Optional[datetime]:
    """
    日付文字列をdatetimeオブジェクトに変換
    
    Args:
        date_str: 日付文字列（ISO形式: "2024-01-01T00:00:00" または "2024-01-01"）
    
    Returns:
        datetimeオブジェクト、パースに失敗した場合はNone
    """
    if not date_str:
        return None
    
    try:
        # ISO形式を試す
        if 'T' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            # 日付のみの場合は時刻を00:00:00に設定
            return datetime.fromisoformat(date_str + 'T00:00:00')
    except ValueError:
        try:
            # その他の形式を試す
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d %H:%M:%S',
                '%Y-%m-%d',
                '%Y/%m/%d'
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        except Exception:
            pass
    
    logger.warning(f'日付文字列のパースに失敗しました: {date_str}')
    return None


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
        """チャンネルの会話履歴を取得（レート制限を考慮）"""
        messages = []
        try:
            logger.info(f'チャンネル履歴を取得中... (limit: {limit or "無制限"})')
            count = 0
            async for message in channel.history(limit=limit, oldest_first=True):
                messages.append(message)
                count += 1
                # レート制限を避けるため、一定数ごとに少し待機
                if count % 50 == 0:
                    await asyncio.sleep(0.5)
            logger.info(f'{len(messages)}件のメッセージを取得しました')
        except discord.HTTPException as e:
            if e.status == 429:
                logger.warning('レート制限に達しました。しばらく待機します...')
                await asyncio.sleep(5)
            else:
                logger.error(f'履歴取得エラー: {e}')
        except Exception as e:
            logger.error(f'履歴取得エラー: {e}')
        return messages
    
    async def fetch_history_by_date_range(
        self,
        channel: discord.TextChannel,
        after_date: datetime,
        limit_per_batch: int = 100
    ) -> List[discord.Message]:
        """
        日付基準で段階的に全メッセージを取得
        
        Args:
            channel: チャンネル
            after_date: 開始日時
            limit_per_batch: 1回の取得で取得する最大件数（デフォルト: 100）
        
        Returns:
            取得した全メッセージのリスト
        """
        all_messages = []
        current_date = after_date
        batch_count = 0
        
        logger.info(f'日付基準で段階的に履歴を取得開始: {after_date.isoformat()}以降')
        
        while True:
            try:
                batch_count += 1
                batch_messages = []
                count = 0
                
                # 現在の日付以降のメッセージを取得
                async for message in channel.history(
                    after=current_date,
                    limit=limit_per_batch,
                    oldest_first=True
                ):
                    batch_messages.append(message)
                    count += 1
                    # レート制限を避けるため、一定数ごとに少し待機
                    if count % 50 == 0:
                        await asyncio.sleep(0.5)
                
                # 取得したメッセージが0件の場合、ループ終了
                if len(batch_messages) == 0:
                    logger.info('これ以上取得できるメッセージがありません。取得を終了します。')
                    break
                
                # 取得したメッセージを追加
                all_messages.extend(batch_messages)
                
                # 取得したメッセージの中で最新の日付を取得
                latest_date = max(msg.created_at for msg in batch_messages)
                
                # 進捗表示
                logger.info(
                    f'バッチ {batch_count}: {len(batch_messages)}件取得 '
                    f'(累計: {len(all_messages)}件, 最新日時: {latest_date.isoformat()})'
                )
                
                # 最新日付を1ミリ秒進めて、次の取得の開始点とする
                # これにより、同じメッセージを重複して取得することを防ぐ
                current_date = latest_date + timedelta(milliseconds=1)
                
                # レート制限を避けるため、バッチ間で待機
                await asyncio.sleep(1)
                
            except discord.HTTPException as e:
                if e.status == 429:
                    logger.warning('レート制限に達しました。しばらく待機します...')
                    await asyncio.sleep(5)
                else:
                    logger.error(f'履歴取得エラー: {e}')
                    break
            except Exception as e:
                logger.error(f'履歴取得エラー: {e}')
                break
        
        logger.info(f'段階的履歴取得完了: 合計 {len(all_messages)}件のメッセージを取得しました')
        return all_messages
    
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
    
    def get_latest_timestamp(self) -> Optional[datetime]:
        """
        保存済みメッセージの中で最新のtimestampを取得
        
        Returns:
            最新のtimestamp（datetimeオブジェクト）、存在しない場合はNone
        """
        try:
            if not self.data_file.exists():
                return None
            
            latest_timestamp = None
            
            # ファイルの最後から読み込む（最新のメッセージを優先的に確認）
            # 効率化のため、最後の1000行を確認
            with open(self.data_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 最後から順に確認（最新のメッセージから）
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    timestamp_str = data.get('timestamp')
                    if timestamp_str:
                        # ISO形式のtimestampをパース
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            if latest_timestamp is None or timestamp > latest_timestamp:
                                latest_timestamp = timestamp
                        except (ValueError, AttributeError):
                            continue
                except json.JSONDecodeError:
                    continue
            
            if latest_timestamp:
                logger.info(f'保存済みメッセージの最新timestamp: {latest_timestamp.isoformat()}')
            else:
                logger.info('保存済みメッセージが見つかりませんでした')
            
            return latest_timestamp
            
        except Exception as e:
            logger.error(f'最新timestamp取得エラー: {e}')
            return None


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
            saved_history = []
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
    
    # 初回起動時にチャンネル履歴を取得（バックグラウンドで実行）
    try:
        channel = bot.get_channel(TARGET_CHANNEL_ID)
        if channel:
            logger.info('初回起動時の履歴取得を開始...')
            # バックグラウンドタスクとして実行（レート制限を避けるため）
            asyncio.create_task(fetch_initial_history(channel))
    except Exception as e:
        logger.error(f'初回履歴取得エラー: {e}')


async def fetch_initial_history(channel: discord.TextChannel):
    """初回起動時にチャンネル履歴を取得（レート制限を考慮）"""
    try:
        # 保存済みメッセージの最新timestampを取得
        latest_timestamp = history_manager.get_latest_timestamp()
        
        # 優先順位: 1. 保存済みメッセージの最新timestamp, 2. 環境変数HISTORY_AFTER, 3. 全履歴
        after_date = None
        
        if latest_timestamp:
            # 保存済みメッセージの最新timestamp以降を取得
            after_date = latest_timestamp
            logger.info(f'既存データの最新日時以降を取得します: {after_date.isoformat()}以降')
        elif HISTORY_AFTER:
            # 環境変数HISTORY_AFTERが設定されている場合
            after_date = parse_date_string(HISTORY_AFTER)
            if after_date:
                logger.info(f'環境変数HISTORY_AFTERに基づいて履歴を取得します: {after_date.isoformat()}以降')
            else:
                logger.warning(f'HISTORY_AFTERの日付パースに失敗しました: {HISTORY_AFTER}。全履歴を取得します。')
        
        # 日付が指定されている場合は段階的取得を使用
        if after_date:
            messages = await history_manager.fetch_history_by_date_range(channel, after_date)
        else:
            logger.info('チャンネル履歴を取得中...（時間がかかる場合があります）')
            # 全履歴を取得（limit=Noneで全件取得）
            messages = await history_manager.fetch_channel_history(channel, limit=None)
        
        logger.info(f'{len(messages)}件のメッセージを取得しました。処理を開始...')
        
        new_count = 0
        total_count = len(messages)
        
        for idx, msg in enumerate(messages, 1):
            if msg.id not in history_manager.processed_message_ids:
                history_manager.save_message(msg, is_assistant=(msg.author == bot.user))
                new_count += 1
            
            # 進捗表示（100件ごと、または最後）
            if idx % 100 == 0 or idx == total_count:
                logger.info(f'進捗: {idx}/{total_count}件処理済み（新規: {new_count}件）')
        
        logger.info(f'初回履歴取得完了: {new_count}件の新しいメッセージを保存しました（総数: {total_count}件）')
    except Exception as e:
        logger.error(f'初回履歴取得エラー: {e}')


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
    
    # 新しいメッセージのみを保存（全履歴を取得しない）
    try:
        if message.id not in history_manager.processed_message_ids:
            history_manager.save_message(message, is_assistant=False)
    except Exception as e:
        logger.error(f'メッセージ保存エラー: {e}')
    
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
            
            # 応答を送信（Discordのメッセージ長制限を考慮）
            if len(response) > 2000:
                # 長い場合は分割して送信
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                for chunk in chunks:
                    sent_message = await message.channel.send(chunk)
                    # ボットの応答を保存（save_messageのみを使用して重複を防ぐ）
                    history_manager.save_message(sent_message, is_assistant=True)
            else:
                sent_message = await message.channel.send(response)
                # ボットの応答を保存（save_messageのみを使用して重複を防ぐ）
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
