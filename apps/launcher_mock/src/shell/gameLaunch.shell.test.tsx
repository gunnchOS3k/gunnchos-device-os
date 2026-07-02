import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import GameMode from './GameMode'

describe('GameMode launch adapter', () => {
  it('renders first-party games without Launch mock copy', () => {
    render(<GameMode onExit={() => {}} />)
    expect(screen.getByText(/Anime Aggressors/i)).toBeInTheDocument()
    expect(screen.queryByText(/Launch \(mock\)/i)).not.toBeInTheDocument()
  })

  it('shows launch readiness checklist', () => {
    render(<GameMode onExit={() => {}} />)
    fireEvent.click(screen.getByText(/Anime Aggressors/i))
    expect(screen.getByTestId('game-launch-panel')).toBeInTheDocument()
    expect(screen.getByTestId('launch-readiness-checklist')).toBeInTheDocument()
    expect(screen.getByTestId('game-readiness')).toHaveTextContent(/not connected/i)
  })

  it('shows not connected status for anime-aggressors before web build', () => {
    render(<GameMode onExit={() => {}} />)
    fireEvent.click(screen.getByText(/Anime Aggressors/i))
    expect(screen.getByTestId('game-readiness')).toHaveTextContent(/not connected/i)
    expect(screen.getByTestId('launch-readiness-checklist')).toHaveTextContent(/Phase 2E/i)
    expect(screen.getByTestId('game-launch-button')).toBeDisabled()
  })
})
