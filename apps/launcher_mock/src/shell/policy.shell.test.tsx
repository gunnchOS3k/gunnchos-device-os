import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import MediaMode from './MediaMode'
import CampusMode from './CampusMode'
import { DEFAULT_PROFILE } from '../data/studentProfile'
import { saveDeploymentMode } from '../services/policyEnforcementService'

const profile = { ...DEFAULT_PROFILE, displayName: 'Test', onboarded: true }

describe('Shell policy enforcement UI', () => {
  beforeEach(() => {
    localStorage.setItem('gunnchos-profile', JSON.stringify(profile))
    saveDeploymentMode('School')
  })

  it('shows blocked reason for Netflix in School Mode', () => {
    render(<MediaMode onExit={() => {}} deploymentMode="School" />)
    expect(screen.getByTestId('blocked-reason-netflix')).toBeInTheDocument()
  })

  it('Campus Mode shows blocked ChatGPT in School Mode', () => {
    render(
      <CampusMode
        profile={profile}
        deploymentMode="School"
        onEnterGameMode={() => {}}
        onEnterMediaMode={() => {}}
        onResetOnboarding={() => {}}
      />,
    )
    expect(screen.getByTestId('blocked-chatgpt')).toBeInTheDocument()
  })

  it('Offline Mode blocks YouTube streaming card', () => {
    render(<MediaMode onExit={() => {}} deploymentMode="Offline" />)
    expect(screen.getByTestId('blocked-reason-youtube')).toBeInTheDocument()
  })
})
