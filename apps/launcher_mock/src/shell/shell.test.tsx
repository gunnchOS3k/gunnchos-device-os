import { render, screen, fireEvent } from '@testing-library/react'
import GunnchOSShell from '../shell/GunnchOSShell'
import { describe, it, expect, beforeEach } from 'vitest'
import App from '../App'
import FirstBootFlow from '../shell/FirstBootFlow'
import CampusMode from '../shell/CampusMode'
import GameMode from '../shell/GameMode'
import MediaMode from '../shell/MediaMode'
import BrowserPwaHub from '../shell/BrowserPwaHub'
import SettingsPanel from '../shell/SettingsPanel'
import { DEFAULT_PROFILE } from '../data/studentProfile'

const onboardedProfile = {
  ...DEFAULT_PROFILE,
  displayName: 'Test Student',
  onboarded: true,
}

describe('GunnchOS shell', () => {
  beforeEach(() => {
    localStorage.setItem('gunnchos-profile', JSON.stringify(onboardedProfile))
  })

  it('App renders without crashing', () => {
    render(<App />)
    expect(screen.getByText(/Campus Mode/i)).toBeInTheDocument()
  })

  it('FirstBootFlow renders', () => {
    localStorage.removeItem('gunnchos-profile')
    render(<FirstBootFlow onComplete={() => {}} />)
    expect(screen.getByText(/Welcome to GunnchOS/i)).toBeInTheDocument()
  })

  it('Campus Mode renders', () => {
    render(
      <CampusMode
        profile={onboardedProfile}
        onEnterGameMode={() => {}}
        onEnterMediaMode={() => {}}
        onResetOnboarding={() => {}}
      />,
    )
    expect(screen.getByText(/Hey Test/i)).toBeInTheDocument()
  })

  it('Game Mode renders first-party games', () => {
    render(<GameMode onExit={() => {}} />)
    expect(screen.getByText(/Anime Aggressors/i)).toBeInTheDocument()
    expect(screen.getByText(/Foot Racing Game/i)).toBeInTheDocument()
    expect(screen.getByText(/Earth Species/i)).toBeInTheDocument()
  })

  it('Media Mode renders', () => {
    render(<MediaMode onExit={() => {}} />)
    expect(screen.getByTestId('media-mode')).toBeInTheDocument()
    expect(screen.getByText(/Media Mode/i)).toBeInTheDocument()
  })

  it('Media cards render YouTube, Netflix, Hulu, and Local Media', () => {
    render(<MediaMode onExit={() => {}} />)
    expect(screen.getByTestId('media-card-youtube')).toBeInTheDocument()
    expect(screen.getByTestId('media-card-netflix')).toBeInTheDocument()
    expect(screen.getByTestId('media-card-hulu')).toBeInTheDocument()
    expect(screen.getByTestId('media-card-local_media')).toBeInTheDocument()
  })

  it('Netflix/Hulu DRM warnings appear', () => {
    render(<MediaMode onExit={() => {}} />)
    expect(screen.getByTestId('drm-warning-netflix')).toBeInTheDocument()
    expect(screen.getByTestId('drm-warning-hulu')).toBeInTheDocument()
  })

  it('Browser/PWA hub renders', () => {
    render(<BrowserPwaHub onBack={() => {}} />)
    expect(screen.getByText(/Browser & PWA Hub/i)).toBeInTheDocument()
  })

  it('Settings panel renders', () => {
    render(
      <SettingsPanel
        profile={onboardedProfile}
        onBack={() => {}}
        onResetOnboarding={() => {}}
      />,
    )
    expect(screen.getByText(/Settings/i)).toBeInTheDocument()
  })

  it('switching modes does not crash', () => {
    render(<GunnchOSShell />)
    fireEvent.click(screen.getByLabelText('Media Mode'))
    expect(screen.getByTestId('media-mode')).toBeInTheDocument()
    fireEvent.click(screen.getByText(/Exit to Campus/i))
    expect(screen.getByText(/Campus Mode/i)).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('Game Mode'))
    expect(screen.getByText(/Anime Aggressors/i)).toBeInTheDocument()
  })
})
