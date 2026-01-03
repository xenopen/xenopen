"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.QBittorrentService = void 0;
const axios_1 = __importStar(require("axios"));
const env_1 = require("../config/env");
class QBittorrentService {
    client;
    cookie = null;
    constructor() {
        this.client = axios_1.default.create({
            baseURL: env_1.config.qbittorrent.url,
        });
    }
    async login() {
        try {
            const params = new URLSearchParams();
            params.append('username', env_1.config.qbittorrent.username);
            params.append('password', env_1.config.qbittorrent.password);
            const response = await this.client.post('/api/v2/auth/login', params, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            });
            if (response.headers['set-cookie']) {
                this.cookie = response.headers['set-cookie'][0];
                return true;
            }
            return false;
        }
        catch (error) {
            console.error('Error logging into qBittorrent:', error);
            return false;
        }
    }
    async getTorrents() {
        if (!this.cookie) {
            const loggedIn = await this.login();
            if (!loggedIn)
                return [];
        }
        try {
            const response = await this.client.get('/api/v2/torrents/info', {
                headers: {
                    Cookie: this.cookie,
                },
            });
            return response.data;
        }
        catch (error) {
            console.error('Error fetching torrents:', error);
            return [];
        }
    }
    async addTorrent(magnetLink) {
        if (!this.cookie) {
            const loggedIn = await this.login();
            if (!loggedIn)
                return false;
        }
        try {
            const params = new FormData();
            // Note: In a real implementation with axios and FormData in Node, 
            // you might need 'form-data' package or handle boundary headers manually.
            // For simplicity here, assuming simple form urlencoded might not work for file upload endpoints 
            // but often works for magnet links if the API supports it. 
            // qBittorrent /api/v2/torrents/add supports 'urls' parameter.
            const data = new URLSearchParams();
            data.append('urls', magnetLink);
            await this.client.post('/api/v2/torrents/add', data, {
                headers: {
                    Cookie: this.cookie,
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
            });
            return true;
        }
        catch (error) {
            console.error('Error adding torrent:', error);
            return false;
        }
    }
}
exports.QBittorrentService = QBittorrentService;
//# sourceMappingURL=qbittorrent.js.map