# Discord AI Agent (Ollama連携) - AI짱

Mac上で動作するDiscordボット「AI짱」。特定のDiscordチャンネルで会話を監視し、Ollamaを使用してAI応答を生成します。

## 機能

- **AI짱としての自己認識**: システムプロンプトにより、AI짱という名前と役割を認識
- **Discordの特定チャンネルでメッセージを監視**
- **Ollamaを使用したAI応答生成**
- **会話履歴の管理**: システムメッセージを含めた適切な履歴管理
- **Discord情報取得機能**:
  - チャンネル情報の取得
  - ユーザー情報の取得
  - メッセージ履歴の取得
  - サーバー情報の取得
- **豊富なコマンド機能**: ping, reset, status, channelinfo, userinfo, history, whoami

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
SYSTEM_PROMPT=あなたは「AI짱」という名前のDiscord botです。
あなたは親しみやすく、フレンドリーで、ユーザーとの会話を楽しむキャラクターです。
日本語で自然な会話をしてください。
必要に応じてDiscordの情報（ユーザー情報、チャンネル情報、メッセージ履歴など）を活用できます。
あなたの名前は「AI짱」です。自己紹介するときは必ずこの名前を使ってください。
```

**注意**: `SYSTEM_PROMPT`は複数行になるため、適切にエスケープするか、環境変数として設定してください。デフォルト値が設定されているため、省略することも可能です。

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
2. AI짱が自動的にメッセージを検知
3. Ollamaで応答を生成してチャンネルに送信

### AI짱について

AI짱は自己認識を持つDiscord botです:
- 自分が「AI짱」という名前であることを認識
- Discord botとしての役割を理解
- システムプロンプトによって性格や振る舞いをカスタマイズ可能
- 会話履歴を保持し、文脈を理解した応答が可能

### Discord情報取得機能

AI짱は以下のDiscord情報を活用できます:
- **チャンネル情報**: チャンネル名、ID、タイプ、所属サーバー
- **ユーザー情報**: ユーザー名、表示名、ID、アカウント作成日
- **メッセージ履歴**: 過去のメッセージを取得して文脈を理解
- **メンション情報**: メンションされたユーザーの情報を自動取得

これらの情報は、会話の中で自動的に活用されます。

### コマンド

#### 基本コマンド
- `!ping` - ボットの応答性をテスト
- `!reset` - 会話履歴をリセット（AI짱として再初期化）
- `!status` - AI짱の状態を表示
- `!whoami` - AI짱の自己紹介

#### Discord情報取得コマンド
- `!channelinfo [channel_id]` - チャンネル情報を表示（IDを省略すると現在のチャンネル）
- `!userinfo [user_id]` - ユーザー情報を表示（IDを省略すると自分の情報）
- `!history [limit]` - 最近のメッセージ履歴を表示（最大20件）

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
