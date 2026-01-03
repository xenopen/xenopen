import { Client, GatewayIntentBits, TextChannel } from 'discord.js';
import { config } from '../config/env';

export class DiscordService {
  private client: Client;
  private isReady: boolean = false;

  constructor() {
    this.client = new Client({
      intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages],
    });

    this.client.once('ready', () => {
      console.log(`Discord bot logged in as ${this.client.user?.tag}`);
      this.isReady = true;
    });

    if (config.discord.token) {
        this.client.login(config.discord.token).catch(err => {
            console.error('Failed to login to Discord:', err);
        });
    } else {
        console.warn('Discord token is missing in configuration.');
    }
  }

  async sendMessage(message: string): Promise<void> {
    if (!this.isReady) {
      console.warn('Discord client is not ready yet.');
      return;
    }

    if (!config.discord.channelId) {
        console.warn('Discord channel ID is not configured.');
        return;
    }

    try {
      const channel = await this.client.channels.fetch(config.discord.channelId);
      if (channel && channel instanceof TextChannel) {
        await channel.send(message);
      } else {
        console.error('Discord channel not found or is not a text channel.');
      }
    } catch (error) {
      console.error('Error sending message to Discord:', error);
    }
  }
}
