/**
 * First-party App Library catalog — only wired product entries.
 * No fabricated third-party indexing.
 */

import type { Cx2Surface } from '../shellSurfaces'

export type AppLibraryCategory =
  | 'Learning'
  | 'Intelligence'
  | 'Games'
  | 'Creation'
  | 'Communication'
  | 'Leisure'
  | 'Files & Storage'
  | 'System'
  | 'Career/Portfolio'

export type LibraryEntry = {
  id: string
  name: string
  category: AppLibraryCategory
  purpose: string
  surface?: Cx2Surface
  gameId?: string
  installState: 'bundled' | 'adapter' | 'available' | 'unavailable'
}

export const FIRST_PARTY_LIBRARY: LibraryEntry[] = [
  {
    id: 'waike',
    name: 'WAIKE',
    category: 'Learning',
    purpose: 'Courses and lesson continuity',
    surface: 'waike',
    installState: 'adapter',
  },
  {
    id: 'gunnchai',
    name: 'gunnchAI',
    category: 'Intelligence',
    purpose: 'Ask for help with truthful runtime labels',
    surface: 'gunnchai',
    installState: 'bundled',
  },
  {
    id: 'anime-aggressors',
    name: 'Anime Aggressors',
    category: 'Games',
    purpose: 'Launch when Capsule web or guest build is present',
    surface: 'games',
    gameId: 'anime-aggressors',
    installState: 'available',
  },
  {
    id: 'pedestrian-pursuit',
    name: 'Pedestrian Pursuit',
    category: 'Games',
    purpose: 'Launch when Capsule web or guest build is present',
    surface: 'games',
    gameId: 'pedestrian-pursuit',
    installState: 'available',
  },
  {
    id: 'archive-of-life',
    name: 'Archive of Life',
    category: 'Games',
    purpose: 'Launch when Capsule web build is present',
    surface: 'games',
    gameId: 'archive-of-life',
    installState: 'available',
  },
  {
    id: 'beatlink-party',
    name: 'BeatLink Party',
    category: 'Games',
    purpose: 'Launch when Capsule web build is present',
    surface: 'games',
    gameId: 'beatlink-party',
    installState: 'available',
  },
  {
    id: 'creation',
    name: 'Creation',
    category: 'Creation',
    purpose: 'Create, edit, and save local notes',
    surface: 'creation',
    installState: 'bundled',
  },
  {
    id: 'connect',
    name: 'Connect',
    category: 'Communication',
    purpose: 'Local mail and calendar',
    surface: 'connect',
    installState: 'bundled',
  },
  {
    id: 'leisure',
    name: 'Leisure',
    category: 'Leisure',
    purpose: 'Rights-safe rest and offline media',
    surface: 'leisure',
    installState: 'bundled',
  },
  {
    id: 'vault',
    name: 'Vault',
    category: 'Files & Storage',
    purpose: 'Files you keep and recover',
    surface: 'vault',
    installState: 'bundled',
  },
  {
    id: 'care',
    name: 'Care',
    category: 'Files & Storage',
    purpose: 'Backups and recovery',
    surface: 'care',
    installState: 'bundled',
  },
  {
    id: 'settings',
    name: 'Settings',
    category: 'System',
    purpose: 'Appearance, AI runtime, privacy, diagnostics',
    surface: 'settings',
    installState: 'bundled',
  },
  {
    id: 'search',
    name: 'Search / Command',
    category: 'System',
    purpose: 'Find wired spaces and commands',
    surface: 'search',
    installState: 'bundled',
  },
  {
    id: 'assist',
    name: 'Assist',
    category: 'System',
    purpose: 'Accessibility controls',
    surface: 'assist',
    installState: 'bundled',
  },
  {
    id: 'wallet',
    name: 'Wallet',
    category: 'Career/Portfolio',
    purpose: 'Credentials you control',
    surface: 'wallet',
    installState: 'bundled',
  },
  {
    id: 'portfolio',
    name: 'Portfolio',
    category: 'Career/Portfolio',
    purpose: 'Evidence you can share',
    surface: 'portfolio',
    installState: 'bundled',
  },
  {
    id: 'career',
    name: 'Career',
    category: 'Career/Portfolio',
    purpose: 'Profile and pathways',
    surface: 'career',
    installState: 'bundled',
  },
  {
    id: 'verifier',
    name: 'Verifier',
    category: 'Career/Portfolio',
    purpose: 'Check claims honestly',
    surface: 'verifier',
    installState: 'bundled',
  },
]

export const LIBRARY_CATEGORY_ORDER: AppLibraryCategory[] = [
  'Learning',
  'Intelligence',
  'Games',
  'Creation',
  'Communication',
  'Leisure',
  'Files & Storage',
  'System',
  'Career/Portfolio',
]

export const GAME_TITLES = FIRST_PARTY_LIBRARY.filter((e) => e.category === 'Games')
