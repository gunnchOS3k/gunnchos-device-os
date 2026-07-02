import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import BrowserPwaHub from './BrowserPwaHub'
import * as appLaunch from '../services/appLaunchService'

describe('BrowserPwaHub', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders hub with real launch actions', () => {
    render(<BrowserPwaHub onBack={() => {}} />)
    expect(screen.getByTestId('browser-pwa-hub')).toBeInTheDocument()
    expect(screen.getByText(/external browser route prototype/i)).toBeInTheDocument()
    expect(screen.getByTestId('pwa-launch-drive')).toBeInTheDocument()
    expect(screen.getByTestId('pwa-launch-chatgpt')).toBeInTheDocument()
  })

  it('shows launch result when app opened', () => {
    vi.spyOn(appLaunch, 'launchApp').mockReturnValue({
      status: 'launched',
      targetId: 'drive',
      message: 'Opened Google Drive in a new browser tab',
      openedUrl: 'https://drive.google.com',
    })
    render(<BrowserPwaHub onBack={() => {}} />)
    fireEvent.click(screen.getByTestId('pwa-launch-drive'))
    expect(screen.getByTestId('launch-result')).toHaveTextContent(/launched/i)
  })

  it('shows blocked result in School mode', () => {
    vi.spyOn(appLaunch, 'launchApp').mockReturnValue({
      status: 'blocked_by_policy',
      targetId: 'vscode-web',
      message: 'vscode is blocked in School Mode',
    })
    render(<BrowserPwaHub onBack={() => {}} deploymentMode="School" />)
    fireEvent.click(screen.getByTestId('pwa-launch-vscode-web'))
    expect(screen.getByTestId('launch-result')).toHaveTextContent(/blocked/i)
  })
})
