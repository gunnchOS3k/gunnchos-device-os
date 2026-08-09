/** Default unit-test / single-process backend — no external deps. */
export class InMemoryRoomStore {
    backend = 'memory';
    rooms = new Map();
    has(code) {
        return this.rooms.has(code.toUpperCase());
    }
    get(code) {
        return this.rooms.get(code.toUpperCase()) ?? null;
    }
    set(code, snapshot) {
        this.rooms.set(code.toUpperCase(), snapshot);
    }
    delete(code) {
        this.rooms.delete(code.toUpperCase());
    }
    *entries() {
        yield* this.rooms.entries();
    }
}
//# sourceMappingURL=memoryStore.js.map