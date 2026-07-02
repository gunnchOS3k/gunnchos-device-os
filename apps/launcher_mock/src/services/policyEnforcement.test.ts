import { describe, it, expect, vi } from 'vitest'
import { evaluateAppPolicy } from './policyEnforcementService'
import { launchApp } from './appLaunchService'
import { launchGame } from './gameLaunchService'

describe('policyEnforcementService', () => {
  it('School Mode blocks Netflix', () => {
    const r = evaluateAppPolicy('netflix', 'School', { schoolModeDefault: 'blocked' })
    expect(r.canLaunch).toBe(false)
    expect(r.decision).toBe('blocked_by_school')
  })

  it('School Mode blocks Hulu', () => {
    const r = evaluateAppPolicy('hulu', 'School', { schoolModeDefault: 'blocked' })
    expect(r.canLaunch).toBe(false)
  })

  it('Offline Mode blocks streaming routes', () => {
    const r = evaluateAppPolicy('youtube', 'Offline', { requiresNetwork: true, offlineSupported: false })
    expect(r.canLaunch).toBe(false)
    expect(r.message).toMatch(/Offline/i)
  })

  it('Media Mode allows YouTube', () => {
    const r = evaluateAppPolicy('youtube', 'Media', { requiresNetwork: true })
    expect(r.canLaunch).toBe(true)
  })

  it('Campus Mode allows school/productivity native apps', () => {
    expect(evaluateAppPolicy('files', 'Media', { isNativeShellApp: true }).canLaunch).toBe(true)
    expect(evaluateAppPolicy('notes', 'School', { isNativeShellApp: true }).canLaunch).toBe(true)
  })

  it('Game Mode allows first-party games', () => {
    const r = evaluateAppPolicy('anime-aggressors', 'Play', { isFirstPartyGame: true })
    expect(r.canLaunch).toBe(true)
  })

  it('appLaunchService respects policy in School mode', () => {
    const result = launchApp(
      { id: 'vscode-web', name: 'VS Code Web', launchType: 'external_url', url: 'https://vscode.dev' },
      'School',
      vi.fn(),
    )
    expect(result.status).toBe('blocked_by_policy')
  })

  it('gameLaunchService allows playable web build in Play mode', () => {
    const openWindow = vi.fn(() => ({}) as Window)
    const result = launchGame('anime-aggressors', 'Play', openWindow)
    expect(result.status).toBe('launched')
  })
})
