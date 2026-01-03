"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.config = void 0;
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config();
exports.config = {
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
//# sourceMappingURL=env.js.map