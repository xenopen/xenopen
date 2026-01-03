# Personal App Integration Manager

個人的に使用するアプリケーション (Notion, qBittorrent, Discordなど) を連携し、自動化するためのツールです。
設定やタスク管理はNotionデータベースを通じて行います。

## 機能

- **Notion連携**: 設定値やタスクの管理をNotionデータベースで行います。
- **qBittorrent連携**: アクティブなトレントの監視などが可能です。
- **Discord連携**: 通知やメッセージ送信を行います。
- **自動実行**: 定期的にNotionを確認し、タスクを実行します。

## 前提条件

- Node.js (v18以上推奨)
- Notion アカウントとインテグレーション設定
- Discord Bot Token (通知を受け取る場合)
- qBittorrent WebUI (有効化されている場合)

## セットアップ

1. **リポジトリのクローンと依存関係のインストール**

   ```bash
   npm install
   ```

2. **環境変数の設定**

   `.env.example` をコピーして `.env` を作成し、必要な情報を入力します。

   ```bash
   cp .env.example .env
   ```

   - `NOTION_API_KEY`: Notionインテグレーションのシークレットキー
   - `NOTION_DATABASE_ID`: 設定用データベースのID
   - `DISCORD_TOKEN`: Discord Botのトークン
   - `DISCORD_CHANNEL_ID`: 通知を送るチャンネルID
   - `QBITTORRENT_URL`: WebUIのURL (例: http://localhost:8080)

3. **Notionデータベースの準備**

   Notionで新しいデータベースを作成し、以下のプロパティを追加してください。

   | プロパティ名 | 種類 (Type) | 説明 |
   | --- | --- | --- |
   | **Name** | Title | 設定項目名やタスク名 |
   | **Value** | Text | 設定値やメッセージ内容 |
   | **Enabled** | Checkbox | 有効/無効の切り替え |
   | **Type** | Select | `Config`, `Task`, `DiscordMessage` などの種別 |

   ※ 作成したデータベースに、作成したNotionインテグレーションコネクトを追加することを忘れないでください。

4. **実行**

   開発モードで実行:
   ```bash
   npm run dev
   ```

   ビルドして実行:
   ```bash
   npm run build
   npm start
   ```

## 対応アプリケーション状況

- ✅ **Notion**: 設定・データソースとして完全対応
- ✅ **Discord**: 通知送信に対応
- ✅ **qBittorrent**: ログイン・一覧取得に対応
- ⚠️ **Apple Calendar**: 現在API制限により未実装 (将来的にiCal連携などで対応検討)
- ⚠️ **Notion Calendar**: Notionデータベース経由で管理可能

## カスタマイズ

`src/index.ts` 内のロジックを編集することで、特定の `Type` や `Name` に応じた処理を追加できます。
