import type { Cx2Surface } from '../CompleteExperienceShell'
import type { HostKind } from '../platform/hostRuntime'
import Icon from '../design/icons/Icon'
import type { VxpIconName } from '../design/tokens'

const SPACES: { id: Cx2Surface; label: string; purpose: string; icon: VxpIconName }[] = [
  { id: 'vault', label: 'Vault', purpose: 'Files you keep and recover', icon: 'vault' },
  { id: 'app_center', label: 'App Center', purpose: 'Install and open tools', icon: 'app_center' },
  { id: 'connect', label: 'Connect', purpose: 'Mail and calendar locally', icon: 'connect' },
  { id: 'wallet', label: 'Wallet', purpose: 'Credentials you control', icon: 'wallet' },
  { id: 'portfolio', label: 'Portfolio', purpose: 'Evidence you can share', icon: 'portfolio' },
  { id: 'career', label: 'Career', purpose: 'Profile and pathways', icon: 'career' },
  { id: 'verifier', label: 'Verifier', purpose: 'Check claims honestly', icon: 'verifier' },
  { id: 'assist', label: 'Assist', purpose: 'Contrast, motion, scale', icon: 'assist' },
  { id: 'care', label: 'Care', purpose: 'Backups and recovery', icon: 'care' },
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
          Continue your work, open a space by purpose, and see only status we can prove.
          {offline ? ' Offline mode is on — local work continues.' : ''}
        </p>
        <p className="vxp-identity-meta" data-testid="home-identity-meta">
          {identityNote}
        </p>
      </header>

      <section className="vxp-home-section" aria-labelledby="vxp-continue-title">
        <h2 id="vxp-continue-title">Continue</h2>
        <div className="vxp-continue-empty" role="status">
          <Icon name="empty" size={24} />
          <div>
            <strong>Nothing to resume yet</strong>
            <p>Open Vault or App Center when you are ready. We will not invent recent activity.</p>
          </div>
        </div>
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
            <span>{offline ? 'Offline — connectivity not available' : 'Connectivity — browser reports online'}</span>
          </li>
          <li>
            <Icon name="status_warn" size={18} />
            <span>Canonical logo asset pending intake</span>
          </li>
          <li>
            <Icon name="assist" size={18} />
            <span>Accessibility: open Assist for contrast, motion, and scale</span>
          </li>
        </ul>
        <p className="vxp-discover">
          Tip: use the dock (or side rail) for Home, Vault, App Center, and Connect. More holds Assist, Care, Wallet,
          Portfolio, Career, and Verifier.
        </p>
      </section>
    </section>
  )
}
