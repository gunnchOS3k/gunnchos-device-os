/**
 * Search / Command index — only wired destinations and commands.
 */

import { FIRST_PARTY_LIBRARY } from './appLibraryCatalog'
import type { Cx2Surface } from '../shellSurfaces'

export type SearchHit = {
  id: string
  title: string
  detail: string
  kind: 'surface' | 'library' | 'command' | 'setting'
  surface: Cx2Surface
  settingSection?: string
}

const SURFACE_HITS: SearchHit[] = [
  { id: 'surf-home', title: 'Home', detail: 'Continue and spaces', kind: 'surface', surface: 'home' },
  { id: 'surf-search', title: 'Search / Command', detail: 'Find wired destinations', kind: 'surface', surface: 'search' },
  { id: 'surf-settings', title: 'Settings', detail: 'System preferences', kind: 'surface', surface: 'settings' },
  { id: 'surf-waike', title: 'WAIKE', detail: 'Learning route', kind: 'surface', surface: 'waike' },
  { id: 'surf-gunnchai', title: 'gunnchAI', detail: 'Assist conversation', kind: 'surface', surface: 'gunnchai' },
  { id: 'surf-games', title: 'Games', detail: 'Game library', kind: 'surface', surface: 'games' },
  { id: 'surf-creation', title: 'Creation', detail: 'Create and save', kind: 'surface', surface: 'creation' },
  { id: 'surf-leisure', title: 'Leisure', detail: 'Rights-safe media', kind: 'surface', surface: 'leisure' },
  { id: 'surf-vault', title: 'Vault', detail: 'Files & storage', kind: 'surface', surface: 'vault' },
  { id: 'surf-apps', title: 'App Library', detail: 'Install and open tools', kind: 'surface', surface: 'app_center' },
  { id: 'surf-connect', title: 'Connect', detail: 'Communication', kind: 'surface', surface: 'connect' },
  { id: 'surf-care', title: 'Care', detail: 'Backups', kind: 'surface', surface: 'care' },
  { id: 'surf-assist', title: 'Assist', detail: 'Accessibility', kind: 'surface', surface: 'assist' },
]

const SETTING_HITS: SearchHit[] = [
  { id: 'set-appearance', title: 'Appearance', detail: 'Settings · Appearance', kind: 'setting', surface: 'settings', settingSection: 'appearance' },
  { id: 'set-a11y', title: 'Accessibility', detail: 'Settings · Accessibility', kind: 'setting', surface: 'settings', settingSection: 'accessibility' },
  { id: 'set-ai', title: 'AI / Assist runtime', detail: 'Settings · AI / Assist', kind: 'setting', surface: 'settings', settingSection: 'ai' },
  { id: 'set-privacy', title: 'Privacy & Permissions', detail: 'Settings · Privacy', kind: 'setting', surface: 'settings', settingSection: 'privacy' },
  { id: 'set-diag', title: 'Developer / Diagnostics', detail: 'Settings · Diagnostics', kind: 'setting', surface: 'settings', settingSection: 'diagnostics' },
]

const COMMAND_HITS: SearchHit[] = [
  { id: 'cmd-open-waike', title: 'Open WAIKE', detail: 'Command', kind: 'command', surface: 'waike' },
  { id: 'cmd-open-games', title: 'Open Games library', detail: 'Command', kind: 'command', surface: 'games' },
  { id: 'cmd-ask', title: 'Ask gunnchAI', detail: 'Command', kind: 'command', surface: 'gunnchai' },
  { id: 'cmd-create', title: 'New Creation note', detail: 'Command', kind: 'command', surface: 'creation' },
]

export function searchWiredIndex(query: string): SearchHit[] {
  const q = query.trim().toLowerCase()
  const libraryHits: SearchHit[] = FIRST_PARTY_LIBRARY.map((e) => ({
    id: `lib-${e.id}`,
    title: e.name,
    detail: `${e.category} · ${e.purpose}`,
    kind: 'library' as const,
    surface: e.surface || 'app_center',
  }))
  const all = [...SURFACE_HITS, ...SETTING_HITS, ...COMMAND_HITS, ...libraryHits]
  if (!q) return all.slice(0, 12)
  return all.filter(
    (h) =>
      h.title.toLowerCase().includes(q) ||
      h.detail.toLowerCase().includes(q) ||
      h.id.toLowerCase().includes(q),
  )
}
