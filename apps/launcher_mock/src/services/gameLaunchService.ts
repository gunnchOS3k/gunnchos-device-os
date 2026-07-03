export type GameLaunchType = 'web_build' | 'local_executable_placeholder' | 'native_future' | 'unavailable'

export type GameReadiness =
  | 'playable_web_build'
  | 'design_stub'
  | 'not_connected'
  | 'native_build_pending'

export interface GameLaunchChecklist {
  buildPath: string
  controllerSupport: string
  saveLoad: string
  performanceTarget: string
  offlineSupport: string
}

export interface GameLaunchMeta {
  id: string
  title: string
  launchType: GameLaunchType
  readiness: GameReadiness
  webBuildPath?: string
  checklist: GameLaunchChecklist
  nextAction: string
}

import { evaluateAppPolicy, DeploymentMode } from './policyEnforcementService'

export type GameLaunchResultStatus =
  | 'launched'
  | 'not_connected'
  | 'native_build_pending'
  | 'unavailable'
  | 'blocked_by_policy'

export interface GameLaunchResult {
  status: GameLaunchResultStatus
  gameId: string
  message: string
  openedUrl?: string
}

export const GAME_LAUNCH_REGISTRY: Record<string, GameLaunchMeta> = {
  'anime-aggressors': {
    id: 'anime-aggressors',
    title: 'Anime Aggressors',
    launchType: 'web_build',
    readiness: 'playable_web_build',
    webBuildPath: '/games/anime-aggressors-web/index.html',
    checklist: {
      buildPath: 'games/anime-aggressors-web → public/games/anime-aggressors-web',
      controllerSupport: 'Keyboard wired; gamepad placeholder',
      saveLoad: 'Not wired',
      performanceTarget: '60 FPS target',
      offlineSupport: 'Static web build; cache via PWA future',
    },
    nextAction: 'Expand vertical slice — roster, saves, tournaments',
  },
  'foot-racing': {
    id: 'foot-racing',
    title: 'Foot Racing Game',
    launchType: 'web_build',
    readiness: 'playable_web_build',
    webBuildPath: '/games/foot-racing-web/index.html',
    checklist: {
      buildPath: 'games/foot-racing-web → public/games/foot-racing-web',
      controllerSupport: 'Keyboard wired; gamepad placeholder',
      saveLoad: 'Not wired',
      performanceTarget: '60 FPS target',
      offlineSupport: 'Static web build; cache via PWA future',
    },
    nextAction: 'Expand vertical slice — tracks, multiplayer, native build',
  },
  'earth-species': {
    id: 'earth-species',
    title: 'Earth Species Artifact Adventure',
    launchType: 'web_build',
    readiness: 'playable_web_build',
    webBuildPath: '/games/earth-species-web/index.html',
    checklist: {
      buildPath: 'games/earth-species-web → public/games/earth-species-web',
      controllerSupport: 'Keyboard wired; touch planned',
      saveLoad: 'Collection log in-session only',
      performanceTarget: '60 FPS target',
      offlineSupport: 'Static web build; cache via PWA future',
    },
    nextAction: 'Expand vertical slice — quests, verified citations, native build',
  },
}

export function getGameLaunchMeta(gameId: string): GameLaunchMeta | undefined {
  return GAME_LAUNCH_REGISTRY[gameId]
}

export function launchGame(
  gameId: string,
  deploymentMode: DeploymentMode = 'Play',
  openWindow: (url: string) => Window | null = url => window.open(url, '_blank', 'noopener,noreferrer'),
): GameLaunchResult {
  const meta = getGameLaunchMeta(gameId)
  if (!meta) {
    return { status: 'unavailable', gameId, message: 'Unknown game' }
  }

  const policy = evaluateAppPolicy(gameId, deploymentMode, { isFirstPartyGame: true })
  if (!policy.canLaunch) {
    return { status: 'blocked_by_policy', gameId, message: policy.message }
  }

  if (meta.readiness === 'playable_web_build' && meta.webBuildPath) {
    openWindow(meta.webBuildPath)
    return {
      status: 'launched',
      gameId,
      message: `Launched ${meta.title} web build`,
      openedUrl: meta.webBuildPath,
    }
  }

  if (meta.readiness === 'native_build_pending') {
    return {
      status: 'native_build_pending',
      gameId,
      message: `${meta.title}: native build not connected. ${meta.nextAction}`,
    }
  }

  if (meta.readiness === 'design_stub') {
    return {
      status: 'not_connected',
      gameId,
      message: `${meta.title} is a design stub. ${meta.nextAction}`,
    }
  }

  return {
    status: 'not_connected',
    gameId,
    message: `${meta.title} is not wired yet. ${meta.nextAction}`,
  }
}
