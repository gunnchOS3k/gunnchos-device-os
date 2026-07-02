import { useState } from 'react'
import { theme } from '../styles/gunnchosTheme'
import { GUNNCH_APPS, CAMPUS_DOCK_IDS, getApp, GunnchApp } from '../data/gunnchApps'
import { StudentProfile } from '../data/studentProfile'
import AppIcon from '../components/AppIcon'
import BrowserPwaHub from './BrowserPwaHub'
import FileManager from './FileManager'
import NotesApp from './NotesApp'
import SettingsPanel from './SettingsPanel'
import { DeploymentMode } from '../services/policyEnforcementService'
import { evaluateAppPolicy } from '../services/policyEnforcementService'
import { launchApp } from '../services/appLaunchService'

export type CampusView = 'home' | 'browser' | 'files' | 'notes' | 'settings' | 'app'

interface CampusModeProps {
  profile: StudentProfile
  deploymentMode: DeploymentMode
  onEnterGameMode: () => void
  onEnterMediaMode: () => void
  onResetOnboarding: () => void
}

const HUB_SECTIONS = [
  { title: 'Study & Productivity', categories: ['productivity', 'learning'] as const },
  { title: 'Coding & STEM', categories: ['coding', 'stem'] as const },
  { title: 'AI & Learning', categories: ['ai'] as const },
  { title: 'Creative & Media', categories: ['creative', 'media'] as const },
]

export default function CampusMode({
  profile,
  deploymentMode,
  onEnterGameMode,
  onEnterMediaMode,
  onResetOnboarding,
}: CampusModeProps) {
  const [view, setView] = useState<CampusView>('home')
  const [activeApp, setActiveApp] = useState<GunnchApp | null>(null)
  const [aiPanelOpen, setAiPanelOpen] = useState(false)
  const [policyMessage, setPolicyMessage] = useState<string | null>(null)
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  const openApp = (appId: string) => {
    setPolicyMessage(null)
    const policy = evaluateAppPolicy(appId, deploymentMode, {
      isNativeShellApp: ['files', 'notes', 'browser', 'settings'].includes(appId),
    })
    if (!policy.canLaunch) {
      setPolicyMessage(policy.message)
      return
    }
    if (policy.decision === 'warning_only') {
      setPolicyMessage(policy.message)
    }

    if (appId === 'game-mode') {
      onEnterGameMode()
      return
    }
    if (appId === 'media-mode') {
      onEnterMediaMode()
      return
    }
    if (appId === 'browser') {
      setView('browser')
      return
    }
    if (appId === 'files') {
      setView('files')
      return
    }
    if (appId === 'notes') {
      setView('notes')
      return
    }
    if (appId === 'settings') {
      setView('settings')
      return
    }
    if (appId === 'ai-assistant') {
      setAiPanelOpen(true)
      return
    }
    const app = getApp(appId)
    if (app?.url) {
      const result = launchApp(
        { id: app.id, name: app.name, launchType: 'external_url', url: app.url },
        deploymentMode,
      )
      if (result.status === 'blocked_by_policy') {
        setPolicyMessage(result.message)
        return
      }
      setPolicyMessage(result.warning ?? result.message)
      return
    }
    if (app) {
      setActiveApp(app)
      setView('app')
    }
  }

  const goHome = () => {
    setView('home')
    setActiveApp(null)
    setAiPanelOpen(false)
    setPolicyMessage(null)
  }

  if (view === 'browser') return <BrowserPwaHub onBack={goHome} deploymentMode={deploymentMode} />
  if (view === 'files') return <FileManager onBack={goHome} />
  if (view === 'notes') return <NotesApp onBack={goHome} />
  if (view === 'settings') {
    return (
      <SettingsPanel profile={profile} onBack={goHome} onResetOnboarding={onResetOnboarding} />
    )
  }

  if (view === 'app' && activeApp) {
    return (
      <div style={{ padding: 24 }}>
        <button type="button" onClick={goHome} style={backBtn}>← Campus</button>
        <h1>{activeApp.name}</h1>
        <p style={{ color: theme.textMuted }}>{activeApp.description}</p>
        <p style={{ fontSize: 12, color: theme.textMuted }}>App shell prototype — full integration pending</p>
      </div>
    )
  }

  const dockApps = CAMPUS_DOCK_IDS.map(id => getApp(id)).filter(Boolean) as GunnchApp[]

  return (
    <div style={shell} data-testid="campus-mode">
      {policyMessage && (
        <div data-testid="campus-policy-message" style={policyBanner}>{policyMessage}</div>
      )}
      <header style={header}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24 }}>Hey {profile.displayName || 'Student'}</h1>
          <p style={{ margin: '4px 0 0', color: theme.textMuted, fontSize: 14 }}>
            Campus Mode · {deploymentMode} · {now}
          </p>
        </div>
      </header>

      <nav style={dock} aria-label="Campus dock">
        {dockApps.map(app => (
          <button
            key={app.id}
            type="button"
            aria-label={app.name}
            data-testid={`campus-dock-${app.id}`}
            onClick={() => openApp(app.id)}
            style={dockBtn}
          >
            <AppIcon name={app.icon} size={28} color={theme.accent} />
            <span style={{ fontSize: 11, marginTop: 4 }}>{app.name}</span>
          </button>
        ))}
      </nav>

      <main style={{ padding: '0 24px 24px', flex: 1, overflow: 'auto' }}>
        {HUB_SECTIONS.map(section => (
          <section key={section.title} style={{ marginBottom: 28 }}>
            <h2 style={sectionTitle}>{section.title}</h2>
            <div style={grid}>
              {GUNNCH_APPS.filter(a => section.categories.includes(a.category as never)).map(app => {
                const pol = evaluateAppPolicy(app.id, deploymentMode, { isNativeShellApp: app.level === 'native' })
                return (
                  <button
                    key={app.id}
                    type="button"
                    aria-label={app.name}
                    data-testid={`campus-app-${app.id}`}
                    disabled={!pol.canLaunch}
                    onClick={() => openApp(app.id)}
                    style={{ ...appTile, opacity: pol.canLaunch ? 1 : 0.5 }}
                  >
                    <AppIcon name={app.icon} size={32} color={theme.accent} />
                    <span style={{ fontSize: 13, marginTop: 8 }}>{app.name}</span>
                    {!pol.canLaunch && (
                      <span data-testid={`blocked-${app.id}`} style={{ fontSize: 10, color: theme.danger }}>
                        Blocked
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          </section>
        ))}
      </main>

      {aiPanelOpen && (
        <div style={aiPanel}>
          <p>AI assistant UI shell — no backend in prototype</p>
          <button type="button" onClick={() => setAiPanelOpen(false)}>Close</button>
        </div>
      )}
    </div>
  )
}

const shell: React.CSSProperties = {
  minHeight: '100vh',
  background: theme.bg,
  color: theme.text,
  fontFamily: theme.font,
  display: 'flex',
  flexDirection: 'column',
}

const header: React.CSSProperties = { padding: '20px 24px 12px' }

const policyBanner: React.CSSProperties = {
  padding: '10px 16px',
  background: `${theme.warning}22`,
  borderBottom: `1px solid ${theme.warning}`,
  fontSize: 13,
}

const dock: React.CSSProperties = {
  display: 'flex',
  gap: 8,
  overflowX: 'auto',
  padding: '12px 24px',
  borderBottom: `1px solid ${theme.border}`,
}

const dockBtn: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  minWidth: 72,
  padding: 8,
  border: 'none',
  background: 'transparent',
  color: theme.text,
  cursor: 'pointer',
}

const sectionTitle: React.CSSProperties = {
  fontSize: 14,
  color: theme.textMuted,
  textTransform: 'uppercase',
  letterSpacing: 1,
  margin: '0 0 12px',
}

const grid: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
  gap: 10,
}

const appTile: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: 16,
  borderRadius: theme.radius,
  border: `1px solid ${theme.border}`,
  background: theme.surfaceRaised,
  color: theme.text,
  cursor: 'pointer',
}

const backBtn: React.CSSProperties = {
  marginBottom: 16,
  padding: '8px 12px',
  borderRadius: 8,
  border: `1px solid ${theme.border}`,
  background: theme.surfaceRaised,
  color: theme.text,
  cursor: 'pointer',
}

const aiPanel: React.CSSProperties = {
  position: 'fixed',
  bottom: 24,
  right: 24,
  padding: 16,
  background: theme.surface,
  border: `1px solid ${theme.border}`,
  borderRadius: theme.radius,
}
