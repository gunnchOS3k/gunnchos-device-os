import type { RoomSnapshot, RoomStore } from './types.js';
/** Default unit-test / single-process backend — no external deps. */
export declare class InMemoryRoomStore implements RoomStore {
    readonly backend: "memory";
    private rooms;
    has(code: string): boolean;
    get(code: string): RoomSnapshot | null;
    set(code: string, snapshot: RoomSnapshot): void;
    delete(code: string): void;
    entries(): IterableIterator<[string, RoomSnapshot]>;
}
//# sourceMappingURL=memoryStore.d.ts.map