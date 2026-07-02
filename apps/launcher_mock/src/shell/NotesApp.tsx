import { useMemo, useRef, useState } from 'react'
import { theme } from '../styles/gunnchosTheme'
import AppIcon from '../components/AppIcon'
import {
  Note,
  createNote,
  deleteNote,
  exportNotes,
  importNotes,
  listNotes,
  resetStarterNotes,
  saveNote,
  togglePin,
} from '../services/notesStore'

interface NotesAppProps {
  onBack: () => void
}

export default function NotesApp({ onBack }: NotesAppProps) {
  const [query, setQuery] = useState('')
  const [notes, setNotes] = useState<Note[]>(() => listNotes())
  const [selectedId, setSelectedId] = useState<string | null>(notes[0]?.id ?? null)
  const [title, setTitle] = useState(notes[0]?.title ?? '')
  const [body, setBody] = useState(notes[0]?.body ?? '')
  const [message, setMessage] = useState<string | null>(null)
  const importRef = useRef<HTMLInputElement>(null)

  const selected = useMemo(
    () => notes.find(n => n.id === selectedId),
    [notes, selectedId],
  )

  const refresh = (q = query) => {
    const next = listNotes(q)
    setNotes(next)
    return next
  }

  const showMsg = (text: string) => {
    setMessage(text)
    setTimeout(() => setMessage(null), 2500)
  }

  const selectNote = (note: Note) => {
    setSelectedId(note.id)
    setTitle(note.title)
    setBody(note.body)
  }

  const handleCreate = () => {
    const note = createNote('New Note', '')
    const next = refresh()
    const created = next.find(n => n.id === note.id) ?? note
    selectNote(created)
    showMsg('Note created')
  }

  const handleSave = () => {
    if (!selectedId) return
    const saved = saveNote(selectedId, { title, body })
    refresh()
    setTitle(saved.title)
    setBody(saved.body)
    showMsg('Note saved')
  }

  const handleDelete = () => {
    if (!selectedId) return
    if (!window.confirm('Delete this note?')) return
    deleteNote(selectedId)
    const next = refresh()
    const first = next[0]
    setSelectedId(first?.id ?? null)
    setTitle(first?.title ?? '')
    setBody(first?.body ?? '')
    showMsg('Note deleted')
  }

  const handlePin = () => {
    if (!selectedId) return
    togglePin(selectedId)
    refresh()
    showMsg('Pin updated')
  }

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(exportNotes(), null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'gunnchos-notes.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleImport = (file: File) => {
    const reader = new FileReader()
    reader.onload = () => {
      try {
        importNotes(JSON.parse(String(reader.result)))
        const next = refresh('')
        const first = next[0]
        setSelectedId(first?.id ?? null)
        setTitle(first?.title ?? '')
        setBody(first?.body ?? '')
        showMsg('Notes imported')
      } catch (e) {
        showMsg(e instanceof Error ? e.message : 'Import failed')
      }
    }
    reader.readAsText(file)
  }

  const handleReset = () => {
    if (!window.confirm('Reset to starter notes?')) return
    const next = resetStarterNotes()
    setSelectedId(next[0]?.id ?? null)
    setTitle(next[0]?.title ?? '')
    setBody(next[0]?.body ?? '')
    refresh('')
    showMsg('Starter notes restored')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }} data-testid="notes-app">
      <header style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 24, paddingBottom: 12 }}>
        <button type="button" onClick={onBack} style={backBtn}>
          <AppIcon name="back" size={20} /> Campus
        </button>
        <h1 style={{ margin: 0, fontSize: 22 }}>Notes</h1>
      </header>

      <p style={{ fontSize: 12, color: theme.textMuted, margin: '0 24px 12px' }}>
        Local browser-backed notes prototype · Persists on this device/browser
      </p>

      {message && (
        <div style={{ margin: '0 24px 12px', padding: '8px 12px', background: theme.accentMuted, borderRadius: 8, fontSize: 13 }}>
          {message}
        </div>
      )}

      <div style={{ display: 'flex', flex: 1, minHeight: 0, padding: '0 24px 24px', gap: 16 }}>
        <aside style={sidebar}>
          <input
            type="search"
            placeholder="Search notes..."
            value={query}
            onChange={e => {
              setQuery(e.target.value)
              refresh(e.target.value)
            }}
            data-testid="notes-search"
            style={searchInput}
          />
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
            <button type="button" onClick={handleCreate} style={toolBtn} data-testid="create-note-btn">+ New</button>
            <button type="button" onClick={handleExport} style={toolBtn}>Export</button>
            <button type="button" onClick={() => importRef.current?.click()} style={toolBtn}>Import</button>
            <button type="button" onClick={handleReset} style={toolBtn}>Reset</button>
          </div>
          <input
            ref={importRef}
            type="file"
            accept="application/json"
            style={{ display: 'none' }}
            onChange={e => {
              const f = e.target.files?.[0]
              if (f) handleImport(f)
              e.target.value = ''
            }}
          />
          <div style={{ overflow: 'auto', flex: 1 }}>
            {notes.map(note => (
              <button
                key={note.id}
                type="button"
                onClick={() => selectNote(note)}
                data-testid={`note-item-${note.id}`}
                style={{
                  ...noteItem,
                  borderColor: selectedId === note.id ? theme.accent : theme.border,
                  background: selectedId === note.id ? theme.accentMuted : theme.surfaceRaised,
                }}
              >
                <span style={{ fontWeight: 600 }}>{note.pinned ? '📌 ' : ''}{note.title}</span>
                <span style={{ fontSize: 12, color: theme.textMuted, marginTop: 4 }}>
                  {note.body.slice(0, 60) || 'Empty note'}
                </span>
              </button>
            ))}
          </div>
        </aside>

        <main style={editor}>
          {selected ? (
            <>
              <input
                value={title}
                onChange={e => setTitle(e.target.value)}
                data-testid="note-title-input"
                style={titleInput}
              />
              <textarea
                value={body}
                onChange={e => setBody(e.target.value)}
                data-testid="note-body-input"
                style={bodyInput}
              />
              <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button type="button" onClick={handleSave} style={toolBtn} data-testid="save-note-btn">Save</button>
                <button type="button" onClick={handlePin} style={toolBtn}>
                  {selected.pinned ? 'Unpin' : 'Pin'}
                </button>
                <button type="button" onClick={handleDelete} style={toolBtn}>Delete</button>
              </div>
            </>
          ) : (
            <p style={{ color: theme.textMuted }}>Select or create a note</p>
          )}
        </main>
      </div>
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

const sidebar: React.CSSProperties = {
  width: 280,
  display: 'flex',
  flexDirection: 'column',
  background: theme.surface,
  borderRadius: theme.radius,
  border: `1px solid ${theme.border}`,
  padding: 12,
}

const editor: React.CSSProperties = {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  background: theme.surfaceRaised,
  borderRadius: theme.radius,
  border: `1px solid ${theme.border}`,
  padding: 16,
}

const searchInput: React.CSSProperties = {
  width: '100%',
  padding: '10px 12px',
  marginBottom: 12,
  borderRadius: 8,
  border: `1px solid ${theme.border}`,
  background: theme.bg,
  color: theme.text,
  boxSizing: 'border-box',
}

const toolBtn: React.CSSProperties = {
  padding: '6px 12px',
  borderRadius: 6,
  border: `1px solid ${theme.border}`,
  background: theme.surface,
  color: theme.text,
  cursor: 'pointer',
  fontSize: 13,
}

const noteItem: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'flex-start',
  width: '100%',
  padding: '10px 12px',
  marginBottom: 8,
  borderRadius: 8,
  border: '1px solid',
  cursor: 'pointer',
  textAlign: 'left',
  color: theme.text,
}

const titleInput: React.CSSProperties = {
  width: '100%',
  padding: '10px 12px',
  marginBottom: 12,
  borderRadius: 8,
  border: `1px solid ${theme.border}`,
  background: theme.bg,
  color: theme.text,
  fontSize: 18,
  fontWeight: 600,
  boxSizing: 'border-box',
}

const bodyInput: React.CSSProperties = {
  flex: 1,
  width: '100%',
  minHeight: 280,
  padding: 12,
  borderRadius: 8,
  border: `1px solid ${theme.border}`,
  background: theme.bg,
  color: theme.text,
  fontSize: 14,
  lineHeight: 1.5,
  boxSizing: 'border-box',
  resize: 'vertical',
}
