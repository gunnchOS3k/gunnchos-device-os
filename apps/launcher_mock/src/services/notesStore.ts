/** Browser-backed notes storage prototype — persists in localStorage. */

import {
  isEncryptionEnabled,
  isWorkspaceLocked,
  persistSessionIfPossible,
  readWorkspaceFromSession,
  writeWorkspaceToSession,
} from './encryptedWorkspaceStore'

export const NOTES_STORAGE_KEY = 'gunnchos-notes-v1'

export interface Note {
  id: string
  title: string
  body: string
  pinned: boolean
  modifiedAt: string
  createdAt: string
}

export interface NotesExport {
  version: 1
  exportedAt: string
  notes: Note[]
}

function nowIso(): string {
  return new Date().toISOString()
}

function newId(): string {
  return `note_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
}

function loadRaw(): Note[] {
  if (isEncryptionEnabled()) {
    if (isWorkspaceLocked()) return []
    return readWorkspaceFromSession().notes
  }
  try {
    const raw = localStorage.getItem(NOTES_STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as Note[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function saveRaw(notes: Note[]): void {
  if (isEncryptionEnabled()) {
    if (isWorkspaceLocked()) throw new Error('Workspace is locked')
    writeWorkspaceToSession({ notes })
    void persistSessionIfPossible()
    return
  }
  localStorage.setItem(NOTES_STORAGE_KEY, JSON.stringify(notes))
}

const STARTER_NOTES: Omit<Note, 'id' | 'createdAt' | 'modifiedAt'>[] = [
  {
    title: 'Welcome to GunnchOS',
    body: 'This is your local notes app. Notes persist in browser storage on this device prototype.',
    pinned: true,
  },
  {
    title: 'Class Notes',
    body: 'Capture lecture points, definitions, and questions to ask your professor.',
    pinned: false,
  },
  {
    title: 'Project Ideas',
    body: 'Brainstorm apps, games, STEM builds, and portfolio projects here.',
    pinned: false,
  },
  {
    title: 'Portfolio Checklist',
    body: 'Resume · GitHub repos · demo video · class projects · internship targets',
    pinned: true,
  },
]

export function createStarterNotes(): Note[] {
  const t = nowIso()
  return STARTER_NOTES.map(s => ({
    ...s,
    id: newId(),
    createdAt: t,
    modifiedAt: t,
  }))
}

export function ensureNotesInitialized(): Note[] {
  if (isEncryptionEnabled() && isWorkspaceLocked()) return []
  const existing = loadRaw()
  if (existing.length > 0) return existing
  const starter = createStarterNotes()
  saveRaw(starter)
  return starter
}

export function listNotes(query = ''): Note[] {
  const q = query.trim().toLowerCase()
  const notes = ensureNotesInitialized()
  const filtered = q
    ? notes.filter(
        n => n.title.toLowerCase().includes(q) || n.body.toLowerCase().includes(q),
      )
    : notes
  return filtered.sort((a, b) => {
    if (a.pinned !== b.pinned) return a.pinned ? -1 : 1
    return b.modifiedAt.localeCompare(a.modifiedAt)
  })
}

export function getNote(id: string): Note | undefined {
  return ensureNotesInitialized().find(n => n.id === id)
}

export function createNote(title: string, body = ''): Note {
  const t = nowIso()
  const note: Note = {
    id: newId(),
    title: title.trim() || 'Untitled',
    body,
    pinned: false,
    createdAt: t,
    modifiedAt: t,
  }
  const notes = ensureNotesInitialized()
  notes.push(note)
  saveRaw(notes)
  return note
}

export function saveNote(id: string, updates: Partial<Pick<Note, 'title' | 'body' | 'pinned'>>): Note {
  const notes = ensureNotesInitialized()
  const idx = notes.findIndex(n => n.id === id)
  if (idx < 0) throw new Error('Note not found')
  notes[idx] = {
    ...notes[idx],
    ...updates,
    title: updates.title !== undefined ? (updates.title.trim() || 'Untitled') : notes[idx].title,
    modifiedAt: nowIso(),
  }
  saveRaw(notes)
  return notes[idx]
}

export function deleteNote(id: string): void {
  saveRaw(ensureNotesInitialized().filter(n => n.id !== id))
}

export function togglePin(id: string): Note {
  const note = getNote(id)
  if (!note) throw new Error('Note not found')
  return saveNote(id, { pinned: !note.pinned })
}

export function exportNotes(): NotesExport {
  return {
    version: 1,
    exportedAt: nowIso(),
    notes: ensureNotesInitialized(),
  }
}

export function importNotes(data: NotesExport): void {
  if (!data || data.version !== 1 || !Array.isArray(data.notes)) {
    throw new Error('Invalid notes JSON')
  }
  saveRaw(data.notes)
}

export function resetStarterNotes(): Note[] {
  const starter = createStarterNotes()
  saveRaw(starter)
  return starter
}
