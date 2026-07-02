import { describe, it, expect, beforeEach } from 'vitest'
import {
  WORKSPACE_STORAGE_KEY,
  createDemoWorkspace,
  createFile,
  createFolder,
  exportWorkspace,
  getChildren,
  loadFileContent,
  resetDemoWorkspace,
  saveFileContent,
} from '../services/localWorkspaceStore'
import {
  NOTES_STORAGE_KEY,
  createNote,
  listNotes,
  resetStarterNotes,
  saveNote,
} from '../services/notesStore'

describe('localWorkspaceStore', () => {
  beforeEach(() => {
    localStorage.removeItem(WORKSPACE_STORAGE_KEY)
    resetDemoWorkspace()
  })

  it('creates demo folders', () => {
    const roots = getChildren(null)
    expect(roots.some(n => n.name === 'Downloads')).toBe(true)
    expect(roots.some(n => n.name === 'Notes')).toBe(true)
  })

  it('creates folder and text file', () => {
    const folder = createFolder(null, 'Test Folder')
    const file = createFile(folder.id, 'hello.txt', 'hi')
    expect(getChildren(folder.id).map(n => n.name)).toContain('hello.txt')
    expect(loadFileContent(file.id)).toBe('hi')
  })

  it('saves and reloads text content', () => {
    const file = createFile(null, 'draft.txt', 'v1')
    saveFileContent(file.id, 'v2')
    expect(loadFileContent(file.id)).toBe('v2')
  })

  it('exports workspace JSON', () => {
    const data = exportWorkspace()
    expect(data.version).toBe(1)
    expect(data.nodes.length).toBeGreaterThan(0)
    expect(data.claim).toMatch(/prototype/i)
  })
})

describe('notesStore', () => {
  beforeEach(() => {
    localStorage.removeItem(NOTES_STORAGE_KEY)
    resetStarterNotes()
  })

  it('creates starter notes', () => {
    const notes = listNotes()
    expect(notes.some(n => n.title === 'Welcome to GunnchOS')).toBe(true)
  })

  it('creates and saves a note', () => {
    const note = createNote('Test Note', 'body')
    saveNote(note.id, { body: 'updated body' })
    const found = listNotes().find(n => n.id === note.id)
    expect(found?.body).toBe('updated body')
  })
})
