export interface FirstPartyGame {
  id: string
  title: string
  genre: string
  description: string
  fpsTarget: number
  supportsController: boolean
  supportsTouch: boolean
  offline: boolean
  accent: string
}

export const FIRST_PARTY_GAMES: FirstPartyGame[] = [
  {
    id: 'anime-aggressors',
    title: 'Anime Aggressors',
    genre: 'Platform Fighter',
    description: 'Original-character arena combat with combos, specials, and local multiplayer.',
    fpsTarget: 60,
    supportsController: true,
    supportsTouch: true,
    offline: true,
    accent: '#ff6b6b',
  },
  {
    id: 'foot-racing',
    title: 'Foot Racing Game',
    genre: 'Action Racing',
    description: 'Sprint, parkour, and trick your way through original tracks. Your feet are the vehicle.',
    fpsTarget: 60,
    supportsController: true,
    supportsTouch: true,
    offline: true,
    accent: '#ffd93d',
  },
  {
    id: 'earth-species',
    title: 'Earth Species Artifact Adventure',
    genre: 'Educational RPG',
    description: 'Explore Earth, collect species artifacts, and learn biology, ecology, and conservation.',
    fpsTarget: 60,
    supportsController: true,
    supportsTouch: true,
    offline: true,
    accent: '#6bcb77',
  },
]
