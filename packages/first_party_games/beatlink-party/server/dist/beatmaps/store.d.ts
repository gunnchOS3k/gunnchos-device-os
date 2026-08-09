import type { Beatmap, SongCatalogEntry } from '@beatlink/shared';
export declare function loadCatalog(): SongCatalogEntry[];
export declare function getSongById(id: string): SongCatalogEntry | undefined;
export declare function getBeatmap(beatmapId: string): Beatmap | null;
export declare function getBeatmapForSong(songId: string): Beatmap | null;
//# sourceMappingURL=store.d.ts.map