# Discord AI Agent - Ollama統合

Mac上のOllamaを使用してDiscordチャンネルで会話するAIボットです。

## 特徴

- 🤖 Mac上のOllamaとシームレスに統合
- 💬 特定のチャンネルでメッセージを監視して自動応答
- 🎯 メンション機能で自然な会話
- 📝 豊富なコマンドセット
- ⚙️ 柔軟な設定オプション

## 前提条件

### 1. Ollamaのインストール

Mac上にOllamaをインストールする必要があります：

```bash
# Homebrewを使用してインストール
brew install ollama

# Ollamaサービスを起動
ollama serve
```

### 2. モデルのダウンロード

```bash
# 例: Llama 2をダウンロード
ollama pull llama2

# 他のモデルの例
ollama pull mistral
ollama pull codellama
ollama pull gemma
```

### 3. Python環境

Python 3.8以上が必要です。

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. Discord Botの作成

1. [Discord Developer Portal](https://discord.com/developers/applications)にアクセス
2. 「New Application」をクリックして新しいアプリケーションを作成
3. 左サイドバーから「Bot」を選択
4. 「Add Bot」をクリック
5. トークンをコピー（「Reset Token」で再生成可能）

### 3. Bot権限の設定

Discord Developer Portalで：

1. 「Bot」セクションの「Privileged Gateway Intents」で以下を有効化：
   - ✅ MESSAGE CONTENT INTENT
   - ✅ SERVER MEMBERS INTENT（オプション）
2. 「OAuth2」→「URL Generator」で以下の権限を選択：
   - **Scopes**: `bot`
   - **Bot Permissions**: 
     - Send Messages
     - Read Messages/View Channels
     - Read Message History
3. 生成されたURLでBotをサーバーに招待

### 4. 環境設定

`.env.example`を`.env`にコピーして設定：

```bash
cp .env.example .env
```

`.env`ファイルを編集：

```env
DISCORD_TOKEN=あなたのDiscordボットトークン
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=llama2
TARGET_CHANNEL_ID=123456789012345678  # オプション
BOT_PREFIX=!
```

### 5. チャンネルIDの取得（オプション）

特定のチャンネルのみで動作させたい場合：

1. Discordで「設定」→「詳細設定」→「開発者モード」を有効化
2. 監視したいチャンネルを右クリック
3. 「IDをコピー」をクリック
4. `.env`の`TARGET_CHANNEL_ID`に貼り付け

## 実行

### Ollamaサーバーの起動

別のターミナルウィンドウで：

```bash
ollama serve
```

### Botの起動

```bash
python bot.py
```

または実行権限を付与して：

```bash
chmod +x bot.py
./bot.py
```

## 使い方

### メンション機能

Botをメンションして話しかけると応答します：

```
@BotName こんにちは！今日の天気について教えて
```

### コマンド

#### `!ask` - AIに質問する

```
!ask Pythonでリストをソートする方法は？
```

#### `!chat` - チャット形式で会話

```
!chat こんにちは！元気ですか？
```

#### `!model` - 使用中のモデル情報を表示

```
!model
```

#### `!help_ai` - ヘルプを表示

```
!help_ai
```

## カスタマイズ

### システムプロンプトの変更

`bot.py`の`system_prompt`パラメータを編集して、AIの振る舞いを変更できます：

```python
system_prompt="あなたは専門的な技術アドバイザーです。プログラミングに関する質問に詳しく答えてください。"
```

### モデルの切り替え

`.env`ファイルで`OLLAMA_MODEL`を変更：

```env
OLLAMA_MODEL=mistral
```

利用可能なモデルを確認：

```bash
ollama list
```

### 応答の調整

`bot.py`の`OllamaClient`クラスで、温度やトップP値などのパラメータを調整できます。

## トラブルシューティング

### Ollamaに接続できない

```
エラー: Ollamaサーバーに接続できません。
```

**解決方法:**
1. Ollamaが起動しているか確認: `ps aux | grep ollama`
2. `ollama serve`を別のターミナルで実行
3. URLが正しいか確認: デフォルトは`http://localhost:11434`

### Discordログインエラー

```
エラー: Discordへのログインに失敗しました。
```

**解決方法:**
1. `.env`のトークンが正しいか確認
2. Discord Developer PortalでTokenを再生成

### メッセージが読めない

**解決方法:**
1. Discord Developer Portalで「MESSAGE CONTENT INTENT」が有効になっているか確認
2. Botに適切な権限があるか確認

## 高度な機能

### 会話履歴の保持

会話の文脈を保持したい場合は、データベース（SQLite、Redis等）を統合してメッセージ履歴を管理できます。

### 複数チャンネル対応

`TARGET_CHANNEL_ID`を設定せず、チャンネルごとに異なる動作をする場合は、チャンネルIDをチェックするロジックを追加します。

### 管理者コマンド

特定のユーザーのみが使用できるコマンドを追加：

```python
@bot.command(name='admin_command')
@commands.has_permissions(administrator=True)
async def admin_command(ctx):
    # 管理者専用の処理
    pass
```

## ライセンス

MITライセンス

## 貢献

プルリクエストを歓迎します！

## サポート

問題が発生した場合は、Issueを作成してください。
