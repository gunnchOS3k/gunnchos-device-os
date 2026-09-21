import { describe, expect, it } from 'vitest'
import { FEEDBACK_HUB_URL, feedbackUrlForComponent } from './feedbackUrls'

describe('launcher feedbackUrls', () => {
  it('targets accepted-main FEEDBACK.md', () => {
    expect(FEEDBACK_HUB_URL).toContain('/blob/main/FEEDBACK.md')
    expect(feedbackUrlForComponent('Device OS')).toContain('component=')
  })
})