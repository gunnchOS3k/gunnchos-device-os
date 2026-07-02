export const theme = {
  bg: '#0a0e14',
  surface: '#141b24',
  surfaceRaised: '#1c2633',
  border: '#2d3a4d',
  accent: '#4a9eff',
  accentMuted: '#1e3a5f',
  success: '#34d399',
  warning: '#fbbf24',
  danger: '#f87171',
  text: '#e8eaed',
  textMuted: '#9aa0a6',
  gameBg: '#0d0818',
  gameAccent: '#a855f7',
  font: 'system-ui, -apple-system, "Segoe UI", sans-serif',
  radius: 12,
  touchMin: 44,
} as const

export type Theme = typeof theme
