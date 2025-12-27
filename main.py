#!/usr/bin/env python3
"""Discord AI Agent - メインエントリーポイント"""

import sys
import asyncio
from discord_ai_agent.config import Config
from discord_ai_agent.bot import run_bot
from discord_ai_agent.ollama_client import OllamaClient


def check_ollama_sync(config: Config) -> bool:
    """Ollama接続を同期的にチェック"""
    async def _check():
        client = OllamaClient(host=config.ollama_host, model=config.ollama_model)
        return await client.check_connection()
    
    return asyncio.run(_check())


def main():
    """メイン関数"""
    print("=" * 60)
    print("🤖 Discord AI Agent")
    print("=" * 60)
    
    # 設定を読み込み
    print("\n📋 設定を読み込み中...")
    config = Config.from_env()
    
    # 設定を検証
    errors = config.validate()
    if errors:
        print("\n❌ 設定エラー:")
        for error in errors:
            print(f"  - {error}")
        print("\n.env ファイルを確認してください。")
        print("テンプレートは .env.example を参照してください。")
        sys.exit(1)
    
    print(f"  ✓ Ollamaホスト: {config.ollama_host}")
    print(f"  ✓ 使用モデル: {config.ollama_model}")
    print(f"  ✓ 監視チャンネル数: {len(config.discord_channel_ids)}")
    
    if config.debug:
        print(f"  ✓ デバッグモード: 有効")
    
    # Ollama接続テスト
    print("\n🔌 Ollamaサーバーに接続中...")
    if check_ollama_sync(config):
        print("  ✓ Ollama接続成功")
    else:
        print("  ⚠️ Ollamaに接続できません")
        print("     Ollamaが起動しているか確認してください。")
        print("     Mac: 'ollama serve' または Ollama.app を起動")
        print("\n     ボットは起動しますが、AI応答は利用できません。")
    
    # ボットを起動
    print("\n🚀 Discord Botを起動中...")
    print("   (終了するには Ctrl+C を押してください)")
    print("-" * 60)
    
    try:
        run_bot(config)
    except KeyboardInterrupt:
        print("\n\n👋 ボットを終了しました。")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
