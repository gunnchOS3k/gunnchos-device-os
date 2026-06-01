export const DEVICES = [
  'Student 14.5"',
  'Handheld Hybrid',
  'DS-XL Coder',
  'Arena/Wearables',
] as const

export const MODES = [
  'School Mode',
  'Developer Mode',
  'Play Mode',
  'Research Measurement Mode',
  'Fleet Admin Mode',
] as const

export const DEVICE_ID_MAP: Record<string, string> = {
  'Student 14.5"': 'student_14_5',
  'Handheld Hybrid': 'handheld_hybrid',
  'DS-XL Coder': 'ds_xl_coder',
  'Arena/Wearables': 'arena_wearables',
}

export const MODE_ID_MAP: Record<string, string> = {
  'School Mode': 'school',
  'Developer Mode': 'developer',
  'Play Mode': 'play',
  'Research Measurement Mode': 'research_measurement',
  'Fleet Admin Mode': 'fleet_admin',
}
