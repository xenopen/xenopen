# 🤖 Discord AI Agent

Mac上のOllamaを利用したDiscord AIチャットボットです。特定のチャンネルで会話を聞いて、AIが自動で返答します。

## ✨ 機能

- 🔗 **Ollama連携**: Mac上のローカルLLMを使用
- 💬 **自然な会話**: メンションまたはコマンドでAIと対話
- 📝 **会話履歴**: チャンネルごとに会話コンテキストを保持
- 🎯 **チャンネル指定**: 特定のチャンネルのみを監視
- 🌐 **日本語対応**: 日本語での会話に最適化

## 📋 必要条件

- **Python** 3.9以上
- **Mac** (Ollama動作用)
- **Ollama** インストール済み
- **Discord Bot** トークン

## 🚀 セットアップ

### 1. Ollamaのインストール

```bash
# Homebrewでインストール
brew install ollama

# または公式サイトからダウンロード
# https://ollama.ai/download
```

### 2. AIモデルのダウンロード

```bash
# Ollamaを起動
ollama serve

# 別のターミナルでモデルをダウンロード
ollama pull llama3.2

# 日本語特化モデルを使う場合
ollama pull elyza:jp8b
```

### 3. Discord Botの作成

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 「New Application」をクリック
3. アプリケーション名を入力して作成
4. 左メニューの「Bot」をクリック
5. 「Reset Token」でトークンを取得（**安全に保管**）
6. **重要な設定**:
   - 「MESSAGE CONTENT INTENT」を **有効化**
   - 「SERVER MEMBERS INTENT」を **有効化**

### 4. Botをサーバーに招待

1. 左メニューの「OAuth2」→「URL Generator」をクリック
2. Scopesで「bot」を選択
3. Bot Permissionsで以下を選択:
   - Read Messages/View Channels
   - Send Messages
   - Send Messages in Threads
   - Read Message History
4. 生成されたURLでボットを招待

### 5. チャンネルIDの取得

1. Discord設定 → 詳細設定 → 「開発者モード」を有効化
2. 監視したいチャンネルを右クリック → 「IDをコピー」

### 6. 環境設定

```bash
# リポジトリをクローン
git clone <repository-url>
cd discord-ai-agent

# 環境変数ファイルを作成
cp .env.example .env
```

`.env` ファイルを編集:

```env
# Discord Bot Token（必須）
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# 監視するチャンネルID（必須、カンマ区切りで複数指定可能）
DISCORD_CHANNEL_IDS=123456789012345678

# Ollama設定（オプション）
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# ボットの性格（オプション）
BOT_PERSONALITY=あなたは親切で知識豊富なAIアシスタントです。日本語で丁寧に回答してください。
```

### 7. 依存パッケージのインストール

```bash
# 仮想環境を作成（推奨）
python3 -m venv venv
source venv/bin/activate

# パッケージをインストール
pip install -r requirements.txt
```

### 8. ボットを起動

```bash
# Ollamaが起動していることを確認
ollama serve

# 別のターミナルでボットを起動
python main.py
```

## 📖 使い方

### 基本的な会話

ボットにメンションして話しかけます：

```
@AIBot こんにちは！今日の調子はどう？
```

### コマンド一覧

| コマンド | 説明 |
|---------|------|
| `!ai help` | ヘルプを表示 |
| `!ai clear` | 会話履歴をクリア |
| `!ai status` | ボットの状態を確認 |
| `!ai models` | 利用可能なモデル一覧 |
| `!ai <メッセージ>` | AIに話しかける |

## 🔧 カスタマイズ

### 別のモデルを使用

```env
# .envファイルで指定
OLLAMA_MODEL=elyza:jp8b
```

### ボットの性格を変更

```env
BOT_PERSONALITY=あなたはプログラミングに詳しいエンジニアです。技術的な質問に丁寧に回答してください。
```

## 📁 プロジェクト構造

```
discord-ai-agent/
├── main.py                    # エントリーポイント
├── requirements.txt           # 依存パッケージ
├── .env.example              # 環境変数テンプレート
├── .env                      # 環境変数（作成が必要）
├── README.md                 # このファイル
└── discord_ai_agent/         # メインパッケージ
    ├── __init__.py
    ├── bot.py                # Discord Botロジック
    ├── config.py             # 設定管理
    └── ollama_client.py      # Ollamaクライアント
```

## ⚠️ トラブルシューティング

### Ollamaに接続できない

```bash
# Ollamaが起動しているか確認
curl http://localhost:11434/api/tags

# 起動していない場合
ollama serve
```

### ボットがメッセージに反応しない

1. **MESSAGE CONTENT INTENT** が有効になっているか確認
2. 正しいチャンネルIDが設定されているか確認
3. ボットがそのチャンネルにアクセスできるか確認

### モデルが見つからない

```bash
# インストール済みモデルを確認
ollama list

# モデルをダウンロード
ollama pull llama3.2
```

## 📜 ライセンス

MIT License

## 🤝 貢献

プルリクエストを歓迎します！
