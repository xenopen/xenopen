import cron from 'node-cron';
import { NotionService } from './services/notion';
import { DiscordService } from './services/discord';
import { QBittorrentService } from './services/qbittorrent';

async function main() {
  console.log('Starting Personal App Integration Manager...');

  const notion = new NotionService();
  const discord = new DiscordService();
  const qbittorrent = new QBittorrentService();

  // 1分ごとに実行するCronジョブ
  cron.schedule('* * * * *', async () => {
    console.log('Checking for tasks...');
    
    // Notionから設定やタスクを取得
    const configs = await notion.getConfigurations();
    
    for (const config of configs) {
        if (!config.isEnabled) continue;

        console.log(`Processing config: ${config.name} (${config.type})`);

        // 例: qBittorrentの監視タスク
        if (config.name === 'Check Torrents' && config.type === 'Task') {
            const torrents = await qbittorrent.getTorrents();
            console.log(`Found ${torrents.length} active torrents.`);
            // 必要ならDiscordに通知
            if (torrents.length > 0) {
                 // await discord.sendMessage(`Current active torrents: ${torrents.length}`);
            }
        }

        // 例: 特定のメッセージをDiscordに送信するタスク
        if (config.type === 'DiscordMessage') {
             await discord.sendMessage(`Message from Notion: ${config.value}`);
        }
    }
  });

  console.log('Scheduler started. Waiting for tasks...');
}

main().catch(console.error);
