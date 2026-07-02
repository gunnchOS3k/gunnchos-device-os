import { useState } from 'react'
import { theme } from '../styles/gunnchosTheme'
import { PWA_TARGETS } from '../data/pwaTargets'
import AppIcon from '../components/AppIcon'

interface BrowserPwaHubProps {
  onBack: () => void
}

export default function BrowserPwaHub({ onBack }: BrowserPwaHubProps) {
  const [query, setQuery] = useState('')
  const [activeUrl, setActiveUrl] = useState<string | null>(null)
  const [activeTitle, setActiveTitle] = useState('')

  const filtered = PWA_TARGETS.filter(t =>
    !query || t.name.toLowerCase().includes(query.toLowerCase()) || t.category.toLowerCase().includes(query.toLowerCase()),
  )

  const pinned = filtered.filter(t => t.pinned)
  const rest = filtered.filter(t => !t.pinned)
  const categories = [...new Set(rest.map(t => t.category))]

  const openTarget = (name: string, url: string) => {
    setActiveTitle(name)
    setActiveUrl(url)
  }

  if (activeUrl) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <header style={header}>
          <button type="button" onClick={() => setActiveUrl(null)} style={backBtn}>
            <AppIcon name="back" size={20} /> Back
          </button>
          <span style={{ fontWeight: 600 }}>{activeTitle}</span>
          <span style={{ fontSize: 12, color: theme.textMuted }}>PWA · Mock frame</span>
        </header>
        <div style={browserFrame}>
          <div style={urlBar}>{activeUrl}</div>
          <div style={mockPage}>
            <AppIcon name="browser" size={48} color={theme.accent} />
            <h2 style={{ margin: '16px 0 8px' }}>{activeTitle}</h2>
            <p style={{ color: theme.textMuted, maxWidth: 400, textAlign: 'center' }}>
              In production, this loads the real web app in a Chrome-compatible browser shell.
              Phase 0 mock — no live iframe for security in dev.
            </p>
            <a href={activeUrl} target="_blank" rel="noreferrer" style={extLink}>
              Open in new tab ↗
            </a>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: 24, height: '100%', overflow: 'auto' }}>
      <header style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <button type="button" onClick={onBack} style={backBtn}>
          <AppIcon name="back" size={20} /> Campus
        </button>
        <h1 style={{ margin: 0, fontSize: 22 }}>Browser & PWA Hub</h1>
      </header>

      <div style={searchWrap}>
        <AppIcon name="search" size={20} color={theme.textMuted} />
        <input
          type="search"
          placeholder="Search apps and sites..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          style={searchInput}
        />
      </div>

      <Section title="Pinned for school">
        <AppGrid items={pinned} onOpen={openTarget} />
      </Section>

      {categories.map(cat => (
        <Section key={cat} title={cat}>
          <AppGrid items={rest.filter(t => t.category === cat)} onOpen={openTarget} />
        </Section>
      ))}
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginBottom: 28 }}>
      <h2 style={{ fontSize: 14, color: theme.textMuted, textTransform: 'uppercase', letterSpacing: 1, margin: '0 0 12px' }}>
        {title}
      </h2>
      {children}
    </section>
  )
}

function AppGrid({
  items,
  onOpen,
}: {
  items: { name: string; url: string }[]
  onOpen: (name: string, url: string) => void
}) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10 }}>
      {items.map(item => (
        <button
          key={item.name}
          type="button"
          onClick={() => onOpen(item.name, item.url)}
          style={tile}
        >
          <AppIcon name="browser" size={32} color={theme.accent} />
          <span style={{ fontSize: 13, marginTop: 8 }}>{item.name}</span>
        </button>
      ))}
    </div>
  )
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

const header: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 16,
  padding: '12px 16px',
  borderBottom: `1px solid ${theme.border}`,
  background: theme.surface,
}

const browserFrame: React.CSSProperties = { flex: 1, display: 'flex', flexDirection: 'column' }

const urlBar: React.CSSProperties = {
  padding: '8px 16px',
  background: theme.surfaceRaised,
  fontSize: 13,
  color: theme.textMuted,
  borderBottom: `1px solid ${theme.border}`,
}

const mockPage: React.CSSProperties = {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: 32,
  background: theme.bg,
}

const extLink: React.CSSProperties = {
  marginTop: 16,
  color: theme.accent,
  textDecoration: 'none',
  fontWeight: 600,
}

const searchWrap: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 10,
  padding: '10px 14px',
  background: theme.surfaceRaised,
  borderRadius: theme.radius,
  border: `1px solid ${theme.border}`,
  marginBottom: 24,
}

const searchInput: React.CSSProperties = {
  flex: 1,
  border: 'none',
  background: 'transparent',
  color: theme.text,
  fontSize: 16,
  outline: 'none',
}

const tile: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: 16,
  minHeight: theme.touchMin + 24,
  borderRadius: theme.radius,
  border: `1px solid ${theme.border}`,
  background: theme.surfaceRaised,
  color: theme.text,
  cursor: 'pointer',
}
