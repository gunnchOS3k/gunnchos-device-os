import { useState } from 'react'
import { theme } from '../styles/gunnchosTheme'
import { PWA_TARGETS } from '../data/pwaTargets'
import AppIcon from '../components/AppIcon'
import { launchApp, pwaTargetToLaunchTarget, type AppLaunchResult } from '../services/appLaunchService'

interface BrowserPwaHubProps {
  onBack: () => void
  deploymentMode?: string
}

export default function BrowserPwaHub({ onBack, deploymentMode = 'Media' }: BrowserPwaHubProps) {
  const [query, setQuery] = useState('')
  const [lastResult, setLastResult] = useState<AppLaunchResult | null>(null)

  const filtered = PWA_TARGETS.filter(t =>
    !query || t.name.toLowerCase().includes(query.toLowerCase()) || t.category.toLowerCase().includes(query.toLowerCase()),
  )

  const pinned = filtered.filter(t => t.pinned)
  const rest = filtered.filter(t => !t.pinned)
  const categories = [...new Set(rest.map(t => t.category))]

  const openTarget = (id: string) => {
    const target = PWA_TARGETS.find(t => t.id === id)
    if (!target) return
    const result = launchApp(pwaTargetToLaunchTarget(target), deploymentMode)
    setLastResult(result)
  }

  return (
    <div style={{ padding: 24, height: '100%', overflow: 'auto' }} data-testid="browser-pwa-hub">
      <header style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <button type="button" onClick={onBack} style={backBtn}>
          <AppIcon name="back" size={20} /> Campus
        </button>
        <h1 style={{ margin: 0, fontSize: 22 }}>Browser & PWA Hub</h1>
      </header>

      <p style={{ fontSize: 13, color: theme.textMuted, margin: '0 0 16px' }}>
        Opens real web apps in a new browser tab. Not a production browser shell — external browser route prototype.
      </p>

      {lastResult && (
        <div
          data-testid="launch-result"
          style={{
            marginBottom: 16,
            padding: 12,
            borderRadius: theme.radius,
            border: `1px solid ${lastResult.status === 'launched' ? theme.accent : theme.warning}`,
            background: theme.surfaceRaised,
            fontSize: 13,
          }}
        >
          <strong>{lastResult.status.replace(/_/g, ' ')}</strong>
          <p style={{ margin: '4px 0 0', color: theme.textMuted }}>{lastResult.message}</p>
          {lastResult.openedUrl?.startsWith('http') && (
            <a href={lastResult.openedUrl} target="_blank" rel="noreferrer" style={{ color: theme.accent }}>
              Open link ↗
            </a>
          )}
        </div>
      )}

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
  items: { id: string; name: string; url: string }[]
  onOpen: (id: string) => void
}) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10 }}>
      {items.map(item => (
        <button
          key={item.id}
          type="button"
          data-testid={`pwa-launch-${item.id}`}
          onClick={() => onOpen(item.id)}
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
