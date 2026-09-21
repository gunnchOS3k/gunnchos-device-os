import { describe, expect, it } from 'vitest'
import { FEEDBACK_HUB_URL, feedbackUrlForComponent, SECURITY_MD_URL } from './feedbackUrls'

describe('feedbackUrls', () => {
  it('uses accepted-main hub (never RC1 feature branch)', () => {
    expect(FEEDBACK_HUB_URL).toContain('/blob/main/FEEDBACK.md')
    expect(FEEDBACK_HUB_URL).not.toContain('release/v1.0.0-rc1-ecosystem-freeze')
    expect(SECURITY_MD_URL).toContain('/blob/main/SECURITY.md')
  })

  it('allows public component marker only', () => {
    const url = feedbackUrlForComponent('Device OS')
    expect(url).toContain('component=Device')
    expect(url).not.toMatch(/serial|token|password|@|\d+\.\d+\.\d+\.\d+/i)
  })

  it('strips unsafe characters from component marker', () => {
    const url = feedbackUrlForComponent('Device OS<script>/etc/passwd')
    expect(url).not.toContain('<')
    expect(url).not.toContain('/etc/')
  })
})