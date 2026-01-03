export interface NotionConfigItem {
    id: string;
    name: string;
    value: string;
    isEnabled: boolean;
    type: string;
}
export declare class NotionService {
    private client;
    private databaseId;
    constructor();
    getConfigurations(): Promise<NotionConfigItem[]>;
    addItem(name: string, value: string, type?: string): Promise<void>;
}
//# sourceMappingURL=notion.d.ts.map