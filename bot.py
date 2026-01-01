"""
Discord AI Agent using Ollama
Mac上で動作するDiscordボット。特定のチャンネルで会話を聞いてOllamaで応答します。
"""

import os
import re
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv
import ollama
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

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
BOT_PERSONA_NAME = os.getenv('BOT_PERSONA_NAME', 'AI짱')
BOT_PERSONA_LANGUAGE = os.getenv('BOT_PERSONA_LANGUAGE', 'ja')

SYSTEM_PROMPT = f"""\
あなたはDiscord上で稼働している会話ボット「{BOT_PERSONA_NAME}」です。あなた自身は人間ではなくDiscord Botです。

## 最重要ルール（常に守る）
- 自分の名前は常に「{BOT_PERSONA_NAME}」として認識すること
- 自分はDiscordのボットであり、Discordのチャンネル内会話を支援する存在であること
- 返答は基本的に日本語で行うこと（必要があれば英語も併記してよい）
- 事実が不明なものは推測で断言せず、不明と言うこと

## Discord情報取得（必要なときだけ）
あなたは「ツール呼び出し」を要求することで、Discordから情報を取得できます。
情報が必要な場合は、**次のJSONだけ**を出力してください（他の文章や前置きは禁止）:
{{"tool_calls":[{{"name":"<tool_name>","arguments":{{...}}}}]}}

利用可能なツール:
- discord.get_context: {{"arguments":{{}}}}
- discord.list_channels: {{"arguments":{{"guild_id": null}}}}
- discord.get_recent_messages: {{"arguments":{{"channel_id": null, "limit": 20}}}}  # limitは1〜50
- discord.get_user: {{"arguments":{{"user_id": null}}}}

ツール結果が与えられたら、その内容を使ってユーザーに自然な返答を作成してください。
返答のときはツール呼び出しJSONを出力しないでください。
"""

# Discord intentsの設定
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# ボットの初期化
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# Ollamaクライアントの初期化
ollama_client = ollama.Client(host=OLLAMA_URL)


class DiscordTools:
    """Ollamaが要求したときにDiscord情報を取得するツール群"""

    def __init__(self, bot_instance: commands.Bot):
        self.bot = bot_instance

    async def get_context(self, message: discord.Message) -> Dict[str, Any]:
        guild = message.guild
        channel = message.channel
        me = message.guild.me if guild else None  # type: ignore[attr-defined]

        return {
            "bot_user": {
                "id": str(self.bot.user.id) if self.bot.user else None,
                "name": str(self.bot.user) if self.bot.user else None,
            },
            "guild": {
                "id": str(guild.id) if guild else None,
                "name": guild.name if guild else None,
            },
            "channel": {
                "id": str(channel.id) if channel else None,
                "name": getattr(channel, "name", None),
                "type": str(getattr(channel, "type", None)),
            },
            "bot_member": {
                "display_name": me.display_name if me else None,
            },
        }

    async def list_channels(self, message: discord.Message, guild_id: Optional[int]) -> Dict[str, Any]:
        guild: Optional[discord.Guild]
        if guild_id is None:
            guild = message.guild
        else:
            guild = self.bot.get_guild(guild_id)

        if guild is None:
            return {"error": "guild_not_found"}

        text_channels = []
        for ch in guild.text_channels:
            text_channels.append({"id": str(ch.id), "name": ch.name, "category": ch.category.name if ch.category else None})

        return {"guild": {"id": str(guild.id), "name": guild.name}, "text_channels": text_channels}

    async def get_recent_messages(self, message: discord.Message, channel_id: Optional[int], limit: int) -> Dict[str, Any]:
        if limit < 1:
            limit = 1
        if limit > 50:
            limit = 50

        channel: Optional[discord.abc.Messageable]
        if channel_id is None:
            channel = message.channel
        else:
            fetched = self.bot.get_channel(channel_id)
            if fetched is None:
                return {"error": "channel_not_found"}
            channel = fetched  # type: ignore[assignment]

        if not hasattr(channel, "history"):
            return {"error": "channel_has_no_history"}

        msgs = []
        async for m in channel.history(limit=limit, oldest_first=False):  # type: ignore[attr-defined]
            msgs.append(
                {
                    "id": str(m.id),
                    "author": {
                        "id": str(m.author.id),
                        "name": getattr(m.author, "name", None),
                        "display_name": getattr(m.author, "display_name", None),
                        "bot": getattr(m.author, "bot", None),
                    },
                    "content": m.content,
                    "created_at": m.created_at.isoformat(),
                }
            )

        return {"channel_id": str(getattr(channel, "id", None)), "messages": msgs}

    async def get_user(self, message: discord.Message, user_id: Optional[int]) -> Dict[str, Any]:
        if user_id is None:
            return {"error": "user_id_required"}

        guild = message.guild
        if guild is None:
            return {"error": "guild_required"}

        member = guild.get_member(user_id)
        if member is None:
            try:
                member = await guild.fetch_member(user_id)
            except Exception:
                member = None

        if member is None:
            return {"error": "member_not_found"}

        return {
            "id": str(member.id),
            "name": member.name,
            "display_name": member.display_name,
            "bot": member.bot,
            "roles": [{"id": str(r.id), "name": r.name} for r in member.roles if r.name != "@everyone"],
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        }


class OllamaChat:
    """Ollamaとの会話を管理するクラス"""
    
    def __init__(self, model: str):
        self.model = model
        self.conversation_history: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _trim_history(self, keep_last: int = 40) -> None:
        """
        会話履歴が肥大化しすぎないように調整。
        先頭のsystemプロンプトは必ず保持する。
        """
        if len(self.conversation_history) <= keep_last:
            return
        system_msg = self.conversation_history[0]
        tail = self.conversation_history[-(keep_last - 1) :]
        self.conversation_history = [system_msg, *tail]

    @staticmethod
    def _extract_tool_calls(text: str) -> Optional[Dict[str, Any]]:
        """
        モデル出力からツール呼び出しJSONを抽出。
        期待形式: {"tool_calls":[{"name":"...","arguments":{...}}]}
        """
        # ```json ... ``` 形式を優先
        fenced = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
        candidates: List[str] = []
        if fenced:
            candidates.append(fenced.group(1))
        # 生JSONっぽい塊も候補に入れる（混在出力対策）
        if "tool_calls" in text:
            raw = re.search(r"(\{[\s\S]*\})", text)
            if raw:
                candidates.append(raw.group(1))

        for cand in candidates:
            try:
                obj = json.loads(cand)
            except Exception:
                continue
            if isinstance(obj, dict) and isinstance(obj.get("tool_calls"), list):
                return obj
        return None

    async def _call_ollama(self) -> str:
        logger.info("Ollamaにリクエスト送信...")
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: ollama_client.chat(model=self.model, messages=self.conversation_history),
        )
        return response["message"]["content"]
    
    async def generate_response(self, message: discord.Message) -> str:
        """
        ユーザーメッセージに対してOllamaで応答を生成
        
        Args:
            message: Discordメッセージ
            
        Returns:
            Ollamaからの応答テキスト
        """
        try:
            user_message = message.content
            username = message.author.display_name

            # 会話履歴に追加
            self.conversation_history.append({
                'role': 'user',
                'content': f'{username}: {user_message}'
            })
            
            self._trim_history()

            tools = DiscordTools(bot)

            # ツール呼び出しが必要な場合に備えて複数ターン回す
            for _ in range(4):
                assistant_message = await self._call_ollama()

                # 会話履歴に追加
                self.conversation_history.append({'role': 'assistant', 'content': assistant_message})
                self._trim_history()

                tool_req = self._extract_tool_calls(assistant_message)
                if not tool_req:
                    logger.info(f'Ollamaからの応答: {assistant_message[:50]}...')
                    return assistant_message

                # ツール実行
                results = []
                for call in tool_req.get("tool_calls", []):
                    name = call.get("name")
                    args = call.get("arguments") or {}

                    try:
                        if name == "discord.get_context":
                            res = await tools.get_context(message)
                        elif name == "discord.list_channels":
                            guild_id = args.get("guild_id")
                            res = await tools.list_channels(message, int(guild_id) if guild_id is not None else None)
                        elif name == "discord.get_recent_messages":
                            channel_id = args.get("channel_id")
                            limit = int(args.get("limit", 20))
                            res = await tools.get_recent_messages(message, int(channel_id) if channel_id is not None else None, limit)
                        elif name == "discord.get_user":
                            user_id = args.get("user_id")
                            res = await tools.get_user(message, int(user_id) if user_id is not None else None)
                        else:
                            res = {"error": "unknown_tool", "tool": name}
                    except Exception as e:
                        res = {"error": "tool_execution_failed", "tool": name, "message": str(e)}

                    results.append({"name": name, "result": res})

                # ツール結果をsystemとして与える（モデルが参照できる形に）
                self.conversation_history.append(
                    {
                        "role": "system",
                        "content": "[tool_results]\n" + json.dumps(results, ensure_ascii=False),
                    }
                )
                self.conversation_history.append(
                    {
                        "role": "system",
                        "content": "上記ツール結果を使ってユーザーへ返答を作成してください。ツール呼び出しJSONは出力しないでください。",
                    }
                )
                self._trim_history()

            # 4ターン回しても確定応答が出ない場合
            return "ごめんね、情報取得の途中で行き詰まっちゃった。もう一度聞きたい内容を短くして送ってね。"
            
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
    ollama_chat.conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    await ctx.send('会話履歴をリセットしました。')


@bot.command(name='whoami')
async def whoami(ctx):
    """ボットの人格設定を表示するコマンド"""
    await ctx.send(f'私はDiscordボット「{BOT_PERSONA_NAME}」だよ。モデルは `{OLLAMA_MODEL}` を使ってる。')


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
