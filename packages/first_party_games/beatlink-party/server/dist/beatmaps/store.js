import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateBeatmap } from '@beatlink/shared';
import { createDemoBeatmap } from './generator.js';
const __dirname = dirname(fileURLToPath(import.meta.url));
const contentRoot = join(__dirname, '../../../../content');
let catalog = [];
const beatmapCache = new Map();
export function loadCatalog() {
    if (catalog.length === 0) {
        const demoRaw = readFileSync(join(contentRoot, 'songs/approved-demo-catalog.json'), 'utf-8');
        const demo = JSON.parse(demoRaw);
        let launch = [];
        try {
            const launchRaw = readFileSync(join(contentRoot, 'songs/offline-launch-catalog.json'), 'utf-8');
            launch = JSON.parse(launchRaw).songs ?? [];
        }
        catch {
            launch = [];
        }
        const byId = new Map();
        for (const song of [...demo.songs, ...launch]) {
            byId.set(song.id, song);
        }
        catalog = [...byId.values()];
    }
    return catalog;
}
export function getSongById(id) {
    return loadCatalog().find((s) => s.id === id);
}
export function getBeatmap(beatmapId) {
    if (beatmapCache.has(beatmapId)) {
        return beatmapCache.get(beatmapId);
    }
    const song = loadCatalog().find((s) => s.beatmapId === beatmapId);
    if (!song)
        return null;
    try {
        const raw = readFileSync(join(contentRoot, `beatmaps/${beatmapId}.json`), 'utf-8');
        const parsed = JSON.parse(raw);
        const validation = validateBeatmap(parsed);
        if (validation.success && validation.data) {
            beatmapCache.set(beatmapId, validation.data);
            return validation.data;
        }
    }
    catch {
        // fall through to generated
    }
    const generated = createDemoBeatmap(beatmapId, song.id, song.bpm, song.durationMs);
    beatmapCache.set(beatmapId, generated);
    return generated;
}
export function getBeatmapForSong(songId) {
    const song = getSongById(songId);
    if (!song)
        return null;
    return getBeatmap(song.beatmapId);
}
//# sourceMappingURL=store.js.map