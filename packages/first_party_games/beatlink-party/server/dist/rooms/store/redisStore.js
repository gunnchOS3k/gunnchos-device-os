/**
 * Redis durable room backend — write-through local cache + Redis snapshots.
 * Requires REDIS_URL (see docker-compose.yml). Unit tests keep InMemoryRoomStore.
 */
const KEY_PREFIX = 'beatlink:room:';
export function roomRedisKey(code) {
    return `${KEY_PREFIX}${code.toUpperCase()}`;
}
export class RedisRoomStore {
    backend = 'redis';
    cache = new Map();
    pending = new Map();
    redis;
    defaultTtlSec;
    constructor(redis, options = {}) {
        this.redis = redis;
        this.defaultTtlSec = options.defaultTtlSec ?? 2 * 60 * 60;
    }
    has(code) {
        return this.cache.has(code.toUpperCase());
    }
    get(code) {
        return this.cache.get(code.toUpperCase()) ?? null;
    }
    set(code, snapshot) {
        const key = code.toUpperCase();
        this.cache.set(key, snapshot);
        const ttl = Math.max(1, Math.ceil((snapshot.expiresAt - Date.now()) / 1000) || this.defaultTtlSec);
        const write = this.redis
            .set(roomRedisKey(key), JSON.stringify(snapshot), 'EX', ttl)
            .catch((err) => {
            console.error('[beatlink] redis room save failed', key, err);
        });
        this.pending.set(key, write);
    }
    delete(code) {
        const key = code.toUpperCase();
        this.cache.delete(key);
        const write = this.redis.del(roomRedisKey(key)).catch((err) => {
            console.error('[beatlink] redis room delete failed', key, err);
        });
        this.pending.set(key, write);
    }
    *entries() {
        yield* this.cache.entries();
    }
    async hydrate() {
        const keys = await this.redis.keys(`${KEY_PREFIX}*`);
        let loaded = 0;
        for (const key of keys) {
            const raw = await this.redis.get(key);
            if (!raw)
                continue;
            try {
                const snapshot = JSON.parse(raw);
                if (!snapshot?.code)
                    continue;
                if (Date.now() > snapshot.expiresAt) {
                    await this.redis.del(key);
                    continue;
                }
                this.cache.set(snapshot.code.toUpperCase(), snapshot);
                loaded += 1;
            }
            catch {
                // skip corrupt
            }
        }
        return loaded;
    }
    async flush() {
        await Promise.all([...this.pending.values()]);
        this.pending.clear();
    }
    async close() {
        await this.flush();
        await this.redis.quit();
    }
}
/** Create Redis client when REDIS_URL is set; returns null otherwise. */
export async function createRedisClientFromEnv() {
    const url = process.env.REDIS_URL?.trim();
    if (!url)
        return null;
    const mod = (await import('ioredis'));
    const client = new mod.default(url, {
        maxRetriesPerRequest: 2,
        enableReadyCheck: true,
        lazyConnect: true,
        retryStrategy: () => null,
    });
    // Prevent unhandled 'error' crash when daemon is down during probes.
    client.on('error', () => {
        /* swallowed — callers handle connect failures */
    });
    try {
        await client.connect();
        if (client.status !== 'ready') {
            await new Promise((resolve, reject) => {
                const onReady = () => {
                    cleanup();
                    resolve();
                };
                const onError = (err) => {
                    cleanup();
                    reject(err);
                };
                const cleanup = () => {
                    client.off('ready', onReady);
                    client.off('error', onError);
                };
                client.on('ready', onReady);
                client.on('error', onError);
            });
        }
        return client;
    }
    catch (err) {
        try {
            client.disconnect();
        }
        catch {
            // ignore
        }
        throw err;
    }
}
/** In-process fake Redis for unit tests of the Redis adapter (no daemon). */
export class FakeRedis {
    data = new Map();
    async get(key) {
        const row = this.data.get(key);
        if (!row)
            return null;
        if (row.expiresAt != null && Date.now() > row.expiresAt) {
            this.data.delete(key);
            return null;
        }
        return row.value;
    }
    async set(key, value, ...args) {
        let expiresAt;
        for (let i = 0; i < args.length; i++) {
            if (String(args[i]).toUpperCase() === 'EX' && typeof args[i + 1] === 'number') {
                expiresAt = Date.now() + args[i + 1] * 1000;
            }
        }
        this.data.set(key, { value, expiresAt });
        return 'OK';
    }
    async del(key) {
        return this.data.delete(key) ? 1 : 0;
    }
    async keys(pattern) {
        const prefix = pattern.replace(/\*$/, '');
        return [...this.data.keys()].filter((k) => k.startsWith(prefix));
    }
    async quit() {
        this.data.clear();
        return 'OK';
    }
}
//# sourceMappingURL=redisStore.js.map