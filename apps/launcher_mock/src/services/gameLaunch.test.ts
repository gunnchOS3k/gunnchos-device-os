import { describe, it, expect, vi } from 'vitest'
import { launchGame, getGameLaunchMeta, GAME_LAUNCH_REGISTRY } from './gameLaunchService'

describe('gameLaunchService', () => {
  it('returns playable for web_build when readiness is playable', () => {
    const original = { ...GAME_LAUNCH_REGISTRY['anime-aggressors'] }
    GAME_LAUNCH_REGISTRY['anime-aggressors'] = {
      ...original,
      readiness: 'playable_web_build',
      webBuildPath: '/games/anime-aggressors-web/index.html',
    }
    const openWindow = vi.fn(() => ({}) as Window)
    const result = launchGame('anime-aggressors', openWindow)
    expect(result.status).toBe('launched')
    expect(openWindow).toHaveBeenCalledWith('/games/anime-aggressors-web/index.html')
    GAME_LAUNCH_REGISTRY['anime-aggressors'] = original
  })

  it('returns not_connected for missing build', () => {
    const result = launchGame('anime-aggressors')
    expect(result.status).toBe('not_connected')
  })

  it('returns native_build_pending for foot-racing', () => {
    const result = launchGame('foot-racing')
    expect(result.status).toBe('native_build_pending')
  })

  it('includes launch readiness checklist fields', () => {
    const meta = getGameLaunchMeta('earth-species')
    expect(meta?.checklist.buildPath).toBeTruthy()
    expect(meta?.checklist.controllerSupport).toBeTruthy()
  })
})
