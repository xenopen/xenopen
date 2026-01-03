import { Client } from '@notionhq/client';
import { config } from '../config/env';

export interface NotionConfigItem {
  id: string;
  name: string;
  value: string;
  isEnabled: boolean;
  type: string;
}

export class NotionService {
  private client: Client;
  private databaseId: string;

  constructor() {
    this.client = new Client({ auth: config.notion.apiKey });
    this.databaseId = config.notion.databaseId;
  }

  async getConfigurations(): Promise<NotionConfigItem[]> {
    try {
      const response = await (this.client.databases as any).query({
        database_id: this.databaseId,
        filter: {
          property: 'Enabled',
          checkbox: {
            equals: true,
          },
        },
      });

      const configs: NotionConfigItem[] = response.results.map((page: any) => {
        const properties = page.properties;
        return {
          id: page.id,
          name: properties.Name?.title[0]?.plain_text || 'Untitled',
          value: properties.Value?.rich_text[0]?.plain_text || '',
          isEnabled: properties.Enabled?.checkbox || false,
          type: properties.Type?.select?.name || 'Unknown',
        };
      });

      return configs;
    } catch (error) {
      console.error('Error fetching configuration from Notion:', error);
      return [];
    }
  }

  async addItem(name: string, value: string, type: string = 'Info') {
    try {
      await this.client.pages.create({
        parent: { database_id: this.databaseId },
        properties: {
          Name: {
            title: [
              {
                text: {
                  content: name,
                },
              },
            ],
          },
          Value: {
            rich_text: [
              {
                text: {
                  content: value,
                },
              },
            ],
          },
          Type: {
            select: {
              name: type,
            },
          },
          Enabled: {
            checkbox: true,
          },
        },
      });
      console.log(`Added item to Notion: ${name}`);
    } catch (error) {
      console.error('Error adding item to Notion:', error);
    }
  }
}
