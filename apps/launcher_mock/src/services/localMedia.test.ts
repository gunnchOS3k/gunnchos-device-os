import { describe, it, expect, beforeEach } from 'vitest'
import { formatFileSize, formatMimeType, rememberMedia, listRecentMedia, VIDEO_ACCEPT, AUDIO_ACCEPT } from './localMediaStore'

describe('localMediaStore', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('formats file size', () => {
    expect(formatFileSize(500)).toBe('500 B')
    expect(formatFileSize(2048)).toBe('2.0 KB')
    expect(formatFileSize(5 * 1024 * 1024)).toBe('5.0 MB')
  })

  it('formats mime type', () => {
    expect(formatMimeType('video/mp4')).toBe('video/mp4')
  })

  it('remembers recent media metadata', () => {
    rememberMedia({ name: 'clip.mp4', mimeType: 'video/mp4', sizeBytes: 1000 })
    expect(listRecentMedia()).toHaveLength(1)
    expect(listRecentMedia()[0].name).toBe('clip.mp4')
  })

  it('exports video and audio accept attributes', () => {
    expect(VIDEO_ACCEPT).toContain('video/mp4')
    expect(AUDIO_ACCEPT).toContain('audio/mpeg')
  })
})
