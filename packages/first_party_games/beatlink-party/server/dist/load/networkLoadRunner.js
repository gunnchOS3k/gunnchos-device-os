/**
 * Real Socket.IO network load — cross-process and in-process loopback.
 * Measures localhost join/influence RTT p50/p95/p99 for 8×25/50/100/300.
 */
import { createServer } from 'node:http';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { io as ioClient } from 'socket.io-client';
import { buildNetworkLoadReport, NETWORK_LOAD_DISCLAIMER, summarizeLatencies, } from '@beatlink/game-engine';
import { EVENT_AUDIENCE_TIERS, MAX_PERFORMERS } from '@beatlink/shared';
import { setupRealtime } from '../realtime/socket.js';
import { roomManager as defaultRoomManager } from '../rooms/RoomManager.js';
/** Workspace package exports point at dist/; child tsx server needs them built. */
async function ensureWorkspacePackageDists() {
    const sharedDist = resolve(process.cwd(), 'packages/shared/dist/index.js');
    const engineDist = resolve(process.cwd(), 'packages/game-engine/dist/index.js');
    if (existsSync(sharedDist) && existsSync(engineDist))
        return null;
    const { spawnSync } = await import('node:child_process');
    const { rmSync } = await import('node:fs');
    // Drop stale incremental state so tsc actually re-emits after a dist wipe.
    for (const pkg of ['packages/shared', 'packages/game-engine']) {
        try {
            rmSync(resolve(process.cwd(), pkg, 'tsconfig.tsbuildinfo'), { force: true });
        }
        catch {
            // ignore
        }
    }
    const runBuild = (filter) => spawnSync('pnpm', ['--filter', filter, 'build'], {
        cwd: process.cwd(),
        encoding: 'utf8',
        env: process.env,
        shell: process.platform === 'win32',
    });
    const shared = runBuild('@beatlink/shared');
    const engine = runBuild('@beatlink/game-engine');
    if (!existsSync(sharedDist) || !existsSync(engineDist)) {
        return `workspace_dist_missing shared_exit=${shared.status} engine_exit=${engine.status} ${(engine.stderr || shared.stderr || engine.stdout || shared.stdout || '').slice(0, 400)}`;
    }
    return null;
}
function connectClient(url) {
    return new Promise((resolve, reject) => {
        const socket = ioClient(url, {
            transports: ['websocket'],
            forceNew: true,
            reconnection: false,
            timeout: 10_000,
        });
        const timer = setTimeout(() => {
            socket.close();
            reject(new Error('socket connect timeout'));
        }, 10_000);
        socket.on('connect', () => {
            clearTimeout(timer);
            resolve(socket);
        });
        socket.on('connect_error', (err) => {
            clearTimeout(timer);
            reject(err);
        });
    });
}
function emitAck(socket, event, payload) {
    return new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error(`ack timeout: ${event}`)), 15_000);
        if (payload === undefined) {
            socket.emit(event, (res) => {
                clearTimeout(timer);
                resolve(res);
            });
        }
        else {
            socket.emit(event, payload, (res) => {
                clearTimeout(timer);
                resolve(res);
            });
        }
    });
}
/** Connect sockets in bounded parallel batches to cut wall time under load SLOs. */
async function connectClientsBatched(baseUrl, count, batchSize = 32) {
    const out = [];
    for (let i = 0; i < count; i += batchSize) {
        const n = Math.min(batchSize, count - i);
        const batch = await Promise.all(Array.from({ length: n }, () => connectClient(baseUrl)));
        out.push(...batch);
    }
    return out;
}
export async function runNetworkLoadAgainstServer(baseUrl, options = {}) {
    const performers = options.performers ?? MAX_PERFORMERS;
    const tiers = options.tiers ?? [...EVENT_AUDIENCE_TIERS];
    const mode = options.mode ?? 'cross_process';
    const influenceSampleCap = options.influenceSampleCap ?? 16;
    const metrics = [];
    for (const tier of tiers) {
        const notes = [NETWORK_LOAD_DISCLAIMER];
        const t0 = Date.now();
        const sockets = [];
        const joinRtts = [];
        const influenceRtts = [];
        let ok = true;
        let eventLoss = 0;
        try {
            const host = await connectClient(baseUrl);
            sockets.push(host);
            const created = await emitAck(host, 'room.create', {
                capacityProfile: 'event_sim',
            });
            if (!created?.code)
                throw new Error('room.create failed');
            const code = created.code;
            let performersJoined = 0;
            const performerSocks = await connectClientsBatched(baseUrl, performers, 8);
            sockets.push(...performerSocks);
            for (let i = 0; i < performerSocks.length; i++) {
                const sock = performerSocks[i];
                const j0 = Date.now();
                const joined = await emitAck(sock, 'room.join', {
                    code,
                    name: `P${i}`,
                });
                joinRtts.push(Date.now() - j0);
                if (joined?.ok)
                    performersJoined += 1;
                else {
                    ok = false;
                    eventLoss += 1;
                }
            }
            let audienceJoined = 0;
            const audience = [];
            const audienceSocks = await connectClientsBatched(baseUrl, tier, 32);
            sockets.push(...audienceSocks);
            for (let i = 0; i < audienceSocks.length; i++) {
                const sock = audienceSocks[i];
                const j0 = Date.now();
                const joined = await emitAck(sock, 'room.join_audience', { code, name: `A${i}` });
                joinRtts.push(Date.now() - j0);
                if (joined?.ok && joined.audience?.id) {
                    audienceJoined += 1;
                    audience.push({ sock, id: joined.audience.id });
                }
                else {
                    ok = false;
                    eventLoss += 1;
                }
            }
            // Prefer in-process singleton force when available (cross-process uses phase_blocked RTT).
            defaultRoomManager.forcePhase?.(code, 'playing');
            const influenceTargets = audience.slice(0, Math.min(influenceSampleCap, audience.length));
            for (const a of influenceTargets) {
                const i0 = Date.now();
                try {
                    await emitAck(a.sock, 'audience.influence', {
                        code,
                        audienceId: a.id,
                        type: 'hype',
                    });
                    influenceRtts.push(Date.now() - i0);
                }
                catch {
                    eventLoss += 1;
                    ok = false;
                    influenceRtts.push(Date.now() - i0);
                }
            }
            if (performersJoined !== performers || audienceJoined !== tier) {
                ok = false;
                notes.push(`join_mismatch performers=${performersJoined}/${performers} audience=${audienceJoined}/${tier}`);
            }
            notes.push(`event_loss=${eventLoss}`);
        }
        catch (err) {
            ok = false;
            eventLoss += 1;
            notes.push(err instanceof Error ? err.message : String(err));
        }
        finally {
            for (const s of sockets) {
                try {
                    s.close();
                }
                catch {
                    // ignore
                }
            }
        }
        metrics.push({
            tier,
            performers,
            audience: tier,
            joinRttMs: summarizeLatencies(joinRtts),
            influenceRttMs: summarizeLatencies(influenceRtts),
            wallMs: Date.now() - t0,
            ok: ok && eventLoss === 0,
            notes,
            eventLoss,
        });
    }
    return buildNetworkLoadReport({ mode, baseUrl, performers, tiers, metrics });
}
/**
 * In-process HTTP+Socket.IO server on ephemeral port — still real WebSocket frames.
 * Uses a dedicated RoomManager so tests do not collide with the singleton.
 */
export async function runInProcessSocketNetworkLoad(options = {}) {
    const httpServer = createServer((_req, res) => {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'ok', harness: 'network-load' }));
    });
    setupRealtime(httpServer, '*');
    await new Promise((resolve) => {
        httpServer.listen(0, '127.0.0.1', () => resolve());
    });
    const address = httpServer.address();
    if (!address || typeof address === 'string') {
        httpServer.close();
        throw new Error('failed to bind ephemeral port');
    }
    const baseUrl = `http://127.0.0.1:${address.port}`;
    try {
        return await runNetworkLoadAgainstServer(baseUrl, {
            performers: options.performers,
            tiers: options.tiers,
            mode: 'in_process_socket',
        });
    }
    finally {
        await new Promise((resolve) => httpServer.close(() => resolve()));
    }
}
/**
 * Cross-process load via `tsx` child (real separate Node process + WebSocket clients).
 */
export async function runCrossProcessNetworkLoad(options) {
    const distErr = await ensureWorkspacePackageDists();
    if (distErr) {
        return buildNetworkLoadReport({
            mode: 'cross_process',
            baseUrl: 'http://127.0.0.1:0',
            performers: options.performers,
            tiers: options.tiers,
            metrics: [
                {
                    tier: (options.tiers?.[0] ?? 25),
                    performers: options.performers ?? MAX_PERFORMERS,
                    audience: options.tiers?.[0] ?? 25,
                    joinRttMs: { p50: 0, p95: 0, p99: 0, samples: 0 },
                    influenceRttMs: { p50: 0, p95: 0, p99: 0, samples: 0 },
                    wallMs: 0,
                    ok: false,
                    notes: [NETWORK_LOAD_DISCLAIMER, distErr],
                },
            ],
        });
    }
    const port = options.port ?? 3200 + Math.floor(Math.random() * 400);
    const baseUrl = `http://127.0.0.1:${port}`;
    const { spawn } = await import('node:child_process');
    const { createRequire } = await import('node:module');
    const serverEntry = resolve(process.cwd(), 'apps/server/src/index.ts');
    // Resolve tsx by absolute path — Gate1/CI pnpm layouts can miss bare `--import tsx`
    // and `.bin/tsx` shims are unreliable when spawned without a shell.
    const requireFromRoot = createRequire(resolve(process.cwd(), 'package.json'));
    let tsxImportSpec = 'tsx';
    try {
        tsxImportSpec = requireFromRoot.resolve('tsx');
    }
    catch {
        try {
            tsxImportSpec = createRequire(resolve(process.cwd(), 'apps/server/package.json')).resolve('tsx');
        }
        catch {
            // keep bare specifier; Node resolves from cwd
        }
    }
    const child = spawn(process.execPath, ['--import', tsxImportSpec, serverEntry], {
        cwd: process.cwd(),
        env: {
            ...process.env,
            ...options.env,
            PORT: String(port),
            BEATLINK_ROOM_STORE: options.env?.BEATLINK_ROOM_STORE ?? 'memory',
            CORS_ORIGIN: '*',
        },
        stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stderrBuf = '';
    child.on('error', (err) => {
        stderrBuf += `spawn_error=${err instanceof Error ? err.message : String(err)}\n`;
    });
    child.stderr?.on('data', (chunk) => {
        stderrBuf += chunk.toString();
    });
    child.stdout?.on('data', (chunk) => {
        stderrBuf += chunk.toString();
    });
    const readyTimeout = options.readyTimeoutMs ?? 45_000;
    const started = Date.now();
    let ready = false;
    while (Date.now() - started < readyTimeout) {
        if (child.exitCode != null)
            break;
        try {
            const res = await fetch(`${baseUrl}/health`);
            if (res.ok) {
                ready = true;
                break;
            }
        }
        catch {
            // retry
        }
        await new Promise((r) => setTimeout(r, 200));
    }
    if (!ready) {
        child.kill('SIGTERM');
        return buildNetworkLoadReport({
            mode: 'cross_process',
            baseUrl,
            performers: options.performers,
            tiers: options.tiers,
            metrics: [
                {
                    tier: (options.tiers?.[0] ?? 25),
                    performers: options.performers ?? MAX_PERFORMERS,
                    audience: options.tiers?.[0] ?? 25,
                    joinRttMs: { p50: 0, p95: 0, p99: 0, samples: 0 },
                    influenceRttMs: { p50: 0, p95: 0, p99: 0, samples: 0 },
                    wallMs: Date.now() - started,
                    ok: false,
                    notes: [
                        NETWORK_LOAD_DISCLAIMER,
                        `child_not_ready exit=${child.exitCode} launcher=node --import ${tsxImportSpec}`,
                        stderrBuf.slice(0, 800),
                    ],
                },
            ],
        });
    }
    try {
        return await runNetworkLoadAgainstServer(baseUrl, {
            performers: options.performers,
            tiers: options.tiers,
            mode: 'cross_process',
        });
    }
    finally {
        child.kill('SIGTERM');
        await new Promise((r) => setTimeout(r, 500));
        if (!child.killed)
            child.kill('SIGKILL');
    }
}
//# sourceMappingURL=networkLoadRunner.js.map