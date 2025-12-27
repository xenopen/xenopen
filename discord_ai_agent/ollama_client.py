"""Ollamaクライアントモジュール"""

import asyncio
from typing import List, Dict, Optional
import ollama
from ollama import AsyncClient


class OllamaClient:
    """Ollamaとの通信を担当するクライアント"""
    
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.2"):
        self.host = host
        self.model = model
        self.client = AsyncClient(host=host)
        self._conversation_history: Dict[int, List[Dict[str, str]]] = {}
    
    async def check_connection(self) -> bool:
        """Ollamaサーバーへの接続を確認"""
        try:
            await self.client.list()
            return True
        except Exception as e:
            print(f"Ollama接続エラー: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """利用可能なモデル一覧を取得"""
        try:
            response = await self.client.list()
            return [model.model for model in response.models]
        except Exception as e:
            print(f"モデル一覧取得エラー: {e}")
            return []
    
    async def chat(
        self,
        message: str,
        conversation_id: int,
        system_prompt: Optional[str] = None,
        max_history: int = 10
    ) -> str:
        """メッセージを送信してレスポンスを取得
        
        Args:
            message: ユーザーからのメッセージ
            conversation_id: 会話を識別するID（通常はDiscordチャンネルID）
            system_prompt: システムプロンプト（ボットの性格設定）
            max_history: 保持する会話履歴の最大数
            
        Returns:
            AIからのレスポンス
        """
        # 会話履歴を取得または初期化
        if conversation_id not in self._conversation_history:
            self._conversation_history[conversation_id] = []
        
        history = self._conversation_history[conversation_id]
        
        # メッセージを構築
        messages = []
        
        # システムプロンプトを追加
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # 会話履歴を追加
        messages.extend(history)
        
        # 新しいユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })
        
        try:
            # Ollamaにリクエスト
            response = await self.client.chat(
                model=self.model,
                messages=messages
            )
            
            assistant_message = response.message.content
            
            # 会話履歴を更新
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": assistant_message})
            
            # 履歴が長すぎる場合は古いものを削除
            if len(history) > max_history * 2:
                self._conversation_history[conversation_id] = history[-(max_history * 2):]
            
            return assistant_message
            
        except Exception as e:
            error_msg = f"Ollama通信エラー: {e}"
            print(error_msg)
            return f"申し訳ありません。エラーが発生しました: {str(e)}"
    
    def clear_history(self, conversation_id: int) -> None:
        """特定の会話履歴をクリア"""
        if conversation_id in self._conversation_history:
            del self._conversation_history[conversation_id]
    
    def clear_all_history(self) -> None:
        """全ての会話履歴をクリア"""
        self._conversation_history.clear()


async def test_ollama():
    """Ollama接続テスト"""
    client = OllamaClient()
    
    print("Ollamaサーバーに接続中...")
    if await client.check_connection():
        print("✓ 接続成功")
        
        models = await client.list_models()
        print(f"利用可能なモデル: {models}")
        
        if models:
            response = await client.chat(
                message="こんにちは！自己紹介をしてください。",
                conversation_id=0,
                system_prompt="あなたは親切なAIアシスタントです。"
            )
            print(f"レスポンス: {response}")
    else:
        print("✗ 接続失敗 - Ollamaが起動しているか確認してください")


if __name__ == "__main__":
    asyncio.run(test_ollama())
