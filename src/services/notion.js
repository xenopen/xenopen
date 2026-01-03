"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.NotionService = void 0;
const client_1 = require("@notionhq/client");
const env_1 = require("../config/env");
class NotionService {
    client;
    databaseId;
    constructor() {
        this.client = new client_1.Client({ auth: env_1.config.notion.apiKey });
        this.databaseId = env_1.config.notion.databaseId;
    }
    async getConfigurations() {
        try {
            const response = await this.client.databases.query({
                database_id: this.databaseId,
                filter: {
                    property: 'Enabled',
                    checkbox: {
                        equals: true,
                    },
                },
            });
            const configs = response.results.map((page) => {
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
        }
        catch (error) {
            console.error('Error fetching configuration from Notion:', error);
            return [];
        }
    }
    async addItem(name, value, type = 'Info') {
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
        }
        catch (error) {
            console.error('Error adding item to Notion:', error);
        }
    }
}
exports.NotionService = NotionService;
//# sourceMappingURL=notion.js.map