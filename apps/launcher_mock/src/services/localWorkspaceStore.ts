/** Browser-backed local workspace storage prototype — not a production OS filesystem. */

export const WORKSPACE_STORAGE_KEY = 'gunnchos-workspace-v1'
export const WORKSPACE_CLAIM = 'local browser-backed workspace storage prototype'

export interface WorkspaceNode {
  id: string
  name: string
  type: 'folder' | 'file'
  parentId: string | null
  content?: string
  modifiedAt: string
}

export interface WorkspaceExport {
  version: 1
  claim: typeof WORKSPACE_CLAIM
  exportedAt: string
  nodes: WorkspaceNode[]
}

const DEFAULT_FOLDER_NAMES = [
  'Downloads',
  'Offline Docs',
  'Code Projects',
  'Notes',
  'Media',
  'Portfolio',
] as const

function nowIso(): string {
  return new Date().toISOString()
}

function newId(): string {
  return `ws_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
}

function loadRaw(): WorkspaceNode[] {
  try {
    const raw = localStorage.getItem(WORKSPACE_STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as WorkspaceNode[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function saveRaw(nodes: WorkspaceNode[]): void {
  localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify(nodes))
}

export function createDemoWorkspace(): WorkspaceNode[] {
  const t = nowIso()
  return DEFAULT_FOLDER_NAMES.map(name => ({
    id: newId(),
    name,
    type: 'folder' as const,
    parentId: null,
    modifiedAt: t,
  }))
}

export function ensureWorkspaceInitialized(): WorkspaceNode[] {
  const existing = loadRaw()
  if (existing.length > 0) return existing
  const demo = createDemoWorkspace()
  saveRaw(demo)
  return demo
}

export function getAllNodes(): WorkspaceNode[] {
  return ensureWorkspaceInitialized()
}

export function getChildren(parentId: string | null): WorkspaceNode[] {
  return getAllNodes()
    .filter(n => n.parentId === parentId)
    .sort((a, b) => {
      if (a.type !== b.type) return a.type === 'folder' ? -1 : 1
      return a.name.localeCompare(b.name)
    })
}

export function getNode(id: string): WorkspaceNode | undefined {
  return getAllNodes().find(n => n.id === id)
}

export function getPath(nodeId: string): WorkspaceNode[] {
  const path: WorkspaceNode[] = []
  let current = getNode(nodeId)
  while (current) {
    path.unshift(current)
    current = current.parentId ? getNode(current.parentId) : undefined
  }
  return path
}

function nameExists(parentId: string | null, name: string, excludeId?: string): boolean {
  return getChildren(parentId).some(
    n => n.name.toLowerCase() === name.toLowerCase() && n.id !== excludeId,
  )
}

export function createFolder(parentId: string | null, name: string): WorkspaceNode {
  const trimmed = name.trim()
  if (!trimmed) throw new Error('Folder name required')
  if (nameExists(parentId, trimmed)) throw new Error('Name already exists')
  const node: WorkspaceNode = {
    id: newId(),
    name: trimmed,
    type: 'folder',
    parentId,
    modifiedAt: nowIso(),
  }
  const nodes = getAllNodes()
  nodes.push(node)
  saveRaw(nodes)
  return node
}

export function createFile(parentId: string | null, name: string, content = ''): WorkspaceNode {
  const trimmed = name.trim()
  if (!trimmed) throw new Error('File name required')
  if (nameExists(parentId, trimmed)) throw new Error('Name already exists')
  const node: WorkspaceNode = {
    id: newId(),
    name: trimmed,
    type: 'file',
    parentId,
    content,
    modifiedAt: nowIso(),
  }
  const nodes = getAllNodes()
  nodes.push(node)
  saveRaw(nodes)
  return node
}

export function renameNode(id: string, newName: string): WorkspaceNode {
  const trimmed = newName.trim()
  if (!trimmed) throw new Error('Name required')
  const nodes = getAllNodes()
  const idx = nodes.findIndex(n => n.id === id)
  if (idx < 0) throw new Error('Node not found')
  const node = nodes[idx]
  if (nameExists(node.parentId, trimmed, id)) throw new Error('Name already exists')
  nodes[idx] = { ...node, name: trimmed, modifiedAt: nowIso() }
  saveRaw(nodes)
  return nodes[idx]
}

export function deleteNode(id: string): void {
  const nodes = getAllNodes()
  const toDelete = new Set<string>()
  const collect = (nodeId: string) => {
    toDelete.add(nodeId)
    nodes.filter(n => n.parentId === nodeId).forEach(c => collect(c.id))
  }
  collect(id)
  saveRaw(nodes.filter(n => !toDelete.has(n.id)))
}

export function saveFileContent(id: string, content: string): WorkspaceNode {
  const nodes = getAllNodes()
  const idx = nodes.findIndex(n => n.id === id)
  if (idx < 0) throw new Error('File not found')
  if (nodes[idx].type !== 'file') throw new Error('Not a file')
  nodes[idx] = { ...nodes[idx], content, modifiedAt: nowIso() }
  saveRaw(nodes)
  return nodes[idx]
}

export function loadFileContent(id: string): string {
  const node = getNode(id)
  if (!node || node.type !== 'file') throw new Error('File not found')
  return node.content ?? ''
}

export function exportWorkspace(): WorkspaceExport {
  return {
    version: 1,
    claim: WORKSPACE_CLAIM,
    exportedAt: nowIso(),
    nodes: getAllNodes(),
  }
}

export function importWorkspace(data: WorkspaceExport): void {
  if (!data || data.version !== 1 || !Array.isArray(data.nodes)) {
    throw new Error('Invalid workspace JSON')
  }
  saveRaw(data.nodes)
}

export function resetDemoWorkspace(): WorkspaceNode[] {
  const demo = createDemoWorkspace()
  saveRaw(demo)
  return demo
}

export function formatSize(content?: string): string {
  if (content === undefined) return '—'
  const bytes = new TextEncoder().encode(content).length
  if (bytes < 1024) return `${bytes} B`
  return `${(bytes / 1024).toFixed(1)} KB`
}

export function formatModified(iso: string): string {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}
