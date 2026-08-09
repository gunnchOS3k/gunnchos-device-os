/**
 * Real Socket.IO network load — cross-process and in-process loopback.
 * Measures localhost join/influence RTT p50/p95/p99 for 8×25/50/100/300.
 */
import { type NetworkLoadReport } from '@beatlink/game-engine';
import { type EventAudienceTier } from '@beatlink/shared';
export declare function runNetworkLoadAgainstServer(baseUrl: string, options?: {
    performers?: number;
    tiers?: EventAudienceTier[];
    mode?: NetworkLoadReport['mode'];
    /** Influence samples capped for stable p99 without thrashing CI (default 24). */
    influenceSampleCap?: number;
}): Promise<NetworkLoadReport>;
/**
 * In-process HTTP+Socket.IO server on ephemeral port — still real WebSocket frames.
 * Uses a dedicated RoomManager so tests do not collide with the singleton.
 */
export declare function runInProcessSocketNetworkLoad(options?: {
    performers?: number;
    tiers?: EventAudienceTier[];
}): Promise<NetworkLoadReport>;
/**
 * Cross-process load via `tsx` child (real separate Node process + WebSocket clients).
 */
export declare function runCrossProcessNetworkLoad(options: {
    port?: number;
    performers?: number;
    tiers?: EventAudienceTier[];
    env?: Record<string, string>;
    readyTimeoutMs?: number;
}): Promise<NetworkLoadReport>;
//# sourceMappingURL=networkLoadRunner.d.ts.map