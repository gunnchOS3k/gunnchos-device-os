import { useState } from 'react'
import { theme } from '../styles/gunnchosTheme'
import { GUNNCH_APPS, CAMPUS_DOCK_IDS, getApp, GunnchApp } from '../data/gunnchApps'
import { StudentProfile } from '../data/studentProfile'
import AppIcon from '../components/AppIcon'
import BrowserPwaHub from './BrowserPwaHub'
import FileManager from './FileManager'
import NotesApp from './NotesApp'
import SettingsPanel from './SettingsPanel'

export type CampusView = 'home' | 'browser' | 'files' | 'notes' | 'settings' | 'app'

interface CampusModeProps {
  profile: StudentProfile
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

export default function CampusMode({ profile, onEnterGameMode, onEnterMediaMode, onResetOnboarding }: CampusModeProps) {
  const [view, setView] = useState<CampusView>('home')
  const [activeApp, setActiveApp] = useState<GunnchApp | null>(null)
  const [aiPanelOpen, setAiPanelOpen] = useState(false)
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  const openApp = (appId: string) => {
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
    if (app) {
      setActiveApp(app)
      setView('app')
    }
  }

  const goHome = () => {
    setView('home')
    setActiveApp(null)
    setAiPanelOpen(false)
  }

  if (view === 'browser') return <BrowserPwaHub onBack={goHome} />
  if (view === 'files') return <FileManager onBack={goHome} />
  if (view === 'notes') return <NotesApp onBack={goHome} />
  if (view === 'settings') {
    return (
      <SettingsPanel profile={profile} onBack={goHome} onResetOnboarding={onResetOnboarding} />
    )
  }

  if (view === 'app' && activeApp) {
    return <AppPlaceholder app={activeApp} onBack={goHome} />
  }

  const dockApps = CAMPUS_DOCK_IDS.map(id => getApp(id)).filter(Boolean) as GunnchApp[]

  return (
    <div style={shell}>
      <header style={topBar}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={logoMark}>G</div>
          <div>
            <div style={{ fontWeight: 600 }}>GunnchOS</div>
            <div style={{ fontSize: 12, color: theme.textMuted }}>Campus Mode</div>
          </div>
        </div>
        <div style={{ fontSize: 14, color: theme.textMuted }}>{now}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {profile.offline && <span style={offlineBadge}>Offline</span>}
          <button type="button" onClick={() => setAiPanelOpen(v => !v)} style={aiBtn} aria-label="AI assistant">
            <AppIcon name="ai" size={20} color={theme.accent} />
          </button>
          <span style={{ fontSize: 13 }}>{profile.displayName}</span>
          <AppIcon name="user" size={22} color={theme.textMuted} />
        </div>
      </header>

      <main style={main}>
        <section style={welcome}>
          <h1 style={{ margin: 0, fontSize: 26 }}>
            Hey {profile.displayName.split(' ')[0]} 👋
          </h1>
          <p style={{ color: theme.textMuted, margin: '6px 0 0' }}>
            Your device for school, code, creativity, and games.
          </p>
        </section>

        <section style={quickRow}>
          {['browser', 'drive', 'd2l', 'vscode-web', 'notebooklm', 'github'].map(id => {
            const app = getApp(id)
            if (!app) return null
            return (
              <button key={id} type="button" onClick={() => openApp(id)} style={quickTile}>
                <AppIcon name={app.icon} size={28} color={theme.accent} />
                <span style={{ fontSize: 12, marginTop: 6 }}>{app.name}</span>
              </button>
            )
          })}
        </section>

        {HUB_SECTIONS.map(section => {
          const apps = GUNNCH_APPS.filter(a =>
            section.categories.includes(a.category as typeof section.categories[number]) &&
            !['browser', 'files', 'settings', 'game-mode'].includes(a.id),
          )
          if (!apps.length) return null
          return (
            <section key={section.title} style={{ marginBottom: 24 }}>
              <h2 style={sectionTitle}>{section.title}</h2>
              <div style={appGrid}>
                {apps.map(app => (
                  <AppTile key={app.id} app={app} onOpen={() => openApp(app.id)} />
                ))}
              </div>
            </section>
          )
        })}
      </main>

      <nav style={dock} aria-label="Dock">
        {dockApps.map(app => (
          <button
            key={app.id}
            type="button"
            onClick={() => openApp(app.id)}
            style={dockBtn}
            aria-label={app.name}
          >
            <AppIcon name={app.icon} size={24} color={app.id === 'game-mode' ? theme.gameAccent : theme.accent} />
            <span style={{ fontSize: 10, marginTop: 4 }}>{app.name.split(' ')[0]}</span>
          </button>
        ))}
      </nav>

      {aiPanelOpen && (
        <aside style={aiPanel}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <strong>GunnchAI Study Assistant</strong>
            <button type="button" onClick={() => setAiPanelOpen(false)} style={{ background: 'none', border: 'none', color: theme.textMuted, cursor: 'pointer', fontSize: 18 }}>×</button>
          </div>
          <p style={{ fontSize: 14, color: theme.textMuted, lineHeight: 1.5 }}>
            Explain assignments · Summarize notes · Quiz you · Debug code · Create flashcards · Voice & camera input
          </p>
          <div style={aiSuggestions}>
            {['Explain this assignment', 'Quiz me on Chapter 5', 'Debug my Python code', 'Make flashcards from my notes'].map(q => (
              <button key={q} type="button" style={aiChip}>{q}</button>
            ))}
          </div>
          <input type="text" placeholder="Ask anything..." style={aiInput} />
          <p style={{ fontSize: 11, color: theme.textMuted, marginTop: 8 }}>Privacy mode on · Student data not used for training</p>
        </aside>
      )}
    </div>
  )
}

function AppTile({ app, onOpen }: { app: GunnchApp; onOpen: () => void }) {
  return (
    <button type="button" onClick={onOpen} style={tile}>
      <AppIcon name={app.icon} size={32} color={theme.accent} />
      <div style={{ textAlign: 'left', flex: 1 }}>
        <div style={{ fontWeight: 500, fontSize: 14 }}>{app.name}</div>
        <div style={{ fontSize: 12, color: theme.textMuted }}>{app.description}</div>
        <span style={levelBadge(app.level)}>{app.level}</span>
      </div>
    </button>
  )
}

function AppPlaceholder({ app, onBack }: { app: GunnchApp; onBack: () => void }) {
  return (
    <div style={{ padding: 24, minHeight: '100vh', background: theme.bg, color: theme.text, fontFamily: theme.font }}>
      <button type="button" onClick={onBack} style={backBtn}>
        <AppIcon name="back" size={20} /> Campus
      </button>
      <div style={{ maxWidth: 480, margin: '40px auto', textAlign: 'center' }}>
        <AppIcon name={app.icon} size={56} color={theme.accent} />
        <h1 style={{ margin: '16px 0 8px' }}>{app.name}</h1>
        <p style={{ color: theme.textMuted }}>{app.description}</p>
        <span style={{ ...levelBadge(app.level), marginTop: 12, display: 'inline-block' }}>{app.level} app</span>
        {app.url && (
          <a href={app.url} target="_blank" rel="noreferrer" style={{ display: 'block', marginTop: 20, color: theme.accent }}>
            Open web target ↗
          </a>
        )}
        <p style={{ fontSize: 13, color: theme.textMuted, marginTop: 24 }}>
          Phase {app.level === 'linux' ? '2' : '1'} deliverable — mock shell in Phase 0
        </p>
      </div>
    </div>
  )
}

function levelBadge(level: string): React.CSSProperties {
  const colors: Record<string, string> = { native: theme.success, pwa: theme.accent, linux: theme.warning, android: theme.gameAccent }
  return {
    display: 'inline-block',
    marginTop: 4,
    padding: '2px 8px',
    borderRadius: 4,
    fontSize: 10,
    textTransform: 'uppercase',
    background: `${colors[level] ?? theme.border}33`,
    color: colors[level] ?? theme.textMuted,
  }
}

const shell: React.CSSProperties = {
  minHeight: '100vh',
  background: theme.bg,
  color: theme.text,
  fontFamily: theme.font,
  display: 'flex',
  flexDirection: 'column',
  position: 'relative',
}

const topBar: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '10px 20px',
  background: theme.surface,
  borderBottom: `1px solid ${theme.border}`,
}

const logoMark: React.CSSProperties = {
  width: 36,
  height: 36,
  borderRadius: 10,
  background: `linear-gradient(135deg, ${theme.accent}, ${theme.gameAccent})`,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontWeight: 700,
  color: '#fff',
}

const main: React.CSSProperties = {
  flex: 1,
  padding: '20px 24px 80px',
  overflow: 'auto',
}

const welcome: React.CSSProperties = { marginBottom: 20 }

const quickRow: React.CSSProperties = {
  display: 'flex',
  gap: 10,
  overflowX: 'auto',
  paddingBottom: 8,
  marginBottom: 24,
}

const quickTile: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: '12px 16px',
  minWidth: 80,
  borderRadius: theme.radius,
  border: `1px solid ${theme.border}`,
  background: theme.surfaceRaised,
  color: theme.text,
  cursor: 'pointer',
  flexShrink: 0,
}

const sectionTitle: React.CSSProperties = {
  fontSize: 13,
  color: theme.textMuted,
  textTransform: 'uppercase',
  letterSpacing: 1,
  margin: '0 0 10px',
}

const appGrid: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
  gap: 10,
}

const tile: React.CSSProperties = {
  display: 'flex',
  alignItems: 'flex-start',
  gap: 14,
  padding: 14,
  borderRadius: theme.radius,
  border: `1px solid ${theme.border}`,
  background: theme.surfaceRaised,
  color: theme.text,
  cursor: 'pointer',
  textAlign: 'left',
  minHeight: theme.touchMin,
}

const dock: React.CSSProperties = {
  position: 'fixed',
  bottom: 0,
  left: 0,
  right: 0,
  display: 'flex',
  justifyContent: 'center',
  gap: 4,
  padding: '8px 12px',
  background: `${theme.surface}ee`,
  backdropFilter: 'blur(12px)',
  borderTop: `1px solid ${theme.border}`,
}

const dockBtn: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: '8px 12px',
  minWidth: 56,
  border: 'none',
  background: 'transparent',
  color: theme.text,
  cursor: 'pointer',
}

const offlineBadge: React.CSSProperties = {
  padding: '4px 10px',
  borderRadius: 20,
  fontSize: 12,
  background: `${theme.warning}33`,
  color: theme.warning,
}

const aiBtn: React.CSSProperties = {
  padding: 8,
  borderRadius: 8,
  border: `1px solid ${theme.border}`,
  background: theme.surfaceRaised,
  cursor: 'pointer',
  display: 'flex',
}

const aiPanel: React.CSSProperties = {
  position: 'fixed',
  top: 56,
  right: 16,
  width: 320,
  maxHeight: 'calc(100vh - 120px)',
  padding: 20,
  background: theme.surface,
  borderRadius: 16,
  border: `1px solid ${theme.border}`,
  boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
  zIndex: 100,
  overflow: 'auto',
}

const aiSuggestions: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: 8,
  margin: '16px 0',
}

const aiChip: React.CSSProperties = {
  padding: '10px 12px',
  borderRadius: 8,
  border: `1px solid ${theme.border}`,
  background: theme.surfaceRaised,
  color: theme.text,
  cursor: 'pointer',
  textAlign: 'left',
  fontSize: 13,
}

const aiInput: React.CSSProperties = {
  width: '100%',
  padding: '12px 14px',
  borderRadius: theme.radius,
  border: `1px solid ${theme.border}`,
  background: theme.surfaceRaised,
  color: theme.text,
  fontSize: 14,
  boxSizing: 'border-box',
}

const backBtn: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 6,
  padding: '8px 12px',
  borderRadius: 8,
  border: `1px solid ${theme.border}`,
  background: theme.surfaceRaised,
  color: theme.text,
  cursor: 'pointer',
}
