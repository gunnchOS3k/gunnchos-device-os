/**
 * Local continuity / recent activity — only records real user actions.
 * Cross-device sync remains pending; never invents activity.
 */

export type ContinuityDomain =
  | 'waike'
  | 'vault'
  | 'app'
  | 'game'
  | 'gunnchai'
  | 'creation'
  | 'connect'
  | 'leisure'
  | 'settings'
  | 'search'

export type ContinuityItem = {
  id: string
  domain: ContinuityDomain
  title: string
  subtitle?: string
  surface: string
  payload?: Record<string, unknown>
  updatedAt: string
}

const KEY = 'gunnchos.capsule.continuity.v1'
const MAX = 24

function readAll(): ContinuityItem[] {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as ContinuityItem[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function writeAll(items: ContinuityItem[]): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(items.slice(0, MAX)))
  } catch {
    // ignore quota / private mode
  }
}

export function listContinuity(): ContinuityItem[] {
  return readAll().sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
}

export function recordContinuity(input: Omit<ContinuityItem, 'updatedAt'> & { updatedAt?: string }): ContinuityItem {
  const item: ContinuityItem = {
    ...input,
    updatedAt: input.updatedAt || new Date().toISOString(),
  }
  const next = [item, ...readAll().filter((x) => x.id !== item.id)].slice(0, MAX)
  writeAll(next)
  return item
}

export function clearContinuity(): void {
  writeAll([])
}
