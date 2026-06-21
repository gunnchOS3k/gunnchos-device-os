export const JOURNEY_PRESETS = [
  { id: 'scooter', label: 'Scooter', desc: 'Simplest path — one tap to start' },
  { id: 'bicycle', label: 'Bicycle', desc: 'Guided learning and creation' },
  { id: 'car', label: 'Car', desc: 'Full student productivity' },
  { id: 'studio', label: 'Studio', desc: 'Art, writing, and music' },
  { id: 'arcade', label: 'Arcade', desc: 'Games and recreation' },
  { id: 'workshop', label: 'Workshop', desc: 'Maker and developer tools' },
  { id: 'laboratory', label: 'Laboratory', desc: 'Research and experiments' },
  { id: 'spaceship', label: 'Spaceship', desc: 'Full power-user control' },
  { id: 'guardian', label: 'Guardian', desc: 'Family safety and supervision' },
  { id: 'classroom', label: 'Classroom', desc: 'Teacher deployment' },
  { id: 'library', label: 'Library', desc: 'Shared public access' },
  { id: 'offline', label: 'Offline', desc: 'No or low internet' },
] as const

export type PresetId = typeof JOURNEY_PRESETS[number]['id']
