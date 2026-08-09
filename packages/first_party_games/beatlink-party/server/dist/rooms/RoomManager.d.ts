import type { AudienceInfluenceEvent, AudienceInfluenceType, AudienceMember, Beatmap, DifficultyId, GameModeId, GameResults, LinkResolveResult, Player, PlayerInputEvent, RoomPhase, RoomPrivacySettings, RoomState, ScoreEvent, TeamId } from '@beatlink/shared';
import { comboFromStreak, type CapacityProfile } from '@beatlink/shared';
import { type CalibrationSample } from '@beatlink/game-engine';
import { type RoomStore } from './store/index.js';
interface InternalRoom extends RoomState {
    beatmap: Beatmap | null;
    hypeCooldowns: Map<string, number>;
    hostToken: string;
    playerTokens: Map<string, string>;
    audienceTokens: Map<string, string>;
    scoredTargets: Set<string>;
    /** Public web origin used when minting join QR payloads. */
    publicOrigin: string;
    calibrationSamples: CalibrationSample[];
}
export declare class RoomManager {
    /** Live in-process room objects (Maps/Sets). Snapshots sync to `store`. */
    private rooms;
    private store;
    private playerToRoom;
    private audienceToRoom;
    private socketToPlayer;
    private socketToAudience;
    private socketToHostRoom;
    constructor(store?: RoomStore);
    getStoreBackend(): RoomStore['backend'];
    /** Swap durable backend (e.g. Redis hydrate at process boot). Keeps live socket maps. */
    replaceStore(store: RoomStore): void;
    /** Persist durable snapshot after in-place mutation. */
    private commit;
    private publish;
    private dropRoom;
    createRoom(hostSocketId: string, options?: {
        publicOrigin?: string;
        gameMode?: GameModeId;
        difficulty?: DifficultyId;
        privacy?: Partial<RoomPrivacySettings>;
        /** `event_sim` raises soft audience ceiling for Beta in-process simulation. */
        capacityProfile?: CapacityProfile;
    }): RoomState & {
        hostToken: string;
    };
    getRoom(code: string): InternalRoom | null;
    stripInternal(room: InternalRoom): RoomState;
    getHostToken(code: string, socketId: string): string | null;
    /** Validate host token and re-bind host socket (reconnect / migration claim). */
    authorizeHost(code: string, socketId: string, hostToken: string | undefined): boolean;
    ownsPlayer(code: string, socketId: string, playerId: string): boolean;
    ownsAudience(code: string, socketId: string, audienceId: string): boolean;
    joinRoom(code: string, socketId: string, name: string): {
        room: RoomState;
        player: Player;
        playerToken: string;
    } | null;
    joinAudience(code: string, socketId: string, name: string): {
        room: RoomState;
        audience: AudienceMember;
        audienceToken: string;
    } | null;
    reconnectPlayer(code: string, playerId: string, playerToken: string, socketId: string): Player | null;
    reconnectAudience(code: string, audienceId: string, audienceToken: string, socketId: string): AudienceMember | null;
    reconnectHost(code: string, hostToken: string, socketId: string): RoomState | null;
    /**
     * When the host socket disconnects, migrate host seat to the first connected player
     * (or keep hostId null until host reconnects with token). Returns new host player id if migrated.
     */
    migrateHostOnDisconnect(socketId: string): {
        room: RoomState;
        previousHostId: string | null;
        newHostPlayerId: string | null;
        hostToken: string;
    } | null;
    claimHostAsPlayer(code: string, playerId: string, playerToken: string, socketId: string): {
        room: RoomState;
        hostToken: string;
    } | null;
    setAudienceMuted(code: string, audienceId: string, muted: boolean): RoomState | null;
    setAudienceSandboxed(code: string, audienceId: string, sandboxed: boolean): RoomState | null;
    /** Assign player to team A / B / solo (lobby / results / song_select). */
    setPlayerTeam(code: string, playerId: string, teamId: TeamId | string): RoomState | null;
    /** Auto-split connected players into A/B. */
    autoAssignTeams(code: string): RoomState | null;
    updatePrivacy(code: string, patch: Partial<RoomPrivacySettings>): RoomState | null;
    /** Test / harness hook — force phase without full transition checks. */
    forcePhase(code: string, phase: RoomPhase): RoomState | null;
    /**
     * Moderated audience influence with anti-grief rate limits.
     * Sandboxed members get accepted=false (no crowd effect).
     */
    processAudienceInfluence(code: string, audienceId: string, type: AudienceInfluenceType, choice?: string): {
        room: RoomState;
        event: AudienceInfluenceEvent;
    } | null;
    leaveRoom(socketId: string): RoomState | null;
    endRoom(code: string, hostSocketId: string): RoomState | null;
    /**
     * Clean shutdown — clears seats, tokens, maps, and marks phase closed.
     * Accepts host token or matching host socket id.
     */
    shutdownRoom(code: string, options?: {
        reason?: string;
        hostSocketId?: string;
        hostToken?: string;
    }): RoomState | null;
    /** Purge expired rooms (TTL). Returns number removed. */
    purgeExpiredRooms(nowMs?: number): string[];
    /** Refresh join QR payload (same code, updated expiry / origin). */
    refreshJoinQr(code: string, publicOrigin?: string): RoomState | null;
    setGameMode(code: string, gameMode: GameModeId | string): RoomState | null;
    setDifficulty(code: string, difficulty: DifficultyId): RoomState | null;
    setRole(code: string, playerId: string, role: Player['role']): RoomState | null;
    setReady(code: string, playerId: string, ready: boolean): RoomState | null;
    selectSong(code: string, songId: string): RoomState | null;
    /** Persist pasted link + resolve snapshot so peers can see preview/eligibility. */
    setResolvedLink(code: string, url: string, result: LinkResolveResult): RoomState | null;
    startCalibration(code: string): RoomState | null;
    /** Record a single calibration tap sample (expected vs tapped). */
    recordCalibrationSample(code: string, sample: CalibrationSample): RoomState | null;
    submitCalibration(code: string, offsetMs?: number): RoomState | null;
    startCountdown(code: string): RoomState | null;
    tickCountdown(code: string): RoomState | null;
    getGameTimeMs(code: string): number;
    getCalibratedGameTimeMs(code: string): number;
    processInput(code: string, input: PlayerInputEvent): {
        room: RoomState;
        scoreEvent: ScoreEvent | null;
    } | null;
    endGame(code: string): GameResults | null;
    /** Rematch: keep seats/tokens, clear scores, return to lobby for next song. */
    rematch(code: string): RoomState | null;
    /** Alias for rematch — host "Next song" control. */
    nextRound(code: string): RoomState | null;
    /** @deprecated Prefer rematch() — keeps seats; still supported for host UI. */
    replay(code: string): RoomState | null;
    getBeatmap(code: string): Beatmap | null;
    getPlayerIdForSocket(socketId: string): string | undefined;
    getAudienceIdForSocket(socketId: string): string | undefined;
    resetToLobby(code: string, phase?: RoomPhase): RoomState | null;
}
export declare const roomManager: RoomManager;
export { comboFromStreak };
//# sourceMappingURL=RoomManager.d.ts.map