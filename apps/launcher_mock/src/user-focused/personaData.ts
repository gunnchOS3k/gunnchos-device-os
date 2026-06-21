export const PERSONAS = [
  { id: 'pre_k_learner', label: 'Pre-K Learner', preset: 'scooter' },
  { id: 'early_reader', label: 'Early Reader', preset: 'scooter' },
  { id: 'high_school_student', label: 'High School Student', preset: 'car' },
  { id: 'writer', label: 'Writer', preset: 'studio' },
  { id: 'musician', label: 'Musician', preset: 'studio' },
  { id: 'artist', label: 'Artist', preset: 'studio' },
  { id: 'gamer', label: 'Gamer', preset: 'arcade' },
  { id: 'college_cs_stem_student', label: 'CS Student', preset: 'workshop' },
  { id: 'postdoctoral_researcher', label: 'Researcher', preset: 'spaceship' },
  { id: 'accessibility_first_user', label: 'Accessibility First', preset: 'car' },
  { id: 'library_community_user', label: 'Library User', preset: 'library' },
  { id: 'parent_guardian', label: 'Parent / Guardian', preset: 'guardian' },
] as const

export type PersonaId = typeof PERSONAS[number]['id']
