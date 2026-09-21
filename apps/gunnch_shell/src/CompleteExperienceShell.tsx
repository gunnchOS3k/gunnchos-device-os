import { useEffect, useMemo, useState } from 'react'
import HomeSurface from './surfaces/HomeSurface'
import VaultSurface from './surfaces/VaultSurface'
import AppCenterSurface from './surfaces/AppCenterSurface'
import ConnectSurface from './surfaces/ConnectSurface'
import AssistSurface from './surfaces/AssistSurface'
import CareSurface from './surfaces/CareSurface'
import WalletSurface from './surfaces/WalletSurface'
import PortfolioSurface from './surfaces/PortfolioSurface'
import CareerProfileSurface from './surfaces/CareerProfileSurface'
import VerifierSurface from './surfaces/VerifierSurface'
import SettingsSurface, { type SettingsSectionId } from './surfaces/SettingsSurface'
import SearchCommandSurface from './surfaces/SearchCommandSurface'
import WaikeSurface from './surfaces/WaikeSurface'
import GunnchAiSurface from './surfaces/GunnchAiSurface'
import GamesSurface from './surfaces/GamesSurface'
import CreationSurface from './surfaces/CreationSurface'
import LeisureSurface from './surfaces/LeisureSurface'
import type { HostKind } from './platform/hostRuntime'
import { recordContinuity } from './platform/continuityStore'
import Icon from './design/icons/Icon'
import type { VxpIconName } from './design/tokens'
import type { Cx2Surface } from './shellSurfaces'
import './design/tokens.css'
import './cx2.css'

export type { Cx2Surface } from './shellSurfaces'

type NavItem = { id: Cx2Surface; label: string; shortcut: string; icon: VxpIconName }

const PRIMARY_NAV: NavItem[] = [
  { id: 'home', label: 'Home', shortcut: '1', icon: 'home' },
  { id: 'vault', label: 'Vault', shortcut: '2', icon: 'vault' },
  { id: 'app_center', label: 'Apps', shortcut: '3', icon: 'app_center' },
  { id: 'connect', label: 'Connect', shortcut: '4', icon: 'connect' },
]

const MORE_NAV: NavItem[] = [
  { id: 'waike', label: 'WAIKE', shortcut: '5', icon: 'career' },
  { id: 'gunnchai', label: 'gunnchAI', shortcut: '6', icon: 'assist' },
  { id: 'games', label: 'Games', shortcut: '7', icon: 'app_center' },
  { id: 'creation', label: 'Creation', shortcut: '8', icon: 'file' },
  { id: 'leisure', label: 'Leisure', shortcut: '9', icon: 'care' },
  { id: 'assist', label: 'Assist', shortcut: '0', icon: 'assist' },
  { id: 'care', label: 'Care', shortcut: '', icon: 'care' },
  { id: 'wallet', label: 'Wallet', shortcut: '', icon: 'wallet' },
  { id: 'portfolio', label: 'Portfolio', shortcut: '', icon: 'portfolio' },
  { id: 'career', label: 'Career', shortcut: '', icon: 'career' },
  { id: 'verifier', label: 'Verifier', shortcut: '', icon: 'verifier' },
  { id: 'settings', label: 'Settings', shortcut: '', icon: 'status_ok' },
  { id: 'search', label: 'Search', shortcut: '', icon: 'search' },
]

/** Keyboard Alt catalog — primary + first more items with shortcuts. */
const SURFACES: NavItem[] = [
  ...PRIMARY_NAV,
  ...MORE_NAV.filter((s) => s.shortcut),
]

export type DeviceProfile = 'student_14_5' | 'handheld_hybrid' | 'ds_xl' | 'docked' | 'ci_qemu'

interface Props {
  profile?: DeviceProfile
  offline?: boolean
  onExit?: () => void
  initialSurface?: Cx2Surface
  onSessionChange?: (partial: {
    surface: string
    history: string[]
    highContrast: boolean
    reduceMotion: boolean
    scale: number
  }) => void
  hostKind?: HostKind
}

function isMoreSurface(id: Cx2Surface): boolean {
  return MORE_NAV.some((s) => s.id === id)
}

const CONTINUITY_SURFACES: Cx2Surface[] = [
  'waike',
  'vault',
  'app_center',
  'games',
  'gunnchai',
  'creation',
  'connect',
  'leisure',
]

export default function CompleteExperienceShell({
  profile = 'student_14_5',
  offline = false,
  onExit,
  initialSurface = 'home',
  onSessionChange,
  hostKind,
}: Props) {
  const [surface, setSurface] = useState<Cx2Surface>(initialSurface)
  const [history, setHistory] = useState<Cx2Surface[]>([initialSurface])
  const [error, setError] = useState<string | null>(null)
  const [highContrast, setHighContrast] = useState(false)
  const [reduceMotion, setReduceMotion] = useState(false)
  const [scale, setScale] = useState(1)
  const [moreOpen, setMoreOpen] = useState(() => isMoreSurface(initialSurface))
  const [wideLayout, setWideLayout] = useState(false)
  const [settingsSection, setSettingsSection] = useState<SettingsSectionId | undefined>(undefined)

  const emitSession = (nextSurface: Cx2Surface, nextHistory: Cx2Surface[]) => {
    onSessionChange?.({
      surface: nextSurface,
      history: nextHistory,
      highContrast,
      reduceMotion,
      scale,
    })
  }

  const go = (id: Cx2Surface) => {
    setError(null)
    setSurface(id)
    setMoreOpen(false)
    if (id !== 'settings') setSettingsSection(undefined)
    setHistory((h) => {
      const next = [...h, id]
      emitSession(id, next)
      return next
    })
    if (CONTINUITY_SURFACES.includes(id)) {
      recordContinuity({
        id: `surface-${id}`,
        domain:
          id === 'app_center'
            ? 'app'
            : id === 'vault'
              ? 'vault'
              : id === 'waike'
                ? 'waike'
                : id === 'games'
                  ? 'game'
                  : id === 'gunnchai'
                    ? 'gunnchai'
                    : id === 'creation'
                      ? 'creation'
                      : id === 'connect'
                        ? 'connect'
                        : 'leisure',
        title: MORE_NAV.find((s) => s.id === id)?.label || PRIMARY_NAV.find((s) => s.id === id)?.label || id,
        surface: id,
      })
    }
  }

  const back = () => {
    setHistory((h) => {
      if (h.length <= 1) return h
      const next = h.slice(0, -1)
      const s = next[next.length - 1]
      setSurface(s)
      setMoreOpen(false)
      emitSession(s, next)
      return next
    })
  }

  const home = () => {
    setHistory(['home'])
    setSurface('home')
    setMoreOpen(false)
    setError(null)
    emitSession('home', ['home'])
  }

  const openSettings = (section?: SettingsSectionId) => {
    setSettingsSection(section)
    go('settings')
  }

  useEffect(() => {
    onSessionChange?.({
      surface,
      history,
      highContrast,
      reduceMotion,
      scale,
    })
    // Intentional: persist assist prefs when they change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [highContrast, reduceMotion, scale])

  useEffect(() => {
    const mq = window.matchMedia('(min-width: 900px) and (orientation: landscape), (min-width: 1100px)')
    const apply = () => setWideLayout(mq.matches)
    apply()
    mq.addEventListener('change', apply)
    return () => mq.removeEventListener('change', apply)
  }, [])

  useEffect(() => {
    const onKey = (e: globalThis.KeyboardEvent) => {
      if (e.altKey && ((e.key >= '1' && e.key <= '9') || e.key === '0')) {
        e.preventDefault()
        const idx = e.key === '0' ? 9 : Number(e.key) - 1
        if (SURFACES[idx]) go(SURFACES[idx].id)
      }
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        go('search')
      }
      if (e.key === 'Escape') {
        if (moreOpen && !isMoreSurface(surface)) {
          setMoreOpen(false)
          return
        }
        back()
      }
      if (e.altKey && e.key.toLowerCase() === 'h') home()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [moreOpen, surface])

  const layoutClass = useMemo(() => {
    const parts = ['cx2-shell', 'vxp-living', `profile-${profile}`]
    if (highContrast) parts.push('high-contrast')
    if (reduceMotion) parts.push('reduce-motion')
    if (offline) parts.push('offline')
    if (wideLayout) parts.push('vxp-rail-layout')
    else parts.push('vxp-dock-layout')
    return parts.join(' ')
  }, [profile, highContrast, reduceMotion, offline, wideLayout])

  const body = (() => {
    switch (surface) {
      case 'home':
        return <HomeSurface offline={offline} onNavigate={go} hostKind={hostKind} />
      case 'vault':
        return <VaultSurface offline={offline} onError={setError} />
      case 'app_center':
        return <AppCenterSurface offline={offline} onError={setError} onOpenSurface={go} />
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
      case 'wallet':
        return <WalletSurface offline={offline} onError={setError} />
      case 'portfolio':
        return <PortfolioSurface offline={offline} onError={setError} />
      case 'career':
        return <CareerProfileSurface offline={offline} onError={setError} />
      case 'verifier':
        return <VerifierSurface offline={offline} onError={setError} />
      case 'settings':
        return (
          <SettingsSurface
            offline={offline}
            hostKind={hostKind}
            highContrast={highContrast}
            reduceMotion={reduceMotion}
            scale={scale}
            onHighContrast={setHighContrast}
            onReduceMotion={setReduceMotion}
            onScale={setScale}
            onNavigate={(id) => go(id)}
            initialSection={settingsSection}
          />
        )
      case 'search':
        return (
          <SearchCommandSurface
            onNavigate={go}
            onOpenSettingsSection={(section) => openSettings(section)}
          />
        )
      case 'waike':
        return <WaikeSurface offline={offline} onError={setError} onReturnHome={home} />
      case 'gunnchai':
        return <GunnchAiSurface offline={offline} onError={setError} />
      case 'games':
        return <GamesSurface onError={setError} />
      case 'creation':
        return <CreationSurface onError={setError} />
      case 'leisure':
        return <LeisureSurface onNavigateVault={() => go('vault')} />
    }
  })()

  const primaryActive = (id: Cx2Surface) => surface === id
  const moreActive = (isMoreSurface(surface) && surface !== 'settings' && surface !== 'search') || moreOpen

  const navButtons = (items: NavItem[], ariaLabel: string) => (
    <nav className="vxp-nav" aria-label={ariaLabel}>
      {items.map((s) => (
        <button
          key={s.id}
          type="button"
          className={primaryActive(s.id) ? 'vxp-nav-btn active' : 'vxp-nav-btn'}
          aria-current={surface === s.id ? 'page' : undefined}
          aria-keyshortcuts={s.shortcut ? `Alt+${s.shortcut}` : undefined}
          onClick={() => go(s.id)}
        >
          <Icon name={s.icon} size={20} />
          <span className="vxp-nav-label">{s.label}</span>
        </button>
      ))}
    </nav>
  )

  return (
    <div
      className={layoutClass}
      style={{ fontSize: `${scale}rem` }}
      role="application"
      aria-label="gunnchOS Complete Experience"
    >
      <header className="cx2-topbar vxp-topbar" role="banner">
        <div className="cx2-brand" aria-label="gunnchOS brand">
          <span className="cx2-brand-mark">gunnchOS</span>
          <span className="cx2-brand-sub">Living Workspace</span>
        </div>
        <div className="vxp-utility" aria-label="Session controls">
          <button
            type="button"
            className={surface === 'search' ? 'vxp-util-btn active' : 'vxp-util-btn'}
            onClick={() => go('search')}
            aria-label="Search / Command"
            data-testid="open-search"
          >
            <Icon name="search" size={18} />
            <span>Search</span>
          </button>
          <button
            type="button"
            className={surface === 'settings' ? 'vxp-util-btn active' : 'vxp-util-btn'}
            onClick={() => openSettings()}
            aria-label="Settings"
            data-testid="open-settings"
          >
            <Icon name="status_ok" size={18} />
            <span>Settings</span>
          </button>
          <button
            type="button"
            className="vxp-util-btn"
            onClick={back}
            aria-label="Back"
            disabled={history.length <= 1}
          >
            <Icon name="back" size={18} />
            <span>Back</span>
          </button>
          <button type="button" className="vxp-util-btn" onClick={home} aria-label="Go to Home">
            <Icon name="home" size={18} />
            <span>Home</span>
          </button>
          {onExit && (
            <button type="button" className="vxp-util-btn" onClick={onExit} aria-label="Exit Complete Experience">
              <Icon name="exit" size={18} />
              <span>Exit</span>
            </button>
          )}
        </div>
      </header>

      <div className="vxp-body">
        {wideLayout && (
          <aside className="vxp-rail" aria-label="Primary navigation rail">
            {navButtons(PRIMARY_NAV, 'Primary')}
            <button
              type="button"
              className={moreActive ? 'vxp-nav-btn active' : 'vxp-nav-btn'}
              aria-expanded={moreOpen}
              aria-controls="vxp-more-panel"
              onClick={() => setMoreOpen((o) => !o)}
            >
              <Icon name="more" size={20} />
              <span className="vxp-nav-label">More</span>
            </button>
            {moreOpen && (
              <div id="vxp-more-panel" className="vxp-more-panel">
                {navButtons(MORE_NAV, 'More surfaces')}
              </div>
            )}
          </aside>
        )}

        <div className="vxp-content">
          {offline && (
            <div className="cx2-banner vxp-banner" role="status">
              <Icon name="offline" size={18} />
              <span>Offline — local work continues; queued actions sync when connectivity returns.</span>
            </div>
          )}
          {error && (
            <div className="cx2-banner error vxp-banner" role="alert">
              <Icon name="error" size={18} />
              <span>{error}</span>
            </div>
          )}
          <main className="cx2-main" id="cx2-main" tabIndex={-1}>
            {body}
          </main>
        </div>
      </div>

      {!wideLayout && (
        <nav className="vxp-dock" aria-label="Primary">
          {PRIMARY_NAV.map((s) => (
            <button
              key={s.id}
              type="button"
              className={primaryActive(s.id) ? 'vxp-dock-btn active' : 'vxp-dock-btn'}
              aria-current={surface === s.id ? 'page' : undefined}
              aria-keyshortcuts={`Alt+${s.shortcut}`}
              onClick={() => go(s.id)}
            >
              <Icon name={s.icon} size={22} />
              <span>{s.label}</span>
            </button>
          ))}
          <button
            type="button"
            className={moreActive ? 'vxp-dock-btn active' : 'vxp-dock-btn'}
            aria-expanded={moreOpen}
            aria-controls="vxp-more-sheet"
            onClick={() => setMoreOpen((o) => !o)}
          >
            <Icon name="more" size={22} />
            <span>More</span>
          </button>
        </nav>
      )}

      {!wideLayout && moreOpen && (
        <div className="vxp-more-sheet" id="vxp-more-sheet" role="dialog" aria-label="More surfaces">
          <div className="vxp-more-sheet-inner">
            <header className="vxp-more-sheet-head">
              <strong>More</strong>
              <button type="button" className="vxp-util-btn" onClick={() => setMoreOpen(false)} aria-label="Close More">
                Close
              </button>
            </header>
            {navButtons(MORE_NAV, 'More surfaces')}
          </div>
        </div>
      )}

      <footer className="cx2-footer" role="contentinfo">
        Profile {profile.replace(/_/g, ' ')}
        {hostKind ? ` · host ${hostKind}` : ''} · Alt+1..0 · ⌘/Ctrl+K search · Escape back
      </footer>
    </div>
  )
}
