import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import LocalMediaPlayer from './LocalMediaPlayer'
import MediaMode from './MediaMode'

describe('Local media player', () => {
  it('renders with claim boundary', () => {
    render(<LocalMediaPlayer onBack={() => {}} />)
    expect(screen.getByTestId('local-media-player')).toBeInTheDocument()
    expect(screen.getByText(/browser-backed media playback prototype/i)).toBeInTheDocument()
  })

  it('has file input with audio/video accept', () => {
    render(<LocalMediaPlayer onBack={() => {}} />)
    const input = screen.getByTestId('local-media-file-input') as HTMLInputElement
    expect(input.accept).toContain('video/mp4')
    expect(input.accept).toContain('audio/mpeg')
  })

  it('Media Mode opens local player from Local Media card', () => {
    render(<MediaMode onExit={() => {}} />)
    fireEvent.click(screen.getByTestId('media-card-local_media'))
    expect(screen.getByTestId('local-media-player')).toBeInTheDocument()
  })

  it('DRM disclaimers remain on streaming cards', () => {
    render(<MediaMode onExit={() => {}} />)
    expect(screen.getByTestId('drm-warning-netflix')).toBeInTheDocument()
    expect(screen.getByTestId('drm-warning-hulu')).toBeInTheDocument()
  })
})
