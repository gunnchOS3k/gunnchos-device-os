import { useMemo, useRef, useState } from 'react'
import { theme } from '../styles/gunnchosTheme'
import AppIcon from '../components/AppIcon'
import {
  WORKSPACE_CLAIM,
  WorkspaceNode,
  createFile,
  createFolder,
  deleteNode,
  exportWorkspace,
  formatModified,
  formatSize,
  getChildren,
  getNode,
  getPath,
  importWorkspace,
  loadFileContent,
  renameNode,
  resetDemoWorkspace,
  saveFileContent,
} from '../services/localWorkspaceStore'

interface FileManagerProps {
  onBack: () => void
}

export default function FileManager({ onBack }: FileManagerProps) {
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null)
  const [nodes, setNodes] = useState<WorkspaceNode[]>(() => getChildren(null))
  const [openFileId, setOpenFileId] = useState<string | null>(null)
  const [editorContent, setEditorContent] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const importRef = useRef<HTMLInputElement>(null)

  const path = useMemo(
    () => (currentFolderId ? getPath(currentFolderId) : []),
    [currentFolderId, nodes],
  )

  const refresh = (folderId: string | null = currentFolderId) => {
    setNodes(getChildren(folderId))
  }

  const showMsg = (text: string) => {
    setMessage(text)
    setTimeout(() => setMessage(null), 2500)
  }

  const handleCreateFolder = () => {
    const name = window.prompt('New folder name')
    if (!name) return
    try {
      createFolder(currentFolderId, name)
      refresh()
      showMsg('Folder created')
    } catch (e) {
      showMsg(e instanceof Error ? e.message : 'Could not create folder')
    }
  }

  const handleCreateFile = () => {
    const name = window.prompt('New text file name', 'untitled.txt')
    if (!name) return
    try {
      createFile(currentFolderId, name, '')
      refresh()
      showMsg('File created')
    } catch (e) {
      showMsg(e instanceof Error ? e.message : 'Could not create file')
    }
  }

  const handleRename = (node: WorkspaceNode) => {
    const name = window.prompt('Rename', node.name)
    if (!name || name === node.name) return
    try {
      renameNode(node.id, name)
      refresh()
      showMsg('Renamed')
    } catch (e) {
      showMsg(e instanceof Error ? e.message : 'Could not rename')
    }
  }

  const handleDelete = (node: WorkspaceNode) => {
    if (!window.confirm(`Delete "${node.name}"?`)) return
    deleteNode(node.id)
    if (openFileId === node.id) {
      setOpenFileId(null)
      setEditorContent('')
    }
    refresh()
    showMsg('Deleted')
  }

  const openFile = (node: WorkspaceNode) => {
    setOpenFileId(node.id)
    setEditorContent(loadFileContent(node.id))
  }

  const saveOpenFile = () => {
    if (!openFileId) return
    saveFileContent(openFileId, editorContent)
    refresh()
    showMsg('Saved')
  }

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(exportWorkspace(), null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'gunnchos-workspace.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleImport = (file: File) => {
    const reader = new FileReader()
    reader.onload = () => {
      try {
        importWorkspace(JSON.parse(String(reader.result)))
        setCurrentFolderId(null)
        setOpenFileId(null)
        refresh(null)
        showMsg('Workspace imported')
      } catch (e) {
        showMsg(e instanceof Error ? e.message : 'Import failed')
      }
    }
    reader.readAsText(file)
  }

  const handleReset = () => {
    if (!window.confirm('Reset to demo workspace? This replaces all files.')) return
    resetDemoWorkspace()
    setCurrentFolderId(null)
    setOpenFileId(null)
    refresh(null)
    showMsg('Demo workspace restored')
  }

  const openFileNode = openFileId ? getNode(openFileId) : undefined

  return (
    <div style={{ padding: 24, height: '100%', overflow: 'auto' }} data-testid="file-manager">
      <header style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <button type="button" onClick={onBack} style={backBtn}>
          <AppIcon name="back" size={20} /> Campus
        </button>
        <h1 style={{ margin: 0, fontSize: 22 }}>Files</h1>
      </header>

      <p style={{ fontSize: 12, color: theme.textMuted, margin: '0 0 12px' }}>
        {WORKSPACE_CLAIM} · Not encrypted OS storage
      </p>

      {message && (
        <div style={{ padding: '8px 12px', marginBottom: 12, background: theme.accentMuted, borderRadius: 8, fontSize: 13 }}>
          {message}
        </div>
      )}

      <div style={toolbar}>
        {currentFolderId && (
          <button
            type="button"
            onClick={() => {
              const parent = getNode(currentFolderId)?.parentId ?? null
              setCurrentFolderId(parent)
              refresh(parent)
            }}
            style={toolBtn}
          >
            ↑ Up
          </button>
        )}
        <span style={{ color: theme.textMuted, fontSize: 14 }}>
          /{path.map(p => p.name).join('/') || ''}
        </span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button type="button" onClick={handleCreateFolder} style={toolBtn} data-testid="create-folder-btn">+ Folder</button>
          <button type="button" onClick={handleCreateFile} style={toolBtn} data-testid="create-file-btn">+ File</button>
          <button type="button" onClick={handleExport} style={toolBtn} data-testid="export-workspace-btn">Export</button>
          <button type="button" onClick={() => importRef.current?.click()} style={toolBtn}>Import</button>
          <button type="button" onClick={handleReset} style={toolBtn}>Reset demo</button>
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
      </div>

      {openFileNode ? (
        <div style={editorPanel}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <strong>{openFileNode.name}</strong>
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="button" onClick={saveOpenFile} style={toolBtn} data-testid="save-file-btn">Save</button>
              <button type="button" onClick={() => setOpenFileId(null)} style={toolBtn}>Close</button>
            </div>
          </div>
          <textarea
            value={editorContent}
            onChange={e => setEditorContent(e.target.value)}
            data-testid="file-editor"
            style={textarea}
          />
        </div>
      ) : (
        <>
          <div style={listHeader}>
            <span>Name</span>
            <span>Modified</span>
            <span>Size</span>
            <span>Actions</span>
          </div>
          {nodes.map(entry => (
            <div key={entry.id} style={row} data-testid={`entry-${entry.name}`}>
              <button
                type="button"
                onClick={() => {
                  if (entry.type === 'folder') {
                    setCurrentFolderId(entry.id)
                    refresh(entry.id)
                  } else {
                    openFile(entry)
                  }
                }}
                style={nameBtn}
              >
                <AppIcon
                  name={entry.type === 'folder' ? 'folder' : 'notes'}
                  size={22}
                  color={entry.type === 'folder' ? theme.accent : theme.textMuted}
                />
                {entry.name}
              </button>
              <span style={{ color: theme.textMuted, fontSize: 13 }}>{formatModified(entry.modifiedAt)}</span>
              <span style={{ color: theme.textMuted, fontSize: 13 }}>
                {entry.type === 'file' ? formatSize(entry.content) : '—'}
              </span>
              <span style={{ display: 'flex', gap: 6 }}>
                <button type="button" onClick={() => handleRename(entry)} style={miniBtn}>Rename</button>
                <button type="button" onClick={() => handleDelete(entry)} style={miniBtn}>Delete</button>
              </span>
            </div>
          ))}
          {nodes.length === 0 && (
            <p style={{ color: theme.textMuted, textAlign: 'center', marginTop: 40 }}>Empty folder</p>
          )}
        </>
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
  flexWrap: 'wrap',
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

const miniBtn: React.CSSProperties = { ...toolBtn, padding: '4px 8px', fontSize: 12 }

const listHeader: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 140px 80px 140px',
  padding: '8px 14px',
  fontSize: 12,
  color: theme.textMuted,
  textTransform: 'uppercase',
  letterSpacing: 0.5,
}

const row: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 140px 80px 140px',
  alignItems: 'center',
  padding: '8px 14px',
  borderBottom: `1px solid ${theme.border}`,
  fontSize: 14,
}

const nameBtn: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 10,
  border: 'none',
  background: 'transparent',
  color: theme.text,
  cursor: 'pointer',
  textAlign: 'left',
  padding: 0,
}

const editorPanel: React.CSSProperties = {
  marginTop: 12,
  padding: 16,
  background: theme.surfaceRaised,
  borderRadius: theme.radius,
  border: `1px solid ${theme.border}`,
}

const textarea: React.CSSProperties = {
  width: '100%',
  minHeight: 240,
  padding: 12,
  borderRadius: 8,
  border: `1px solid ${theme.border}`,
  background: theme.bg,
  color: theme.text,
  fontFamily: 'monospace',
  fontSize: 14,
  boxSizing: 'border-box',
}
