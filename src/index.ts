import { Client, GatewayIntentBits } from 'discord.js';
import { Ollama } from 'ollama';
import dotenv from 'dotenv';

dotenv.config();

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

const ollama = new Ollama({
  host: process.env.OLLAMA_HOST || 'http://127.0.0.1:11434',
});

const TOKEN = process.env.DISCORD_TOKEN;
const CHANNEL_ID = process.env.TARGET_CHANNEL_ID;
const MODEL = process.env.OLLAMA_MODEL || 'llama3';

client.once('ready', () => {
  console.log(`Logged in as ${client.user?.tag}!`);
});

client.on('messageCreate', async (message) => {
  // 自身のメッセージは無視
  if (message.author.bot) return;

  // 特定のチャンネル以外は無視
  if (message.channelId !== CHANNEL_ID) return;

  try {
    // タイピング中を表示
    await message.channel.sendTyping();

    const response = await ollama.chat({
      model: MODEL,
      messages: [{ role: 'user', content: message.content }],
    });

    await message.reply(response.message.content);
  } catch (error) {
    console.error('Error:', error);
    await message.reply('申し訳ありません。エラーが発生しました。');
  }
});

if (!TOKEN) {
    console.error("Error: DISCORD_TOKEN is not set in .env");
    process.exit(1);
}

client.login(TOKEN);
