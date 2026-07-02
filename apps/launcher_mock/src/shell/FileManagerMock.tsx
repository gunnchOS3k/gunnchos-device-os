import { useState } from 'react'
import { theme } from '../styles/gunnchosTheme'
import AppIcon from '../components/AppIcon'

interface FileEntry {
  name: string
  type: 'folder' | 'file'
  size?: string
  modified?: string
  icon: string
}

const MOCK_FILES: Record<string, FileEntry[]> = {
  '/': [
    { name: 'Downloads', type: 'folder', modified: 'Today', icon: 'folder' },
    { name: 'Offline Documents', type: 'folder', modified: 'Yesterday', icon: 'folder' },
    { name: 'Code Projects', type: 'folder', modified: 'Mar 28', icon: 'folder' },
    { name: 'STEM Labs', type: 'folder', modified: 'Mar 25', icon: 'folder' },
    { name: 'Creative Work', type: 'folder', modified: 'Mar 20', icon: 'folder' },
    { name: 'USB Drive (mock)', type: 'folder', modified: '—', icon: 'folder' },
  ],
  '/Downloads': [
    { name: 'syllabus_fall2026.pdf', type: 'file', size: '1.2 MB', modified: 'Today', icon: 'pdf' },
    { name: 'lab_report_draft.docx', type: 'file', size: '340 KB', modified: 'Today', icon: 'docs' },
    { name: 'lecture_recording.mp4', type: 'file', size: '128 MB', modified: 'Yesterday', icon: 'video' },
  ],
  '/Offline Documents': [
    { name: 'Research Notes', type: 'folder', modified: 'Mar 28', icon: 'folder' },
    { name: 'essay_final.gdoc', type: 'file', size: 'Offline copy', modified: 'Mar 27', icon: 'docs' },
    { name: 'study_guide_chemistry.pdf', type: 'file', size: '2.1 MB', modified: 'Mar 26', icon: 'pdf' },
  ],
  '/Code Projects': [
    { name: 'intro-python', type: 'folder', modified: 'Mar 28', icon: 'folder' },
    { name: 'portfolio-site', type: 'folder', modified: 'Mar 22', icon: 'folder' },
    { name: 'arduino-sensor-lab', type: 'folder', modified: 'Mar 18', icon: 'folder' },
  ],
}

interface FileManagerMockProps {
  onBack: () => void
}

export default function FileManagerMock({ onBack }: FileManagerMockProps) {
  const [path, setPath] = useState('/')
  const entries = MOCK_FILES[path] ?? []

  const navigate = (name: string, type: string) => {
    if (type !== 'folder') return
    const next = path === '/' ? `/${name}` : `${path}/${name}`
    if (MOCK_FILES[next] || next.startsWith('/Downloads') || next.startsWith('/Offline') || next.startsWith('/Code')) {
      setPath(next in MOCK_FILES ? next : path)
    }
  }

  const goUp = () => {
    if (path === '/') return
    const parts = path.split('/').filter(Boolean)
    parts.pop()
    setPath(parts.length ? `/${parts.join('/')}` : '/')
  }

  return (
    <div style={{ padding: 24, height: '100%', overflow: 'auto' }}>
      <header style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <button type="button" onClick={onBack} style={backBtn}>
          <AppIcon name="back" size={20} /> Campus
        </button>
        <h1 style={{ margin: 0, fontSize: 22 }}>Files</h1>
      </header>

      <div style={toolbar}>
        {path !== '/' && (
          <button type="button" onClick={goUp} style={toolBtn}>↑ Up</button>
        )}
        <span style={{ color: theme.textMuted, fontSize: 14 }}>{path}</span>
        <span style={{ marginLeft: 'auto', fontSize: 13, color: theme.success }}>● Offline-ready</span>
      </div>

      <div style={listHeader}>
        <span>Name</span>
        <span>Modified</span>
        <span>Size</span>
      </div>

      {entries.map(entry => (
        <button
          key={entry.name}
          type="button"
          onClick={() => navigate(entry.name, entry.type)}
          style={row}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <AppIcon name={entry.icon} size={22} color={entry.type === 'folder' ? theme.accent : theme.textMuted} />
            {entry.name}
          </span>
          <span style={{ color: theme.textMuted }}>{entry.modified}</span>
          <span style={{ color: theme.textMuted }}>{entry.size ?? '—'}</span>
        </button>
      ))}

      {entries.length === 0 && (
        <p style={{ color: theme.textMuted, textAlign: 'center', marginTop: 40 }}>Empty folder</p>
      )}
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

const toolbar: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 12,
  padding: '10px 14px',
  background: theme.surfaceRaised,
  borderRadius: theme.radius,
  marginBottom: 12,
}

const toolBtn: React.CSSProperties = {
  padding: '6px 12px',
  borderRadius: 6,
  border: `1px solid ${theme.border}`,
  background: theme.surface,
  color: theme.text,
  cursor: 'pointer',
}

const listHeader: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 100px 80px',
  padding: '8px 14px',
  fontSize: 12,
  color: theme.textMuted,
  textTransform: 'uppercase',
  letterSpacing: 0.5,
}

const row: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 100px 80px',
  width: '100%',
  padding: '12px 14px',
  border: 'none',
  borderBottom: `1px solid ${theme.border}`,
  background: 'transparent',
  color: theme.text,
  cursor: 'pointer',
  textAlign: 'left',
  fontSize: 14,
}
