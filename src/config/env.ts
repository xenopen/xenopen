import dotenv from 'dotenv';

dotenv.config();

export const config = {
  notion: {
    apiKey: process.env.NOTION_API_KEY || '',
    databaseId: process.env.NOTION_DATABASE_ID || '',
  },
  discord: {
    token: process.env.DISCORD_TOKEN || '',
    channelId: process.env.DISCORD_CHANNEL_ID || '',
  },
  qbittorrent: {
    url: process.env.QBITTORRENT_URL || 'http://localhost:8080',
    username: process.env.QBITTORRENT_USERNAME || '',
    password: process.env.QBITTORRENT_PASSWORD || '',
  },
};
