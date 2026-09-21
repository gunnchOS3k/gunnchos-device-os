import { useEffect, useMemo, useState } from 'react'
import Icon from '../design/icons/Icon'
import { SurfaceHeader } from '../design/primitives/SurfaceChrome'
import { resolveAiRuntime } from '../platform/aiRuntime'
import type { HostKind } from '../platform/hostRuntime'
import { feedbackUrlForComponent, SECURITY_MD_URL } from '../platform/feedbackUrls'

const SECTIONS = [
  { id: 'appearance', title: 'Appearance' },
  { id: 'accessibility', title: 'Accessibility' },
  { id: 'connectivity', title: 'Connectivity' },
  { id: 'apps', title: 'Apps' },
  { id: 'storage', title: 'Storage / Vault' },
  { id: 'ai', title: 'AI / Assist' },
  { id: 'learning', title: 'Learning / WAIKE' },
  { id: 'notifications', title: 'Notifications' },
  { id: 'privacy', title: 'Privacy & Permissions' },
  { id: 'capability', title: 'Device / Capability Summary' },
  { id: 'diagnostics', title: 'Developer / Diagnostics' },
  { id: 'about', title: 'About' },
] as const

export type SettingsSectionId = (typeof SECTIONS)[number]['id']

export default function SettingsSurface({
  offline,
  hostKind,
  highContrast,
  reduceMotion,
  scale,
  onHighContrast,
  onReduceMotion,
  onScale,
  onNavigate,
  initialSection,
}: {
  offline?: boolean
  hostKind?: HostKind
  highContrast: boolean
  reduceMotion: boolean
  scale: number
  onHighContrast: (v: boolean) => void
  onReduceMotion: (v: boolean) => void
  onScale: (v: number) => void
  onNavigate: (id: 'app_center' | 'vault' | 'waike' | 'assist' | 'gunnchai') => void
  initialSection?: SettingsSectionId
}) {
  const [query, setQuery] = useState('')
  const [section, setSection] = useState<SettingsSectionId>(initialSection || 'appearance')
  useEffect(() => {
    if (initialSection) setSection(initialSection)
  }, [initialSection])
  const runtime = resolveAiRuntime({ offline, remoteAvailable: !offline, nearbyEdgeAvailable: false })

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return SECTIONS
    return SECTIONS.filter((s) => s.title.toLowerCase().includes(q) || s.id.includes(q))
  }, [query])

  return (
    <section className="cx2-panel vxp-settings" aria-labelledby="cx2-settings-title">
      <SurfaceHeader
        titleId="cx2-settings-title"
        title="Settings"
        lead="System preferences for this device expression of gunnchOS. Search finds wired sections only."
      />

      <div className="vxp-search-row">
        <label htmlFor="settings-search">Search settings</label>
        <input
          id="settings-search"
          className="cx2-field"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search settings"
          data-testid="settings-search"
        />
      </div>

      <div className="vxp-settings-layout">
        <nav className="vxp-settings-nav" aria-label="Settings sections">
          {filtered.map((s) => (
            <button
              key={s.id}
              type="button"
              className={section === s.id ? 'vxp-settings-nav-btn active' : 'vxp-settings-nav-btn'}
              aria-current={section === s.id ? 'page' : undefined}
              onClick={() => setSection(s.id)}
            >
              {s.title}
            </button>
          ))}
        </nav>

        <div className="vxp-settings-body" role="region" aria-label={SECTIONS.find((s) => s.id === section)?.title}>
          {section === 'appearance' && (
            <div className="vxp-assist-list">
              <p className="lead">Living Workspace chrome uses the product tokens. High contrast and scale live under Accessibility.</p>
              <p role="status">Theme: Living Workspace (system default for Capsule).</p>
            </div>
          )}

          {section === 'accessibility' && (
            <div className="vxp-assist-list" role="group" aria-label="Accessibility settings">
              <label className="vxp-assist-row" htmlFor="set-hc">
                <span className="vxp-assist-copy">
                  <Icon name="assist" size={20} />
                  <span>
                    <strong>High contrast</strong>
                    <em>Stronger edges and ink</em>
                  </span>
                </span>
                <input id="set-hc" type="checkbox" checked={highContrast} onChange={(e) => onHighContrast(e.target.checked)} />
              </label>
              <label className="vxp-assist-row" htmlFor="set-rm">
                <span className="vxp-assist-copy">
                  <Icon name="status_warn" size={20} />
                  <span>
                    <strong>Reduce motion</strong>
                    <em>Disable non-essential animation</em>
                  </span>
                </span>
                <input id="set-rm" type="checkbox" checked={reduceMotion} onChange={(e) => onReduceMotion(e.target.checked)} />
              </label>
              <label className="vxp-assist-row" htmlFor="set-scale">
                <span className="vxp-assist-copy">
                  <Icon name="search" size={20} />
                  <span>
                    <strong>UI scale ({scale.toFixed(2)})</strong>
                    <em>Touch targets and type</em>
                  </span>
                </span>
                <input
                  id="set-scale"
                  type="range"
                  min={0.85}
                  max={1.6}
                  step={0.05}
                  value={scale}
                  onChange={(e) => onScale(Number(e.target.value))}
                  aria-label={`UI scale ${scale.toFixed(2)}`}
                />
              </label>
              <button type="button" className="cx2-action" onClick={() => onNavigate('assist')}>
                Open Assist surface
              </button>
            </div>
          )}

          {section === 'connectivity' && (
            <ul className="vxp-status-list">
              <li>
                <Icon name={offline ? 'offline' : 'status_ok'} size={18} />
                <span>{offline ? 'Offline — local work continues' : 'Network path available (browser/host reported)'}</span>
              </li>
              <li>
                <Icon name="status_warn" size={18} />
                <span>Cross-device Continuity sync: pending</span>
              </li>
            </ul>
          )}

          {section === 'apps' && (
            <div>
              <p className="lead">App Library enumerates first-party categories and provider-backed installs when reachable.</p>
              <button type="button" className="cx2-action primary" onClick={() => onNavigate('app_center')}>
                Open App Library
              </button>
            </div>
          )}

          {section === 'storage' && (
            <div>
              <p className="lead">Vault holds recoverable files. Creation notes are stored locally in the shell until Vault export is wired.</p>
              <button type="button" className="cx2-action primary" onClick={() => onNavigate('vault')}>
                Open Vault
              </button>
            </div>
          )}

          {section === 'ai' && (
            <div className="vxp-ai-runtime" data-testid="settings-ai-runtime">
              <p>
                <strong>Active runtime:</strong> {runtime.label}
              </p>
              <p className="lead">{runtime.detail}</p>
              <p className="lead">{runtime.privacy}</p>
              <p role="note">Nearby Mac is never labeled On-device.</p>
              <button type="button" className="cx2-action" onClick={() => onNavigate('gunnchai')}>
                Open gunnchAI
              </button>
            </div>
          )}

          {section === 'learning' && (
            <div>
              <p className="lead">WAIKE is the Learning OS entry. Capsule may host it via adapter (WebView/PWA) when functionally complete.</p>
              <button type="button" className="cx2-action primary" onClick={() => onNavigate('waike')}>
                Open WAIKE
              </button>
            </div>
          )}

          {section === 'notifications' && (
            <p className="lead" role="status">
              Shell notifications are not fully implemented. Android host may surface system notifications separately —
              this Settings section stays honest.
            </p>
          )}

          {section === 'privacy' && (
            <ul className="vxp-status-list">
              <li>
                <Icon name="status_ok" size={18} />
                <span>Bridge capabilities are allowlisted — no arbitrary JS→host calls</span>
              </li>
              <li>
                <Icon name="status_ok" size={18} />
                <span>Camera / microphone require explicit host permission gates</span>
              </li>
              <li>
                <Icon name="assist" size={18} />
                <span>AI prompts follow the runtime privacy note above</span>
              </li>
            </ul>
          )}

          {section === 'capability' && (
            <ul className="vxp-status-list" data-testid="settings-capability">
              <li>
                <Icon name="status_ok" size={18} />
                <span>Host: {hostKind === 'ANDROID_CAPSULE' ? 'Android Capsule' : hostKind || 'browser shell'}</span>
              </li>
              <li>
                <Icon name="status_warn" size={18} />
                <span>Telephony: not claimed as available from this Settings surface</span>
              </li>
              <li>
                <Icon name="status_warn" size={18} />
                <span>Local AI runtime: {runtime.label}</span>
              </li>
              <li>
                <Icon name="offline" size={18} />
                <span>Nearby edge runtime: none paired in this session</span>
              </li>
            </ul>
          )}

          {section === 'diagnostics' && (
            <div className="vxp-diagnostics" data-testid="settings-diagnostics">
              <p className="lead">Engineering metadata belongs here — not on Home.</p>
              <ul className="vxp-status-list">
                <li>
                  <Icon name="status_ok" size={18} />
                  <span>Shell: Complete Experience / Living Workspace</span>
                </li>
                <li>
                  <Icon name="status_ok" size={18} />
                  <span>Host kind code: {hostKind || 'none'}</span>
                </li>
                <li>
                  <Icon name="status_warn" size={18} />
                  <span>HUMAN_A11Y_PENDING — Assist packet still required for a11y PASS</span>
                </li>
                <li>
                  <Icon name="file" size={18} />
                  <span>Parity contract: docs/product/GUNNCHOS_DEVICE_PARITY_CONTRACT.md</span>
                </li>
              </ul>
            </div>
          )}

          {section === 'about' && (
            <div data-testid="settings-about-feedback">
              <h3>gunnchOS</h3>
              <p className="lead">
                Android Capsule is an Android-hosted expression of the same OS — not a companion. Form-factor adapters
                change presentation, not product identity.
              </p>
              <p className="lead">
                <a
                  href={feedbackUrlForComponent('Device OS')}
                  target="_blank"
                  rel="noopener noreferrer"
                  data-testid="feedback-suggestions-link"
                >
                  Feedback &amp; Suggestions
                </a>
                {' · '}
                <a href={SECURITY_MD_URL} target="_blank" rel="noopener noreferrer">
                  Security (private)
                </a>
              </p>
              <p className="lead" role="note">
                Do not post exploitable security details publicly. Links open the public ecosystem hub — no device
                serials, IPs, accounts, or tokens are attached.
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
