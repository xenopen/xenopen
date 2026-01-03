import axios, { AxiosInstance } from 'axios';
import { config } from '../config/env';

export class QBittorrentService {
  private client: AxiosInstance;
  private cookie: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: config.qbittorrent.url,
    });
  }

  async login(): Promise<boolean> {
    try {
      const params = new URLSearchParams();
      params.append('username', config.qbittorrent.username);
      params.append('password', config.qbittorrent.password);

      const response = await this.client.post('/api/v2/auth/login', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      if (response.headers['set-cookie']) {
        this.cookie = response.headers['set-cookie'][0] || null;
        return !!this.cookie;
      }
      return false;
    } catch (error) {
      console.error('Error logging into qBittorrent:', error);
      return false;
    }
  }

  async getTorrents(): Promise<any[]> {
    if (!this.cookie) {
      const loggedIn = await this.login();
      if (!loggedIn) return [];
    }

    try {
      const response = await this.client.get('/api/v2/torrents/info', {
        headers: {
          Cookie: this.cookie,
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching torrents:', error);
      return [];
    }
  }

  async addTorrent(magnetLink: string): Promise<boolean> {
    if (!this.cookie) {
        const loggedIn = await this.login();
        if (!loggedIn) return false;
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
    } catch (error) {
        console.error('Error adding torrent:', error);
        return false;
    }
  }
}
