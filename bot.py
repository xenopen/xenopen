#!/usr/bin/env python3
"""
Discord AI Agent - Ollama統合
Mac上のOllamaを使用してDiscordチャンネルで会話するAIボット
"""

import discord
from discord.ext import commands
import os
import asyncio
import aiohttp
import json
from typing import Optional
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# 設定
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama2')
TARGET_CHANNEL_ID = os.getenv('TARGET_CHANNEL_ID')  # 特定のチャンネルID（オプション）
BOT_PREFIX = os.getenv('BOT_PREFIX', '!')

# Botのインテント設定
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

# Botの初期化
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)


class OllamaClient:
    """Ollama APIとの通信を管理するクライアント"""
    
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip('/')
        self.model = model
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Ollamaを使用してテキストを生成
        
        Args:
            prompt: ユーザーからのプロンプト
            system_prompt: システムプロンプト（オプション）
        
        Returns:
            生成されたテキスト
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '応答を生成できませんでした。')
                    else:
                        error_text = await response.text()
                        print(f"Ollama APIエラー: {response.status} - {error_text}")
                        return f"エラー: Ollama APIからの応答がありません（ステータス: {response.status}）"
        except aiohttp.ClientError as e:
            print(f"接続エラー: {e}")
            return "エラー: Ollamaサーバーに接続できません。Ollamaが起動しているか確認してください。"
        except Exception as e:
            print(f"予期しないエラー: {e}")
            return f"エラー: {str(e)}"
    
    async def chat(self, messages: list) -> str:
        """
        Ollamaのチャット機能を使用（会話履歴を保持）
        
        Args:
            messages: 会話履歴のリスト [{"role": "user", "content": "..."}, ...]
        
        Returns:
            生成されたテキスト
        """
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('message', {}).get('content', '応答を生成できませんでした。')
                    else:
                        error_text = await response.text()
                        print(f"Ollama APIエラー: {response.status} - {error_text}")
                        return f"エラー: Ollama APIからの応答がありません（ステータス: {response.status}）"
        except aiohttp.ClientError as e:
            print(f"接続エラー: {e}")
            return "エラー: Ollamaサーバーに接続できません。Ollamaが起動しているか確認してください。"
        except Exception as e:
            print(f"予期しないエラー: {e}")
            return f"エラー: {str(e)}"


# Ollamaクライアントのインスタンス化
ollama_client = OllamaClient(OLLAMA_API_URL, OLLAMA_MODEL)


@bot.event
async def on_ready():
    """Botが起動したときのイベント"""
    print(f'{bot.user} としてログインしました！')
    print(f'使用モデル: {OLLAMA_MODEL}')
    print(f'Ollama URL: {OLLAMA_API_URL}')
    if TARGET_CHANNEL_ID:
        print(f'監視チャンネルID: {TARGET_CHANNEL_ID}')
    print('準備完了！')


@bot.event
async def on_message(message):
    """メッセージを受信したときのイベント"""
    # Bot自身のメッセージは無視
    if message.author == bot.user:
        return
    
    # 特定のチャンネルIDが設定されている場合、そのチャンネルのみ監視
    if TARGET_CHANNEL_ID and str(message.channel.id) != TARGET_CHANNEL_ID:
        # コマンドは処理する
        await bot.process_commands(message)
        return
    
    # Botがメンションされた場合に反応
    if bot.user.mentioned_in(message):
        # メンションを除去してクリーンなメッセージを取得
        clean_message = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        if not clean_message:
            await message.channel.send('何か話しかけてください！')
            return
        
        # タイピングインジケーターを表示
        async with message.channel.typing():
            # Ollamaで応答を生成
            response = await ollama_client.generate(
                prompt=clean_message,
                system_prompt="あなたは親切で役立つAIアシスタントです。日本語で自然に会話してください。"
            )
            
            # 応答が長すぎる場合は分割（Discord の制限は2000文字）
            if len(response) > 2000:
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                for chunk in chunks:
                    await message.channel.send(chunk)
            else:
                await message.channel.send(response)
    
    # コマンドの処理を続行
    await bot.process_commands(message)


@bot.command(name='ask')
async def ask_command(ctx, *, question: str):
    """
    AIに質問するコマンド
    使用例: !ask 今日の天気は？
    """
    async with ctx.typing():
        response = await ollama_client.generate(
            prompt=question,
            system_prompt="あなたは親切で役立つAIアシスタントです。日本語で自然に会話してください。"
        )
        
        if len(response) > 2000:
            chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(response)


@bot.command(name='chat')
async def chat_command(ctx, *, message_text: str):
    """
    チャット形式でAIと会話するコマンド（会話履歴を含む）
    使用例: !chat こんにちは！
    """
    async with ctx.typing():
        # 簡易的な会話履歴（実際にはデータベースなどで管理するのが望ましい）
        messages = [
            {"role": "system", "content": "あなたは親切で役立つAIアシスタントです。日本語で自然に会話してください。"},
            {"role": "user", "content": message_text}
        ]
        
        response = await ollama_client.chat(messages)
        
        if len(response) > 2000:
            chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(response)


@bot.command(name='model')
async def model_command(ctx):
    """現在使用中のモデル情報を表示"""
    await ctx.send(f'現在使用中のモデル: **{OLLAMA_MODEL}**\nOllama URL: {OLLAMA_API_URL}')


@bot.command(name='help_ai')
async def help_ai_command(ctx):
    """Botの使い方を表示"""
    help_text = """
**Discord AI Agent - 使い方**

🤖 **基本的な使い方:**
• ボットをメンション（@ボット名）して話しかけると返事します
• 特定のチャンネルでのみ動作するように設定できます

📝 **コマンド:**
• `!ask <質問>` - AIに質問する
• `!chat <メッセージ>` - チャット形式で会話する
• `!model` - 現在のモデル情報を表示
• `!help_ai` - このヘルプを表示

💡 **使用例:**
```
@ボット名 こんにちは！
!ask Pythonの基本的な文法を教えて
!chat 今日は良い天気ですね
```

⚙️ **使用モデル:** {OLLAMA_MODEL}
    """
    await ctx.send(help_text)


def main():
    """メイン関数"""
    if not DISCORD_TOKEN:
        print("エラー: DISCORD_TOKENが設定されていません。")
        print(".envファイルにDISCORD_TOKENを設定してください。")
        return
    
    try:
        bot.run(DISCORD_TOKEN)
    except discord.LoginFailure:
        print("エラー: Discordへのログインに失敗しました。トークンを確認してください。")
    except Exception as e:
        print(f"エラー: {e}")


if __name__ == '__main__':
    main()
