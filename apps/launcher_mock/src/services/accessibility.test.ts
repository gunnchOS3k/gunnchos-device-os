import { describe, it, expect } from 'vitest'
import { auditAccessibilitySettings } from './accessibilityAudit'
import { DEFAULT_SETTINGS } from './settingsStore'

describe('accessibilityAudit', () => {
  it('reports settings without certification claim', () => {
    const r = auditAccessibilitySettings({ ...DEFAULT_SETTINGS, largeText: true })
    expect(r.largeTextEnabled).toBe(true)
    expect(r.certificationClaimed).toBe(false)
  })
})
