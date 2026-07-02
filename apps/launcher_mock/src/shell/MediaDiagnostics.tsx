import { theme } from '../styles/gunnchosTheme'
import { useLauncherContract } from '../hooks/useLauncherContract'

interface MediaDiagnosticsProps {
  playbackProfile: 'battery' | 'balanced' | 'quality'
  captionsEnabled: boolean
  onCaptionsChange: (v: boolean) => void
  onProfileChange: (p: 'battery' | 'balanced' | 'quality') => void
}

const NETWORK_CHECKS = [
  'Wi-Fi connected (mock)',
  'Latency < 50 ms (mock)',
  'Packet loss < 1% (mock)',
  'Bandwidth suitable for HD (mock)',
]

export default function MediaDiagnostics({
  playbackProfile,
  captionsEnabled,
  onCaptionsChange,
  onProfileChange,
}: MediaDiagnosticsProps) {
  const { claim_boundary } = useLauncherContract()

  return (
    <aside style={panel}>
      <h2 style={title}>Playback diagnostics</h2>

      <section style={section}>
        <h3 style={sectionTitle}>Network quality</h3>
        <ul style={list}>
          {NETWORK_CHECKS.map(c => (
            <li key={c} style={listItem}>✓ {c}</li>
          ))}
        </ul>
      </section>

      <section style={section}>
        <h3 style={sectionTitle}>Battery / playback profile</h3>
        <div style={btnRow}>
          {(['battery', 'balanced', 'quality'] as const).map(p => (
            <button
              key={p}
              type="button"
              onClick={() => onProfileChange(p)}
              style={{
                ...profileBtn,
                borderColor: playbackProfile === p ? theme.accent : theme.border,
                background: playbackProfile === p ? theme.accentMuted : theme.surfaceRaised,
              }}
            >
              {p === 'battery' ? 'Battery saver' : p === 'balanced' ? 'Balanced' : 'Best quality'}
            </button>
          ))}
        </div>
      </section>

      <section style={section}>
        <h3 style={sectionTitle}>Audio output</h3>
        <p style={hint}>Speakers · Headphones · Bluetooth (mock)</p>
      </section>

      <section style={section}>
        <label style={toggleLabel}>
          <input
            type="checkbox"
            checked={captionsEnabled}
            onChange={e => onCaptionsChange(e.target.checked)}
          />
          Captions / subtitles preference
        </label>
      </section>

      <section style={section}>
        <h3 style={sectionTitle}>External display</h3>
        <p style={warning}>
          HDCP may be required for external display playback of DRM-protected content.
          Service certification not claimed.
        </p>
      </section>

      <section style={drmBox}>
        <strong>DRM / service boundary</strong>
        <p style={{ margin: '8px 0 0', fontSize: 12, lineHeight: 1.5 }}>{claim_boundary.drm_disclaimer}</p>
        <p style={{ margin: '8px 0 0', fontSize: 11, color: theme.textMuted }}>
          DRM circumvention: {claim_boundary.drm_circumvention_supported ? 'yes' : 'not supported'} ·
          Certification claimed: {claim_boundary.service_certification_claimed ? 'yes' : 'no'}
        </p>
      </section>
    </aside>
  )
}

const panel: React.CSSProperties = {
  padding: 20,
  background: theme.surface,
  borderRadius: theme.radius,
  border: `1px solid ${theme.border}`,
}

const title: React.CSSProperties = { margin: '0 0 16px', fontSize: 16 }

const section: React.CSSProperties = { marginBottom: 16 }

const sectionTitle: React.CSSProperties = {
  margin: '0 0 8px',
  fontSize: 12,
  color: theme.textMuted,
  textTransform: 'uppercase',
  letterSpacing: 0.5,
}

const list: React.CSSProperties = { margin: 0, paddingLeft: 18, fontSize: 13 }

const listItem: React.CSSProperties = { marginBottom: 4, color: theme.textMuted }

const btnRow: React.CSSProperties = { display: 'flex', flexWrap: 'wrap', gap: 6 }

const profileBtn: React.CSSProperties = {
  padding: '6px 10px',
  borderRadius: 20,
  border: '1px solid',
  background: theme.surfaceRaised,
  color: theme.text,
  fontSize: 12,
  cursor: 'pointer',
}

const hint: React.CSSProperties = { margin: 0, fontSize: 13, color: theme.textMuted }

const toggleLabel: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 8,
  fontSize: 13,
  cursor: 'pointer',
}

const warning: React.CSSProperties = {
  margin: 0,
  fontSize: 12,
  color: theme.warning,
  lineHeight: 1.5,
}

const drmBox: React.CSSProperties = {
  padding: 12,
  borderRadius: 8,
  background: theme.surfaceRaised,
  border: `1px solid ${theme.border}`,
  fontSize: 13,
}
