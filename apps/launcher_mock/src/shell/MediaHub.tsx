import { theme } from '../styles/gunnchosTheme'
import { MediaAppMeta } from '../hooks/useLauncherContract'
import AppIcon from '../components/AppIcon'

interface MediaHubProps {
  apps: MediaAppMeta[]
  activeMode: string
  onOpen: (app: MediaAppMeta) => void
}

const CATEGORY_LABELS: Record<string, string> = {
  video_streaming: 'Video streaming',
  education_video: 'Education video',
  music_audio: 'Music & audio',
  local_media: 'Local media',
}

export default function MediaHub({ apps, activeMode, onOpen }: MediaHubProps) {
  const categories = [...new Set(apps.map(a => a.category))]

  return (
    <div>
      <p style={{ color: theme.textMuted, fontSize: 14, margin: '0 0 16px' }}>
        Touch-friendly · Controller: D-pad + A to select · Keyboard: Tab + Enter
      </p>
      {categories.map(cat => (
        <section key={cat} style={{ marginBottom: 24 }}>
          <h2 style={catTitle}>{CATEGORY_LABELS[cat] ?? cat}</h2>
          <div style={grid}>
            {apps.filter(a => a.category === cat).map(app => (
              <MediaCard key={app.id} app={app} mode={activeMode} onOpen={() => onOpen(app)} />
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}

function MediaCard({
  app,
  mode,
  onOpen,
}: {
  app: MediaAppMeta
  mode: string
  onOpen: () => void
}) {
  const blocked =
    (mode === 'School' && app.school_mode_default === 'blocked') ||
    (mode === 'Offline' && app.requires_network && !app.offline_supported)

  return (
    <button
      type="button"
      onClick={onOpen}
      disabled={blocked}
      aria-label={`${app.name}${blocked ? ' (blocked in current mode)' : ''}`}
      data-testid={`media-card-${app.id}`}
      style={{
        ...card,
        opacity: blocked ? 0.5 : 1,
        cursor: blocked ? 'not-allowed' : 'pointer',
      }}
    >
      <AppIcon name={iconFor(app.id)} size={36} color={theme.accent} />
      <div style={{ flex: 1, textAlign: 'left' }}>
        <div style={{ fontWeight: 600, fontSize: 15 }}>{app.name}</div>
        <div style={{ fontSize: 11, color: theme.textMuted, marginTop: 2 }}>
          {claimLabel(app.claim_status)}
        </div>
        {app.requires_drm && (
          <div data-testid={`drm-warning-${app.id}`} style={drmBadge}>
            DRM/CDM required · HDCP may apply
          </div>
        )}
        {blocked && <div style={blockedBadge}>Blocked in {mode} Mode</div>}
      </div>
    </button>
  )
}

function iconFor(id: string): string {
  const map: Record<string, string> = {
    youtube: 'video',
    netflix: 'video',
    hulu: 'video',
    local_media: 'folder',
    lecture_video: 'video',
    music_audio: 'mic',
    future_streaming_service: 'cloud',
  }
  return map[id] ?? 'video'
}

function claimLabel(status: string): string {
  const labels: Record<string, string> = {
    browser_route_prototype: 'Browser route prototype',
    local_placeholder: 'Local placeholder',
    future_placeholder: 'Future route',
  }
  return labels[status] ?? status
}

const catTitle: React.CSSProperties = {
  fontSize: 13,
  color: theme.textMuted,
  textTransform: 'uppercase',
  letterSpacing: 1,
  margin: '0 0 10px',
}

const grid: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
  gap: 10,
}

const card: React.CSSProperties = {
  display: 'flex',
  alignItems: 'flex-start',
  gap: 14,
  padding: 16,
  borderRadius: theme.radius,
  border: `1px solid ${theme.border}`,
  background: theme.surfaceRaised,
  color: theme.text,
  minHeight: theme.touchMin,
  width: '100%',
}

const drmBadge: React.CSSProperties = {
  marginTop: 6,
  padding: '4px 8px',
  borderRadius: 6,
  fontSize: 10,
  background: `${theme.warning}22`,
  color: theme.warning,
  display: 'inline-block',
}

const blockedBadge: React.CSSProperties = {
  marginTop: 4,
  fontSize: 10,
  color: theme.danger,
}
