export { InMemoryRoomStore } from './memoryStore.js';
export { RedisRoomStore, FakeRedis, createRedisClientFromEnv, roomRedisKey, } from './redisStore.js';
export { serializeRoom, deserializeRoom, } from './serialize.js';
import { InMemoryRoomStore } from './memoryStore.js';
import { RedisRoomStore, createRedisClientFromEnv } from './redisStore.js';
/**
 * Prefer Redis when REDIS_URL is set and reachable; otherwise in-memory.
 * Unit tests should construct InMemoryRoomStore explicitly.
 */
export async function createRoomStoreFromEnv() {
    const forceMemory = process.env.BEATLINK_ROOM_STORE === 'memory';
    if (forceMemory) {
        return { store: new InMemoryRoomStore(), backend: 'memory', hydrated: 0 };
    }
    try {
        const client = await createRedisClientFromEnv();
        if (!client) {
            return { store: new InMemoryRoomStore(), backend: 'memory', hydrated: 0 };
        }
        const store = new RedisRoomStore(client);
        const hydrated = await store.hydrate();
        console.log(`[beatlink] room store=redis hydrated=${hydrated}`);
        return { store, backend: 'redis', hydrated };
    }
    catch (err) {
        console.warn('[beatlink] Redis unavailable — falling back to in-memory rooms', err);
        return { store: new InMemoryRoomStore(), backend: 'memory', hydrated: 0 };
    }
}
//# sourceMappingURL=index.js.map