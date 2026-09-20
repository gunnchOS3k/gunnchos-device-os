/**
 * Creation domain — local note create/edit/save (Vault-adjacent, shell-owned).
 */

export type CreationDoc = {
  id: string
  title: string
  body: string
  updatedAt: string
}

const KEY = 'gunnchos.capsule.creation.v1'

export function listCreationDocs(): CreationDoc[] {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as CreationDoc[]
    return Array.isArray(parsed) ? parsed.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)) : []
  } catch {
    return []
  }
}

export function saveCreationDoc(doc: Omit<CreationDoc, 'updatedAt'> & { updatedAt?: string }): CreationDoc {
  const next: CreationDoc = {
    ...doc,
    title: doc.title.trim() || 'Untitled note',
    updatedAt: doc.updatedAt || new Date().toISOString(),
  }
  const others = listCreationDocs().filter((d) => d.id !== next.id)
  try {
    localStorage.setItem(KEY, JSON.stringify([next, ...others]))
  } catch {
    // ignore
  }
  return next
}

export function deleteCreationDoc(id: string): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(listCreationDocs().filter((d) => d.id !== id)))
  } catch {
    // ignore
  }
}

export function newCreationId(): string {
  return `note-${Date.now()}`
}
