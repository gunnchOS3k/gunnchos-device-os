export type { RoomSnapshot, RoomStore, RoomStoreBackend } from './types.js';
export { InMemoryRoomStore } from './memoryStore.js';
export { RedisRoomStore, FakeRedis, createRedisClientFromEnv, roomRedisKey, type RedisLike, } from './redisStore.js';
export { serializeRoom, deserializeRoom, type InternalRoomLive, } from './serialize.js';
import type { RoomStore } from './types.js';
export interface CreateRoomStoreResult {
    store: RoomStore;
    backend: 'memory' | 'redis';
    hydrated: number;
}
/**
 * Prefer Redis when REDIS_URL is set and reachable; otherwise in-memory.
 * Unit tests should construct InMemoryRoomStore explicitly.
 */
export declare function createRoomStoreFromEnv(): Promise<CreateRoomStoreResult>;
//# sourceMappingURL=index.d.ts.map