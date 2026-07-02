import { useState } from 'react'
import { theme } from '../styles/gunnchosTheme'
import { getMediaApps, getModePolicy, useLauncherContract, MediaAppMeta } from '../hooks/useLauncherContract'
import AppIcon from '../components/AppIcon'
import MediaHub from './MediaHub'
import MediaDiagnostics from './MediaDiagnostics'
import LocalMediaPlayer from './LocalMediaPlayer'

interface MediaModeProps {
  onExit: () => void
  deploymentMode?: string
}

export default function MediaMode({ onExit, deploymentMode = 'Media' }: MediaModeProps) {
  const contract = useLauncherContract()
  const mediaApps = getMediaApps()
  const modePolicy = getModePolicy(deploymentMode)
  const [selected, setSelected] = useState<MediaAppMeta | null>(null)
  const [showLocalPlayer, setShowLocalPlayer] = useState(false)
  const [playbackProfile, setPlaybackProfile] = useState<'battery' | 'balanced' | 'quality'>('balanced')
  const [captionsEnabled, setCaptionsEnabled] = useState(false)
  const [launchMessage, setLaunchMessage] = useState<string | null>(null)

  const openApp = (app: MediaAppMeta) => {
    if (app.launch_type === 'local_media' || app.id === 'local_media' || app.id === 'lecture_video') {
      setShowLocalPlayer(true)
      setSelected(null)
      return
    }
    setSelected(app)
    setLaunchMessage(null)
  }

  if (showLocalPlayer) {
    return (
      <div style={shell} data-testid="media-mode">
        <LocalMediaPlayer onBack={() => setShowLocalPlayer(false)} />
        <button type="button" onClick={onExit} style={{ ...exitBtn, margin: 16 }}>Exit Media Mode</button>
      </div>
    )
  }

  if (selected) {
    const isHttp = selected.route_url.startsWith('http')
    const handleOpen = () => {
      if (isHttp) {
        window.open(selected.route_url, '_blank', 'noopener,noreferrer')
        setLaunchMessage(`Opened ${selected.name} in a new browser tab`)
      }
    }

    return (
      <div style={shell} data-testid="media-mode-detail">
        <header style={header}>
          <button type="button" onClick={() => setSelected(null)} style={backBtn}>
            <AppIcon name="back" size={18} /> Library
          </button>
          <h1 style={{ margin: 0, fontSize: 20 }}>{selected.name}</h1>
          <button type="button" onClick={onExit} style={exitBtn}>Exit Media Mode</button>
        </header>
        <main style={detailMain}>
          <div style={detailCard}>
            <AppIcon name="video" size={48} color={theme.accent} />
            <p style={{ color: theme.textMuted, maxWidth: 480, textAlign: 'center', lineHeight: 1.6 }}>
              {selected.notes}
            </p>
            <div style={metaRow}>
              <span style={tag}>{selected.claim_status.replace(/_/g, ' ')}</span>
              {selected.requires_drm && (
                <span data-testid="drm-detail-warning" style={{ ...tag, color: theme.warning }}>
                  DRM/CDM support required
                </span>
              )}
            </div>
            {isHttp ? (
              <>
                <button type="button" onClick={handleOpen} style={launchBtn} data-testid="media-open-browser">
                  Open in browser/PWA ↗
                </button>
                {launchMessage && <p style={{ fontSize: 12, color: theme.textMuted }}>{launchMessage}</p>}
              </>
            ) : (
              <button type="button" style={launchBtn} onClick={() => setShowLocalPlayer(true)} data-testid="media-open-local">
                Open Local Media Player
              </button>
            )}
            <p style={{ fontSize: 12, color: theme.textMuted }}>
              Service certification not claimed · No DRM circumvention
            </p>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div style={shell} data-testid="media-mode">
      <header style={header}>
        <div>
          <h1 style={{ margin: 0, fontSize: 26, color: theme.accent }}>Media Mode</h1>
          <p style={{ margin: '4px 0 0', color: theme.textMuted, fontSize: 13 }}>
            Streaming · lectures · local media · touch & controller navigation
          </p>
        </div>
        <button type="button" onClick={onExit} style={exitBtn}>Exit to Campus</button>
      </header>

      <RestrictionsSummary mode={deploymentMode} policy={modePolicy} contract={contract} />

      <div style={content}>
        <div style={{ flex: 1 }}>
          <MediaHub apps={mediaApps} activeMode={deploymentMode} onOpen={openApp} />
        </div>
        <MediaDiagnostics
          playbackProfile={playbackProfile}
          captionsEnabled={captionsEnabled}
          onCaptionsChange={setCaptionsEnabled}
          onProfileChange={setPlaybackProfile}
        />
      </div>
    </div>
  )
}

function RestrictionsSummary({
  mode,
  policy,
  contract,
}: {
  mode: string
  policy: ReturnType<typeof getModePolicy>
  contract: ReturnType<typeof useLauncherContract>
}) {
  const items: string[] = []
  if (mode === 'School') {
    items.push('Netflix and Hulu blocked by default in School Mode')
    items.push('YouTube allowed only if school policy permits')
  }
  if (mode === 'Guardian') {
    items.push('Streaming services age-gated under Guardian Mode')
  }
  if (mode === 'Library' || policy?.library_login_warning) {
    items.push('Library Mode: personal login warning — no saved passwords by default')
  }
  if (mode === 'Offline') {
    items.push('Offline Mode: streaming unavailable; local media and downloaded lectures allowed')
  }
  items.push(contract.claim_boundary.drm_disclaimer)

  return (
    <div data-testid="restrictions-summary" style={restrictions}>
      <strong>Active context: {mode}</strong>
      <ul style={{ margin: '8px 0 0', paddingLeft: 18, fontSize: 12, color: theme.textMuted }}>
        {items.map(i => <li key={i}>{i}</li>)}
      </ul>
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

const header: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '16px 24px',
  borderBottom: `1px solid ${theme.border}`,
  background: theme.surface,
  flexWrap: 'wrap',
  gap: 12,
}

const exitBtn: React.CSSProperties = {
  padding: '10px 16px',
  borderRadius: 8,
  border: `1px solid ${theme.border}`,
  background: theme.surfaceRaised,
  color: theme.text,
  cursor: 'pointer',
}

const backBtn: React.CSSProperties = { ...exitBtn, display: 'flex', alignItems: 'center', gap: 6 }

const restrictions: React.CSSProperties = {
  padding: '12px 24px',
  background: `${theme.accentMuted}`,
  borderBottom: `1px solid ${theme.border}`,
  fontSize: 13,
}

const content: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 300px',
  gap: 20,
  padding: 24,
  flex: 1,
}

const detailMain: React.CSSProperties = {
  flex: 1,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: 32,
}

const detailCard: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: 12,
  padding: 32,
  maxWidth: 520,
  background: theme.surface,
  borderRadius: 16,
  border: `1px solid ${theme.border}`,
}

const metaRow: React.CSSProperties = { display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center' }

const tag: React.CSSProperties = {
  padding: '4px 10px',
  borderRadius: 20,
  fontSize: 11,
  background: theme.surfaceRaised,
  border: `1px solid ${theme.border}`,
  textTransform: 'capitalize',
}

const launchBtn: React.CSSProperties = {
  marginTop: 8,
  padding: '12px 24px',
  borderRadius: 10,
  background: theme.accent,
  color: '#000',
  fontWeight: 600,
  border: 'none',
  cursor: 'pointer',
  fontSize: 14,
}
