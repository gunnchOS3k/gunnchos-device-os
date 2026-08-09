/**
 * Redis durable room backend — write-through local cache + Redis snapshots.
 * Requires REDIS_URL (see docker-compose.yml). Unit tests keep InMemoryRoomStore.
 */
import type { RoomSnapshot, RoomStore } from './types.js';
export interface RedisLike {
    get(key: string): Promise<string | null>;
    set(key: string, value: string, ...args: unknown[]): Promise<unknown>;
    del(key: string): Promise<unknown>;
    keys(pattern: string): Promise<string[]>;
    quit(): Promise<unknown>;
}
export declare function roomRedisKey(code: string): string;
export declare class RedisRoomStore implements RoomStore {
    readonly backend: "redis";
    private cache;
    private pending;
    private redis;
    private defaultTtlSec;
    constructor(redis: RedisLike, options?: {
        defaultTtlSec?: number;
    });
    has(code: string): boolean;
    get(code: string): RoomSnapshot | null;
    set(code: string, snapshot: RoomSnapshot): void;
    delete(code: string): void;
    entries(): IterableIterator<[string, RoomSnapshot]>;
    hydrate(): Promise<number>;
    flush(): Promise<void>;
    close(): Promise<void>;
}
/** Create Redis client when REDIS_URL is set; returns null otherwise. */
export declare function createRedisClientFromEnv(): Promise<RedisLike | null>;
/** In-process fake Redis for unit tests of the Redis adapter (no daemon). */
export declare class FakeRedis implements RedisLike {
    private data;
    get(key: string): Promise<string | null>;
    set(key: string, value: string, ...args: unknown[]): Promise<'OK'>;
    del(key: string): Promise<number>;
    keys(pattern: string): Promise<string[]>;
    quit(): Promise<'OK'>;
}
//# sourceMappingURL=redisStore.d.ts.map