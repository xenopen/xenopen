"""Discord Botメインモジュール"""

import discord
from discord.ext import commands
from typing import Optional

from .config import Config
from .ollama_client import OllamaClient


class DiscordAIBot(commands.Bot):
    """Ollama連携Discord Bot"""
    
    def __init__(self, config: Config):
        # Intentsの設定
        intents = discord.Intents.default()
        intents.message_content = True  # メッセージ内容を読み取るために必要
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix="!ai ",
            intents=intents,
            help_command=None  # デフォルトのヘルプコマンドを無効化
        )
        
        self.config = config
        self.ollama = OllamaClient(
            host=config.ollama_host,
            model=config.ollama_model
        )
        self._setup_commands()
    
    def _setup_commands(self) -> None:
        """コマンドをセットアップ"""
        
        @self.command(name="help")
        async def help_command(ctx: commands.Context):
            """ヘルプを表示"""
            embed = discord.Embed(
                title="🤖 AI Bot ヘルプ",
                description="このボットはOllamaを使用したAIアシスタントです。",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="💬 会話方法",
                value="ボットにメンションするか、`!ai` コマンドを使用してください。",
                inline=False
            )
            embed.add_field(
                name="📝 コマンド一覧",
                value=(
                    "`!ai help` - このヘルプを表示\n"
                    "`!ai clear` - 会話履歴をクリア\n"
                    "`!ai status` - ボットの状態を確認\n"
                    "`!ai models` - 利用可能なモデル一覧"
                ),
                inline=False
            )
            embed.set_footer(text=f"使用モデル: {self.config.ollama_model}")
            await ctx.send(embed=embed)
        
        @self.command(name="clear")
        async def clear_command(ctx: commands.Context):
            """会話履歴をクリア"""
            self.ollama.clear_history(ctx.channel.id)
            await ctx.send("✅ 会話履歴をクリアしました。")
        
        @self.command(name="status")
        async def status_command(ctx: commands.Context):
            """ボットの状態を確認"""
            # Ollama接続確認
            ollama_connected = await self.ollama.check_connection()
            
            embed = discord.Embed(
                title="🔧 ボット状態",
                color=discord.Color.green() if ollama_connected else discord.Color.red()
            )
            embed.add_field(
                name="Ollama接続",
                value="✅ 接続済み" if ollama_connected else "❌ 未接続",
                inline=True
            )
            embed.add_field(
                name="モデル",
                value=self.config.ollama_model,
                inline=True
            )
            embed.add_field(
                name="監視チャンネル数",
                value=str(len(self.config.discord_channel_ids)),
                inline=True
            )
            await ctx.send(embed=embed)
        
        @self.command(name="models")
        async def models_command(ctx: commands.Context):
            """利用可能なモデル一覧を表示"""
            models = await self.ollama.list_models()
            
            if models:
                model_list = "\n".join([f"• {model}" for model in models])
                embed = discord.Embed(
                    title="📦 利用可能なモデル",
                    description=model_list,
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"現在使用中: {self.config.ollama_model}")
            else:
                embed = discord.Embed(
                    title="📦 利用可能なモデル",
                    description="モデルが見つかりませんでした。Ollamaが起動しているか確認してください。",
                    color=discord.Color.red()
                )
            
            await ctx.send(embed=embed)
    
    async def on_ready(self) -> None:
        """ボット起動時のイベント"""
        print(f"{'='*50}")
        print(f"🤖 {self.user.name} が起動しました！")
        print(f"{'='*50}")
        print(f"Bot ID: {self.user.id}")
        print(f"使用モデル: {self.config.ollama_model}")
        print(f"Ollamaホスト: {self.config.ollama_host}")
        print(f"監視チャンネルID: {self.config.discord_channel_ids}")
        
        # Ollama接続確認
        if await self.ollama.check_connection():
            print("✅ Ollamaサーバーに接続しました")
        else:
            print("⚠️ Ollamaサーバーに接続できません。Ollamaが起動しているか確認してください。")
        
        print(f"{'='*50}")
        
        # ステータスを設定
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="会話を待っています..."
            )
        )
    
    async def on_message(self, message: discord.Message) -> None:
        """メッセージ受信時のイベント"""
        # 自分自身のメッセージは無視
        if message.author == self.user:
            return
        
        # Botのメッセージは無視
        if message.author.bot:
            return
        
        # コマンド処理を先に実行
        await self.process_commands(message)
        
        # コマンドとして処理された場合はAI応答しない
        ctx = await self.get_context(message)
        if ctx.valid:
            return
        
        # 監視対象のチャンネルかチェック
        if self.config.discord_channel_ids and message.channel.id not in self.config.discord_channel_ids:
            return
        
        # メンションされた場合、またはDMの場合に反応
        should_respond = False
        content = message.content
        
        # ボットがメンションされているかチェック
        if self.user.mentioned_in(message):
            should_respond = True
            # メンションを削除してメッセージを取得
            content = content.replace(f"<@{self.user.id}>", "").replace(f"<@!{self.user.id}>", "").strip()
        
        # DMの場合は常に反応
        if isinstance(message.channel, discord.DMChannel):
            should_respond = True
        
        if not should_respond:
            return
        
        # 空のメッセージは無視
        if not content:
            await message.reply("何かメッセージを入力してください！")
            return
        
        # タイピング表示
        async with message.channel.typing():
            # AIからの応答を取得
            response = await self.ollama.chat(
                message=content,
                conversation_id=message.channel.id,
                system_prompt=self.config.bot_personality
            )
        
        # 応答が長すぎる場合は分割して送信
        if len(response) <= 2000:
            await message.reply(response)
        else:
            # 2000文字ごとに分割
            chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await message.reply(chunk)
                else:
                    await message.channel.send(chunk)
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """コマンドエラー時のイベント"""
        if isinstance(error, commands.CommandNotFound):
            # 不明なコマンドはAI会話として処理
            content = ctx.message.content
            if content.startswith("!ai "):
                content = content[4:].strip()
                if content:
                    async with ctx.typing():
                        response = await self.ollama.chat(
                            message=content,
                            conversation_id=ctx.channel.id,
                            system_prompt=self.config.bot_personality
                        )
                    await ctx.reply(response)
        else:
            print(f"コマンドエラー: {error}")
            await ctx.send(f"❌ エラーが発生しました: {error}")


def run_bot(config: Config) -> None:
    """ボットを起動"""
    bot = DiscordAIBot(config)
    bot.run(config.discord_bot_token)
