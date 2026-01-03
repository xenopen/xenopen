export declare class QBittorrentService {
    private client;
    private cookie;
    constructor();
    login(): Promise<boolean>;
    getTorrents(): Promise<any[]>;
    addTorrent(magnetLink: string): Promise<boolean>;
}
//# sourceMappingURL=qbittorrent.d.ts.map