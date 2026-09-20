import { useEffect, useState } from 'react'
import type { HostKind } from '../platform/hostRuntime'
import Icon from '../design/icons/Icon'
import type { VxpIconName } from '../design/tokens'
import { listContinuity, type ContinuityItem } from '../platform/continuityStore'
import type { Cx2Surface } from '../shellSurfaces'

const SPACES: { id: Cx2Surface; label: string; purpose: string; icon: VxpIconName }[] = [
  { id: 'waike', label: 'WAIKE', purpose: 'Learning continuity', icon: 'career' },
  { id: 'gunnchai', label: 'gunnchAI', purpose: 'Ask with truthful runtime', icon: 'assist' },
  { id: 'games', label: 'Games', purpose: 'First-party library', icon: 'app_center' },
  { id: 'creation', label: 'Creation', purpose: 'Create and save', icon: 'file' },
  { id: 'connect', label: 'Connect', purpose: 'Mail and calendar locally', icon: 'connect' },
  { id: 'leisure', label: 'Leisure', purpose: 'Rights-safe rest', icon: 'care' },
  { id: 'vault', label: 'Vault', purpose: 'Files you keep and recover', icon: 'vault' },
  { id: 'app_center', label: 'App Library', purpose: 'Install and open tools', icon: 'app_center' },
  { id: 'settings', label: 'Settings', purpose: 'System preferences', icon: 'status_ok' },
  { id: 'search', label: 'Search', purpose: 'Find wired destinations', icon: 'search' },
]

export default function HomeSurface({
  offline,
  onNavigate,
  hostKind,
}: {
  offline?: boolean
  onNavigate: (id: Cx2Surface) => void
  hostKind?: HostKind
}) {
  const [recent, setRecent] = useState<ContinuityItem[]>([])

  useEffect(() => {
    setRecent(listContinuity().slice(0, 6))
  }, [])

  const identityNote =
    hostKind === 'ANDROID_CAPSULE'
      ? 'Running on Capsule'
      : hostKind
        ? `Host: ${hostKind}`
        : 'Browser shell'

  return (
    <section className="cx2-panel vxp-home" aria-labelledby="cx2-home-title">
      <header className="vxp-home-identity">
        <p className="vxp-eyebrow">Living Workspace</p>
        <h1 id="cx2-home-title">gunnchOS</h1>
        <p className="lead">
          Continue real work, open spaces by purpose, and see only status we can prove.
          {offline ? ' Offline mode is on — local work continues.' : ''}
        </p>
        <p className="vxp-identity-meta" data-testid="home-identity-meta">
          {identityNote}
        </p>
      </header>

      <section className="vxp-home-section" aria-labelledby="vxp-continue-title">
        <h2 id="vxp-continue-title">Continue</h2>
        {recent.length === 0 ? (
          <div className="vxp-continue-empty" role="status" data-testid="continue-empty">
            <Icon name="empty" size={24} />
            <div>
              <strong>Nothing to resume yet</strong>
              <p>Open WAIKE, Vault, Games, or Creation when you are ready. We will not invent recent activity.</p>
            </div>
          </div>
        ) : (
          <ul className="vxp-continue-list" aria-label="Continue cards" data-testid="continue-list">
            {recent.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className="vxp-space-card"
                  onClick={() => onNavigate(item.surface as Cx2Surface)}
                >
                  <Icon name="open" size={20} />
                  <span className="vxp-space-label">{item.title}</span>
                  <span className="vxp-space-purpose">
                    {item.subtitle || item.domain} · {new Date(item.updatedAt).toLocaleString()}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="vxp-home-section" aria-labelledby="vxp-spaces-title">
        <h2 id="vxp-spaces-title">Spaces</h2>
        <ul className="vxp-space-grid" aria-label="Spaces by purpose">
          {SPACES.map((s) => (
            <li key={s.id}>
              <button type="button" className="vxp-space-card" onClick={() => onNavigate(s.id)}>
                <Icon name={s.icon} size={22} />
                <span className="vxp-space-label">{s.label}</span>
                <span className="vxp-space-purpose">{s.purpose}</span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="vxp-home-section" aria-labelledby="vxp-status-title">
        <h2 id="vxp-status-title">System status</h2>
        <ul className="vxp-status-list" aria-label="Honest system status">
          <li>
            <Icon name={offline ? 'offline' : 'status_ok'} size={18} />
            <span>{offline ? 'Offline — connectivity not available' : 'Connectivity — host reports a network path'}</span>
          </li>
          <li>
            <Icon name="search" size={18} />
            <span>Search / Command and Settings are system surfaces in the top bar</span>
          </li>
          <li>
            <Icon name="assist" size={18} />
            <span>Accessibility and diagnostics live in Settings — not engineering dump on Home</span>
          </li>
        </ul>
      </section>
    </section>
  )
}
