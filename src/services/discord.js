"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DiscordService = void 0;
const discord_js_1 = require("discord.js");
const env_1 = require("../config/env");
class DiscordService {
    client;
    isReady = false;
    constructor() {
        this.client = new discord_js_1.Client({
            intents: [discord_js_1.GatewayIntentBits.Guilds, discord_js_1.GatewayIntentBits.GuildMessages],
        });
        this.client.once('ready', () => {
            console.log(`Discord bot logged in as ${this.client.user?.tag}`);
            this.isReady = true;
        });
        if (env_1.config.discord.token) {
            this.client.login(env_1.config.discord.token).catch(err => {
                console.error('Failed to login to Discord:', err);
            });
        }
        else {
            console.warn('Discord token is missing in configuration.');
        }
    }
    async sendMessage(message) {
        if (!this.isReady) {
            console.warn('Discord client is not ready yet.');
            return;
        }
        if (!env_1.config.discord.channelId) {
            console.warn('Discord channel ID is not configured.');
            return;
        }
        try {
            const channel = await this.client.channels.fetch(env_1.config.discord.channelId);
            if (channel && channel instanceof discord_js_1.TextChannel) {
                await channel.send(message);
            }
            else {
                console.error('Discord channel not found or is not a text channel.');
            }
        }
        catch (error) {
            console.error('Error sending message to Discord:', error);
        }
    }
}
exports.DiscordService = DiscordService;
//# sourceMappingURL=discord.js.map