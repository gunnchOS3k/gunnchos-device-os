/** Typed mirror of design/tokens.css for TS consumers. */
export const tokens = {
  color: {
    bg: '#0c1218',
    surface: '#162029',
    ink: '#e8eef4',
    muted: '#8fa0b0',
    accent: '#d4a017',
    accentInk: '#1a1404',
    info: '#5b9fd4',
    ok: '#6fbf8a',
    warn: '#e0a45a',
    danger: '#e07a7a',
    line: '#2a3846',
  },
  font: {
    display: '"Avenir Next Condensed", "Segoe UI Semibold", "Helvetica Neue", system-ui, sans-serif',
    body: '"Avenir Next", "Segoe UI", "Helvetica Neue", system-ui, sans-serif',
    mono: '"SF Mono", "Cascadia Mono", "Consolas", ui-monospace, monospace',
  },
  space: { 1: 4, 2: 8, 3: 12, 4: 16, 5: 24, 6: 32, 7: 48 },
  radius: { sm: 6, md: 10, lg: 14 },
  touchMin: 44,
  motion: { fast: 120, med: 220 },
} as const

export type VxpIconName =
  | 'home'
  | 'vault'
  | 'app_center'
  | 'connect'
  | 'more'
  | 'assist'
  | 'care'
  | 'wallet'
  | 'portfolio'
  | 'career'
  | 'verifier'
  | 'back'
  | 'exit'
  | 'search'
  | 'refresh'
  | 'backup'
  | 'trash'
  | 'install'
  | 'open'
  | 'update'
  | 'offline'
  | 'error'
  | 'empty'
  | 'status_ok'
  | 'status_warn'
  | 'chevron'
  | 'file'
  | 'app_glyph'
