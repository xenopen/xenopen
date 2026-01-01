# Discord AI Agent (Ollama連携)

Mac上で動作するDiscordボット。特定のDiscordチャンネルで会話を監視し、Ollamaを使用してAI応答を生成します。

## 機能

- Discordの特定チャンネルでメッセージを監視
- Ollamaを使用したAI応答生成
- 会話履歴の管理
- 「AI짱」人格の固定（systemプロンプト）
- 必要に応じたDiscord情報取得（チャンネル一覧/最近のメッセージ/ユーザー情報など）
- コマンド機能（ping, reset, status, whoami）

## 必要な環境

- Python 3.8以上
- Mac OS
- Ollama（ローカルで起動している必要があります）
- Discord Bot Token

## セットアップ手順

### 1. Ollamaのインストールと起動

```bash
# Ollamaをインストール（まだの場合）
# https://ollama.ai からダウンロードしてインストール

# Ollamaを起動（通常は自動で起動します）
# ターミナルで確認:
curl http://localhost:11434/api/tags
```

### 2. モデルのダウンロード

```bash
# 使用したいモデルをダウンロード（例: llama2）
ollama pull llama2

# 他のモデルも利用可能:
# ollama pull mistral
# ollama pull codellama
# ollama pull llama2:13b
```

### 3. Discord Botの作成

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 「New Application」をクリックしてアプリケーションを作成
3. 「Bot」セクションに移動
4. 「Add Bot」をクリック
5. 「Token」をコピー（後で使用します）
6. 「Privileged Gateway Intents」セクションで以下を有効化:
   - MESSAGE CONTENT INTENT
   - SERVER MEMBERS INTENT（必要に応じて）

### 4. ボットをサーバーに招待

1. 「OAuth2」→「URL Generator」に移動
2. 「Scopes」で以下を選択:
   - `bot`
   - `applications.commands`
3. 「Bot Permissions」で以下を選択:
   - `Send Messages`
   - `Read Message History`
   - `View Channels`
4. 生成されたURLをコピーしてブラウザで開き、ボットをサーバーに招待

### 5. チャンネルIDの取得

1. Discordで開発者モードを有効化:
   - 設定 → 詳細設定 → 開発者モードをON
2. 監視したいチャンネルを右クリック
3. 「IDをコピー」を選択

### 6. プロジェクトのセットアップ

```bash
# リポジトリをクローン（またはダウンロード）
cd /workspace

# 仮想環境を作成（推奨）
python3 -m venv venv
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数ファイルを作成
cp .env.example .env

# .envファイルを編集して設定を入力
# DISCORD_TOKEN: Discord Bot Token
# TARGET_CHANNEL_ID: 監視するチャンネルのID
# OLLAMA_URL: OllamaのURL（デフォルト: http://localhost:11434）
# OLLAMA_MODEL: 使用するモデル名（デフォルト: llama2）
```

### 7. .envファイルの編集

`.env`ファイルを開いて、以下の値を設定してください:

```env
DISCORD_TOKEN=your_discord_bot_token_here
TARGET_CHANNEL_ID=123456789012345678
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2
BOT_PREFIX=!
BOT_PERSONA_NAME=AI짱
BOT_PERSONA_LANGUAGE=ja
```

## 実行方法

```bash
# 仮想環境をアクティベート（まだの場合）
source venv/bin/activate

# ボットを起動
python bot.py
```

ボットが正常に起動すると、指定したチャンネルでメッセージを監視し始めます。

## 使い方

### 基本的な使い方

1. 指定したDiscordチャンネルでメッセージを送信
2. ボットが自動的にメッセージを検知
3. Ollamaで応答を生成してチャンネルに送信

### コマンド

- `!ping` - ボットの応答性をテスト
- `!reset` - 会話履歴をリセット
- `!status` - ボットの状態を表示
- `!whoami` - ボット人格（AI짱）とモデル名を表示

### Discord情報の取得（LLMが必要なとき）

ボットは、Ollama(LLama)が「追加の情報が必要」と判断した場合に限り、Discordから情報を取得して回答精度を上げます。
内部的には、モデルが一時的に **ツール呼び出し用のJSON** を出力し、ボットがそのJSONに従ってDiscord APIから情報を取得し、結果をモデルへ渡した上で最終回答を返します。

現状のツール例:

- `discord.get_context`（現在のギルド/チャンネル情報）
- `discord.list_channels`（テキストチャンネル一覧）
- `discord.get_recent_messages`（指定チャンネルの最近のメッセージ）
- `discord.get_user`（ユーザー情報/ロール等）

## トラブルシューティング

### Ollamaに接続できない

- Ollamaが起動しているか確認: `curl http://localhost:11434/api/tags`
- `.env`ファイルの`OLLAMA_URL`が正しいか確認

### ボットがメッセージに反応しない

- `.env`ファイルの`TARGET_CHANNEL_ID`が正しいか確認
- ボットがチャンネルにアクセスできるか確認
- ボットの権限（MESSAGE CONTENT INTENT）が有効か確認

### モデルが見つからない

- モデルがダウンロードされているか確認: `ollama list`
- `.env`ファイルの`OLLAMA_MODEL`が正しいか確認

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
