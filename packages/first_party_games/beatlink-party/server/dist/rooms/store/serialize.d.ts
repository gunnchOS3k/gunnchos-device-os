import type { RoomSnapshot } from './types.js';
/** Runtime room shape RoomManager keeps (Maps/Sets + snapshot fields). */
export interface InternalRoomLive extends Omit<RoomSnapshot, 'hypeCooldowns' | 'playerTokens' | 'audienceTokens' | 'scoredTargets'> {
    hypeCooldowns: Map<string, number>;
    playerTokens: Map<string, string>;
    audienceTokens: Map<string, string>;
    scoredTargets: Set<string>;
    calibrationSamples: RoomSnapshot['calibrationSamples'];
}
export declare function serializeRoom(room: InternalRoomLive): RoomSnapshot;
export declare function deserializeRoom(snapshot: RoomSnapshot): InternalRoomLive;
//# sourceMappingURL=serialize.d.ts.map