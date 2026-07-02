import { describe, it, expect, vi } from 'vitest'
import { launchApp, pwaTargetToLaunchTarget } from './appLaunchService'
import { PWA_TARGETS } from '../data/pwaTargets'

describe('appLaunchService', () => {
  it('opens valid external_url in new tab', () => {
    const openWindow = vi.fn(() => ({}) as Window)
    const result = launchApp(
      { id: 'drive', name: 'Google Drive', launchType: 'external_url', url: 'https://drive.google.com' },
      'Media',
      openWindow,
    )
    expect(result.status).toBe('launched')
    expect(openWindow).toHaveBeenCalledWith('https://drive.google.com')
  })

  it('returns missing_url when url absent', () => {
    const result = launchApp({ id: 'x', name: 'X', launchType: 'external_url' }, 'Media')
    expect(result.status).toBe('missing_url')
  })

  it('returns blocked_by_policy for vscode-web in School mode', () => {
    const result = launchApp(
      pwaTargetToLaunchTarget(PWA_TARGETS.find(t => t.id === 'vscode-web')!),
      'School',
      vi.fn(),
    )
    expect(result.status).toBe('blocked_by_policy')
  })

  it('returns blocked_by_policy for chatgpt in School mode', () => {
    const result = launchApp(
      pwaTargetToLaunchTarget(PWA_TARGETS.find(t => t.id === 'chatgpt')!),
      'School',
      vi.fn(),
    )
    expect(result.status).toBe('blocked_by_policy')
  })

  it('Google Drive route exists in PWA targets', () => {
    const drive = PWA_TARGETS.find(t => t.id === 'drive')
    expect(drive?.url).toBe('https://drive.google.com')
  })

  it('Brightspace D2L route exists', () => {
    const d2l = PWA_TARGETS.find(t => t.id === 'd2l')
    expect(d2l?.url).toContain('d2l')
  })

  it('ChatGPT route exists', () => {
    const chatgpt = PWA_TARGETS.find(t => t.id === 'chatgpt')
    expect(chatgpt?.url).toContain('openai')
  })

  it('VS Code Web route exists', () => {
    const vscode = PWA_TARGETS.find(t => t.id === 'vscode-web')
    expect(vscode?.url).toContain('vscode')
  })
})
