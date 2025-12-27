# Discord AI Agent (Mac + Ollama)

Mac上で動作するOllamaを利用したDiscord AI Agentです。
特定のチャンネルでの会話を聞き、日本語で応答します。

## 前提条件

*   Node.js (v18以上推奨)
*   [Ollama](https://ollama.com/) がMacにインストールされ、起動していること
*   Discord Bot Token取得済みであること

## セットアップ

1.  依存関係のインストール:
    ```bash
    npm install
    ```

2.  環境設定:
    `.env` ファイルを作成し、以下の内容を設定してください。
    
    ```env
    # Discord Developer Portalから取得したBot Token
    DISCORD_TOKEN=your_discord_bot_token_here
    
    # AIに応答させたいチャンネルのID
    TARGET_CHANNEL_ID=your_target_channel_id_here
    
    # Ollamaの設定 (通常はそのままでOK)
    OLLAMA_HOST=http://127.0.0.1:11434
    OLLAMA_MODEL=llama3
    ```

3.  Ollamaモデルの準備:
    使用するモデル（例: llama3）をpullしておいてください。
    ```bash
    ollama pull llama3
    ```

## 起動方法

### 開発モード
```bash
npm run dev
```

### ビルドして実行
```bash
npm run build
npm start
```

## 注意事項

*   Ollamaがバックグラウンドで起動している必要があります。
*   Mac上での動作を想定しています。
