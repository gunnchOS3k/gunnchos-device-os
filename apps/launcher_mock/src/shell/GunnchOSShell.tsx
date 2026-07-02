import { useState } from 'react'
import { useLocalStorage } from '../hooks/useLocalStorage'
import { DEFAULT_PROFILE, StudentProfile } from '../data/studentProfile'
import FirstBootFlow from './FirstBootFlow'
import CampusMode from './CampusMode'
import GameMode from './GameMode'
import MediaMode from './MediaMode'

export type SystemMode = 'campus' | 'game' | 'media'

interface GunnchOSShellProps {
  devMode?: boolean
  onOpenDevTools?: () => void
}

export default function GunnchOSShell({ devMode, onOpenDevTools }: GunnchOSShellProps) {
  const [profile, setProfile] = useLocalStorage<StudentProfile>('gunnchos-profile', DEFAULT_PROFILE)
  const [systemMode, setSystemMode] = useState<SystemMode>('campus')

  const completeOnboarding = (p: StudentProfile) => setProfile(p)

  const resetOnboarding = () => {
    setProfile(DEFAULT_PROFILE)
    setSystemMode('campus')
  }

  if (!profile.onboarded) {
    return <FirstBootFlow onComplete={completeOnboarding} />
  }

  if (systemMode === 'game') {
    return <GameMode onExit={() => setSystemMode('campus')} />
  }

  if (systemMode === 'media') {
    return (
      <MediaMode
        onExit={() => setSystemMode('campus')}
        deploymentMode={profile.offline ? 'Offline' : profile.guardian ? 'Guardian' : 'Media'}
      />
    )
  }

  return (
    <>
      <CampusMode
        profile={profile}
        onEnterGameMode={() => setSystemMode('game')}
        onEnterMediaMode={() => setSystemMode('media')}
        onResetOnboarding={resetOnboarding}
      />
      {devMode && onOpenDevTools && (
        <button
          type="button"
          onClick={onOpenDevTools}
          style={{
            position: 'fixed',
            bottom: 72,
            right: 12,
            zIndex: 200,
            padding: '6px 10px',
            fontSize: 11,
            borderRadius: 6,
            border: '1px solid #3c4043',
            background: '#1a2332',
            color: '#9aa0a6',
            cursor: 'pointer',
            opacity: 0.7,
          }}
        >
          Dev: Fleet view
        </button>
      )}
    </>
  )
}
