"""設定管理モジュール"""

import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv


@dataclass
class Config:
    """アプリケーション設定"""
    
    # Discord設定
    discord_bot_token: str = ""
    discord_channel_ids: List[int] = field(default_factory=list)
    
    # Ollama設定
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    
    # ボット設定
    bot_personality: str = "あなたは親切で知識豊富なAIアシスタントです。日本語で丁寧に回答してください。"
    
    # デバッグ
    debug: bool = False
    
    @classmethod
    def from_env(cls) -> "Config":
        """環境変数から設定を読み込む"""
        load_dotenv()
        
        # チャンネルIDをパース
        channel_ids_str = os.getenv("DISCORD_CHANNEL_IDS", "")
        channel_ids = []
        if channel_ids_str:
            try:
                channel_ids = [int(cid.strip()) for cid in channel_ids_str.split(",") if cid.strip()]
            except ValueError:
                print("警告: DISCORD_CHANNEL_IDSの形式が不正です。整数のカンマ区切りで指定してください。")
        
        return cls(
            discord_bot_token=os.getenv("DISCORD_BOT_TOKEN", ""),
            discord_channel_ids=channel_ids,
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            bot_personality=os.getenv(
                "BOT_PERSONALITY",
                "あなたは親切で知識豊富なAIアシスタントです。日本語で丁寧に回答してください。"
            ),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )
    
    def validate(self) -> List[str]:
        """設定を検証し、エラーメッセージのリストを返す"""
        errors = []
        
        if not self.discord_bot_token:
            errors.append("DISCORD_BOT_TOKEN が設定されていません")
        
        if not self.discord_channel_ids:
            errors.append("DISCORD_CHANNEL_IDS が設定されていません")
        
        return errors
