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
    const result = launchGame('anime-aggressors', 'Play', openWindow)
    expect(result.status).toBe('launched')
    expect(openWindow).toHaveBeenCalledWith('/games/anime-aggressors-web/index.html')
    GAME_LAUNCH_REGISTRY['anime-aggressors'] = original
  })

  it('anime-aggressors is playable_web_build with valid path', () => {
    const meta = getGameLaunchMeta('anime-aggressors')
    expect(meta?.readiness).toBe('playable_web_build')
    expect(meta?.webBuildPath).toBe('/games/anime-aggressors-web/index.html')
    const openWindow = vi.fn(() => ({}) as Window)
    const result = launchGame('anime-aggressors', 'Play', openWindow)
    expect(result.status).toBe('launched')
    expect(openWindow).toHaveBeenCalledWith('/games/anime-aggressors-web/index.html')
  })

  it('foot-racing is playable_web_build with valid path', () => {
    const meta = getGameLaunchMeta('foot-racing')
    expect(meta?.readiness).toBe('playable_web_build')
    expect(meta?.webBuildPath).toBe('/games/foot-racing-web/index.html')
    const openWindow = vi.fn(() => ({}) as Window)
    const result = launchGame('foot-racing', 'Play', openWindow)
    expect(result.status).toBe('launched')
    expect(openWindow).toHaveBeenCalledWith('/games/foot-racing-web/index.html')
  })

  it('earth-species is playable_web_build with valid path', () => {
    const meta = getGameLaunchMeta('earth-species')
    expect(meta?.readiness).toBe('playable_web_build')
    expect(meta?.webBuildPath).toBe('/games/earth-species-web/index.html')
    const openWindow = vi.fn(() => ({}) as Window)
    const result = launchGame('earth-species', 'Play', openWindow)
    expect(result.status).toBe('launched')
    expect(openWindow).toHaveBeenCalledWith('/games/earth-species-web/index.html')
  })

  it('includes launch readiness checklist fields', () => {
    const meta = getGameLaunchMeta('earth-species')
    expect(meta?.checklist.buildPath).toBeTruthy()
    expect(meta?.checklist.controllerSupport).toBeTruthy()
  })
})
