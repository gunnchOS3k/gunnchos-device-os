import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import FileManager from './FileManager'
import NotesApp from './NotesApp'
import CampusMode from './CampusMode'
import { DEFAULT_PROFILE } from '../data/studentProfile'
import { WORKSPACE_STORAGE_KEY, resetDemoWorkspace } from '../services/localWorkspaceStore'
import { NOTES_STORAGE_KEY, resetStarterNotes, listNotes } from '../services/notesStore'

const onboardedProfile = {
  ...DEFAULT_PROFILE,
  displayName: 'Test Student',
  onboarded: true,
}

describe('FileManager v1', () => {
  beforeEach(() => {
    localStorage.removeItem(WORKSPACE_STORAGE_KEY)
    resetDemoWorkspace()
  })

  it('renders file manager', () => {
    render(<FileManager onBack={() => {}} />)
    expect(screen.getByTestId('file-manager')).toBeInTheDocument()
    expect(screen.getByText(/browser-backed workspace storage prototype/i)).toBeInTheDocument()
  })

  it('creates a folder', () => {
    vi.stubGlobal('prompt', () => 'My Folder')
    render(<FileManager onBack={() => {}} />)
    fireEvent.click(screen.getByTestId('create-folder-btn'))
    expect(screen.getByTestId('entry-My Folder')).toBeInTheDocument()
    vi.unstubAllGlobals()
  })

  it('creates and edits a text file', () => {
    vi.stubGlobal('prompt', (msg: string, def?: string) => (msg.includes('file') ? 'edit-me.txt' : def))
    render(<FileManager onBack={() => {}} />)
    fireEvent.click(screen.getByTestId('create-file-btn'))
    fireEvent.click(screen.getByText('edit-me.txt'))
    const editor = screen.getByTestId('file-editor') as HTMLTextAreaElement
    fireEvent.change(editor, { target: { value: 'Hello workspace' } })
    fireEvent.click(screen.getByTestId('save-file-btn'))
    expect(editor.value).toBe('Hello workspace')
    vi.unstubAllGlobals()
  })

  it('exports workspace JSON', () => {
    render(<FileManager onBack={() => {}} />)
    expect(screen.getByTestId('export-workspace-btn')).toBeInTheDocument()
  })
})

describe('NotesApp v1', () => {
  beforeEach(() => {
    localStorage.removeItem(NOTES_STORAGE_KEY)
    resetStarterNotes()
  })

  it('renders notes app', () => {
    render(<NotesApp onBack={() => {}} />)
    expect(screen.getByTestId('notes-app')).toBeInTheDocument()
  })

  it('creates and saves a note', () => {
    render(<NotesApp onBack={() => {}} />)
    fireEvent.click(screen.getByTestId('create-note-btn'))
    fireEvent.change(screen.getByTestId('note-title-input'), { target: { value: 'Chem Lab' } })
    fireEvent.change(screen.getByTestId('note-body-input'), { target: { value: 'Titration steps' } })
    fireEvent.click(screen.getByTestId('save-note-btn'))
    expect(screen.getByDisplayValue('Chem Lab')).toBeInTheDocument()
  })

  it('persists notes after reload', () => {
    const { unmount } = render(<NotesApp onBack={() => {}} />)
    fireEvent.click(screen.getByTestId('create-note-btn'))
    fireEvent.change(screen.getByTestId('note-title-input'), { target: { value: 'Persist Me' } })
    fireEvent.click(screen.getByTestId('save-note-btn'))
    unmount()
    expect(listNotes().some(n => n.title === 'Persist Me')).toBe(true)
    render(<NotesApp onBack={() => {}} />)
    fireEvent.click(screen.getAllByText('Persist Me')[0])
    expect(screen.getByDisplayValue('Persist Me')).toBeInTheDocument()
  })
})

describe('CampusMode workspace apps', () => {
  beforeEach(() => {
    localStorage.setItem('gunnchos-profile', JSON.stringify(onboardedProfile))
    localStorage.removeItem(WORKSPACE_STORAGE_KEY)
    localStorage.removeItem(NOTES_STORAGE_KEY)
    resetDemoWorkspace()
    resetStarterNotes()
  })

  it('opens File Manager from dock', () => {
    render(
      <CampusMode
        profile={onboardedProfile}
        deploymentMode="Media"
        onEnterGameMode={() => {}}
        onEnterMediaMode={() => {}}
        onResetOnboarding={() => {}}
      />,
    )
    fireEvent.click(screen.getByTestId('campus-dock-files'))
    expect(screen.getByTestId('file-manager')).toBeInTheDocument()
  })

  it('opens Notes from dock', () => {
    render(
      <CampusMode
        profile={onboardedProfile}
        deploymentMode="Media"
        onEnterGameMode={() => {}}
        onEnterMediaMode={() => {}}
        onResetOnboarding={() => {}}
      />,
    )
    fireEvent.click(screen.getByTestId('campus-dock-notes'))
    expect(screen.getByTestId('notes-app')).toBeInTheDocument()
  })
})
