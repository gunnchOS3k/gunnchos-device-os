export interface StudentProfile {
  displayName: string
  who: string
  goal: string
  control: 'simple' | 'guided' | 'full'
  accessibility: string[]
  offline: boolean
  guardian: boolean
  onboarded: boolean
}

export const DEFAULT_PROFILE: StudentProfile = {
  displayName: '',
  who: 'college',
  goal: 'all',
  control: 'guided',
  accessibility: [],
  offline: false,
  guardian: false,
  onboarded: false,
}

export const WHO_OPTIONS = [
  { id: 'high_school', label: 'High school student' },
  { id: 'college', label: 'College student' },
  { id: 'stem', label: 'STEM learner' },
  { id: 'creator', label: 'Creator / artist' },
  { id: 'gamer', label: 'Gamer' },
  { id: 'developer', label: 'Developer / builder' },
]

export const GOAL_OPTIONS = [
  { id: 'learn', label: 'Learn & study' },
  { id: 'code', label: 'Code & build' },
  { id: 'create', label: 'Create media' },
  { id: 'play', label: 'Play games' },
  { id: 'all', label: 'All of the above' },
]

export const CONTROL_OPTIONS = [
  { id: 'simple', label: 'Simple — guide me' },
  { id: 'guided', label: 'Guided — show options' },
  { id: 'full', label: 'Full control — power user' },
]

export const ACCESSIBILITY_OPTIONS = [
  { id: 'large_text', label: 'Large text' },
  { id: 'high_contrast', label: 'High contrast' },
  { id: 'screen_reader', label: 'Screen reader support' },
  { id: 'captions', label: 'Captions' },
  { id: 'dyslexia', label: 'Dyslexia-friendly reading' },
]
