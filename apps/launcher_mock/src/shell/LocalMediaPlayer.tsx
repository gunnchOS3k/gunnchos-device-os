import { useEffect, useRef, useState } from 'react'
import { theme } from '../styles/gunnchosTheme'
import AppIcon from '../components/AppIcon'
import {
  AUDIO_ACCEPT,
  VIDEO_ACCEPT,
  formatFileSize,
  formatMimeType,
  listRecentMedia,
  rememberMedia,
  type LocalMediaEntry,
} from '../services/localMediaStore'

interface LocalMediaPlayerProps {
  onBack: () => void
}

export default function LocalMediaPlayer({ onBack }: LocalMediaPlayerProps) {
  const [entry, setEntry] = useState<LocalMediaEntry | null>(null)
  const [objectUrl, setObjectUrl] = useState<string | null>(null)
  const [captionsOn, setCaptionsOn] = useState(false)
  const [recent] = useState(() => listRecentMedia())
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [objectUrl])

  const handleFile = (file: File | null) => {
    if (!file) return
    if (objectUrl) URL.revokeObjectURL(objectUrl)
    const url = URL.createObjectURL(file)
    setObjectUrl(url)
    const saved = rememberMedia({
      name: file.name,
      mimeType: file.type || 'application/octet-stream',
      sizeBytes: file.size,
      objectUrl: undefined,
    })
    setEntry(saved)
  }

  const isVideo = entry?.mimeType.startsWith('video/')
  const isAudio = entry?.mimeType.startsWith('audio/')

  return (
    <div style={shell} data-testid="local-media-player">
      <header style={header}>
        <button type="button" onClick={onBack} style={backBtn}>
          <AppIcon name="back" size={18} /> Media Library
        </button>
        <h1 style={{ margin: 0, fontSize: 20 }}>Local Media Player</h1>
      </header>

      <main style={main}>
        <p style={boundary}>
          Local browser-backed media playback prototype. Not a production media library. Streaming DRM not handled here.
        </p>

        <div style={pickerRow}>
          <label style={fileLabel}>
            <input
              ref={fileInputRef}
              type="file"
              accept={`${VIDEO_ACCEPT},${AUDIO_ACCEPT}`}
              data-testid="local-media-file-input"
              onChange={e => handleFile(e.target.files?.[0] ?? null)}
              style={{ display: 'none' }}
            />
            <span style={pickBtn}>Choose audio/video file</span>
          </label>
          <label style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
            <input
              type="checkbox"
              checked={captionsOn}
              onChange={e => setCaptionsOn(e.target.checked)}
              data-testid="captions-toggle"
            />
            Captions placeholder
          </label>
        </div>

        {entry && (
          <div style={metaCard} data-testid="local-media-meta">
            <strong>{entry.name}</strong>
            <span data-testid="local-media-mime">{formatMimeType(entry.mimeType)}</span>
            <span data-testid="local-media-size">{formatFileSize(entry.sizeBytes)}</span>
          </div>
        )}

        {objectUrl && isVideo && (
          <video
            controls
            src={objectUrl}
            data-testid="local-media-video"
            style={player}
          >
            {captionsOn && <track kind="captions" label="Captions placeholder" />}
          </video>
        )}

        {objectUrl && isAudio && (
          <audio controls src={objectUrl} data-testid="local-media-audio" style={{ width: '100%', marginTop: 16 }} />
        )}

        {recent.length > 0 && (
          <section style={{ marginTop: 24 }}>
            <h2 style={{ fontSize: 14, color: theme.textMuted }}>Recently opened (metadata only)</h2>
            <ul style={{ fontSize: 13, color: theme.textMuted }}>
              {recent.map(r => (
                <li key={r.id}>{r.name} — {formatFileSize(r.sizeBytes)}</li>
              ))}
            </ul>
            <p style={{ fontSize: 11, color: theme.textMuted }}>
              File blobs are not persisted — re-select files after refresh unless browser retains access.
            </p>
          </section>
        )}
      </main>
    </div>
  )
}

const shell: React.CSSProperties = {
  minHeight: '100%',
  background: theme.bg,
  color: theme.text,
  fontFamily: theme.font,
}

const header: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 16,
  padding: '16px 24px',
  borderBottom: `1px solid ${theme.border}`,
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

const main: React.CSSProperties = { padding: 24, maxWidth: 720, margin: '0 auto' }

const boundary: React.CSSProperties = {
  fontSize: 13,
  color: theme.warning,
  padding: 12,
  borderRadius: theme.radius,
  border: `1px solid ${theme.warning}`,
  background: `${theme.warning}11`,
}

const pickerRow: React.CSSProperties = { display: 'flex', gap: 16, alignItems: 'center', marginTop: 20, flexWrap: 'wrap' }

const fileLabel: React.CSSProperties = { cursor: 'pointer' }

const pickBtn: React.CSSProperties = {
  display: 'inline-block',
  padding: '12px 20px',
  borderRadius: 10,
  background: theme.accent,
  color: '#000',
  fontWeight: 600,
}

const metaCard: React.CSSProperties = {
  display: 'flex',
  gap: 12,
  flexWrap: 'wrap',
  marginTop: 16,
  padding: 12,
  background: theme.surfaceRaised,
  borderRadius: theme.radius,
  fontSize: 13,
}

const player: React.CSSProperties = {
  width: '100%',
  maxHeight: 400,
  marginTop: 16,
  borderRadius: theme.radius,
  background: '#000',
}
