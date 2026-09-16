import { useEffect, useMemo, useState, KeyboardEvent } from 'react'
import { theme } from './styles/gunnchosTheme'
import HomeSurface from './surfaces/HomeSurface'
import VaultSurface from './surfaces/VaultSurface'
import AppCenterSurface from './surfaces/AppCenterSurface'
import ConnectSurface from './surfaces/ConnectSurface'
import AssistSurface from './surfaces/AssistSurface'
import CareSurface from './surfaces/CareSurface'
import './cx2.css'

export type Cx2Surface = 'home' | 'vault' | 'app_center' | 'connect' | 'assist' | 'care'

const SURFACES: { id: Cx2Surface; label: string; shortcut: string }[] = [
  { id: 'home', label: 'Home', shortcut: '1' },
  { id: 'vault', label: 'Vault', shortcut: '2' },
  { id: 'app_center', label: 'App Center', shortcut: '3' },
  { id: 'connect', label: 'Connect', shortcut: '4' },
  { id: 'assist', label: 'Assist', shortcut: '5' },
  { id: 'care', label: 'Care', shortcut: '6' },
]

export type DeviceProfile = 'student_14_5' | 'handheld_hybrid' | 'ds_xl' | 'docked' | 'ci_qemu'

interface Props {
  profile?: DeviceProfile
  offline?: boolean
  onExit?: () => void
}

export default function CompleteExperienceShell({
  profile = 'student_14_5',
  offline = false,
  onExit,
}: Props) {
  const [surface, setSurface] = useState<Cx2Surface>('home')
  const [history, setHistory] = useState<Cx2Surface[]>(['home'])
  const [error, setError] = useState<string | null>(null)
  const [highContrast, setHighContrast] = useState(false)
  const [reduceMotion, setReduceMotion] = useState(false)
  const [scale, setScale] = useState(1)

  const go = (id: Cx2Surface) => {
    setError(null)
    setSurface(id)
    setHistory((h) => [...h, id])
  }

  const back = () => {
    setHistory((h) => {
      if (h.length <= 1) return h
      const next = h.slice(0, -1)
      setSurface(next[next.length - 1])
      return next
    })
  }

  const home = () => {
    setHistory(['home'])
    setSurface('home')
    setError(null)
  }

  useEffect(() => {
    const onKey = (e: globalThis.KeyboardEvent) => {
      if (e.altKey && e.key >= '1' && e.key <= '6') {
        e.preventDefault()
        go(SURFACES[Number(e.key) - 1].id)
      }
      if (e.key === 'Escape') back()
      if (e.altKey && e.key.toLowerCase() === 'h') home()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const layoutClass = useMemo(() => {
    const parts = ['cx2-shell', `profile-${profile}`]
    if (highContrast) parts.push('high-contrast')
    if (reduceMotion) parts.push('reduce-motion')
    if (offline) parts.push('offline')
    return parts.join(' ')
  }, [profile, highContrast, reduceMotion, offline])

  const body = (() => {
    switch (surface) {
      case 'home':
        return <HomeSurface offline={offline} onNavigate={go} />
      case 'vault':
        return <VaultSurface offline={offline} onError={setError} />
      case 'app_center':
        return <AppCenterSurface offline={offline} onError={setError} />
      case 'connect':
        return <ConnectSurface offline={offline} onError={setError} />
      case 'assist':
        return (
          <AssistSurface
            highContrast={highContrast}
            reduceMotion={reduceMotion}
            scale={scale}
            onHighContrast={setHighContrast}
            onReduceMotion={setReduceMotion}
            onScale={setScale}
          />
        )
      case 'care':
        return <CareSurface offline={offline} onError={setError} />
    }
  })()

  return (
    <div
      className={layoutClass}
      style={{ fontSize: `${scale}rem` }}
      role="application"
      aria-label="gunnchOS Complete Experience"
    >
      <header className="cx2-topbar" role="banner">
        <div className="cx2-brand" aria-label="gunnchOS brand">
          <span className="cx2-brand-mark">gunnchOS</span>
          <span className="cx2-brand-sub">Complete Experience</span>
        </div>
        <nav className="cx2-nav" aria-label="Primary">
          {SURFACES.map((s) => (
            <button
              key={s.id}
              type="button"
              className={surface === s.id ? 'cx2-nav-btn active' : 'cx2-nav-btn'}
              aria-current={surface === s.id ? 'page' : undefined}
              aria-keyshortcuts={`Alt+${s.shortcut}`}
              onClick={() => go(s.id)}
            >
              {s.label}
            </button>
          ))}
        </nav>
        <div className="cx2-top-actions">
          <button type="button" className="cx2-nav-btn" onClick={back} aria-label="Back" disabled={history.length <= 1}>
            Back
          </button>
          <button type="button" className="cx2-nav-btn" onClick={home} aria-label="Home">
            Home
          </button>
          {onExit && (
            <button type="button" className="cx2-nav-btn" onClick={onExit} aria-label="Exit Complete Experience">
              Exit
            </button>
          )}
        </div>
      </header>
      {offline && (
        <div className="cx2-banner" role="status">
          Offline — queued actions will sync when connectivity returns.
        </div>
      )}
      {error && (
        <div className="cx2-banner error" role="alert">
          {error}
        </div>
      )}
      <main className="cx2-main" id="cx2-main" tabIndex={-1}>
        {body}
      </main>
      <footer className="cx2-footer" role="contentinfo">
        Profile {profile.replace(/_/g, ' ')} · keyboard Alt+1..6 · Escape back
      </footer>
    </div>
  )
}
