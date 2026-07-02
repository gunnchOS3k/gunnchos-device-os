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

export type GameLaunchResultStatus = 'launched' | 'not_connected' | 'native_build_pending' | 'unavailable'

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
    launchType: 'native_future',
    readiness: 'native_build_pending',
    checklist: {
      buildPath: 'Native engine path TBD',
      controllerSupport: 'Designed',
      saveLoad: 'Cloud save Phase 3',
      performanceTarget: '60 FPS target',
      offlineSupport: 'Planned',
    },
    nextAction: 'Connect native build or web prototype',
  },
  'earth-species': {
    id: 'earth-species',
    title: 'Earth Species Artifact Adventure',
    launchType: 'unavailable',
    readiness: 'design_stub',
    checklist: {
      buildPath: 'Design doc only',
      controllerSupport: 'Planned',
      saveLoad: 'Local save planned',
      performanceTarget: '60 FPS target',
      offlineSupport: 'Core requirement',
    },
    nextAction: 'Complete vertical slice design before build wiring',
  },
}

export function getGameLaunchMeta(gameId: string): GameLaunchMeta | undefined {
  return GAME_LAUNCH_REGISTRY[gameId]
}

export function launchGame(
  gameId: string,
  openWindow: (url: string) => Window | null = url => window.open(url, '_blank', 'noopener,noreferrer'),
): GameLaunchResult {
  const meta = getGameLaunchMeta(gameId)
  if (!meta) {
    return { status: 'unavailable', gameId, message: 'Unknown game' }
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
