export type AppCategory =
  | 'browser'
  | 'productivity'
  | 'coding'
  | 'ai'
  | 'creative'
  | 'stem'
  | 'learning'
  | 'media'
  | 'system'
  | 'games'

export type AppLevel = 'native' | 'pwa' | 'linux' | 'android'

export interface GunnchApp {
  id: string
  name: string
  category: AppCategory
  level: AppLevel
  icon: string
  description: string
  offline?: boolean
  url?: string
}

export const GUNNCH_APPS: GunnchApp[] = [
  { id: 'browser', name: 'Browser', category: 'browser', level: 'native', icon: 'browser', description: 'Chrome-compatible web browsing', offline: false },
  { id: 'files', name: 'Files', category: 'system', level: 'native', icon: 'folder', description: 'Downloads, offline docs, USB drives', offline: true },
  { id: 'notes', name: 'Notes', category: 'productivity', level: 'native', icon: 'notes', description: 'Local notes and study capture', offline: true },
  { id: 'calendar', name: 'Calendar', category: 'productivity', level: 'pwa', icon: 'calendar', description: 'Class schedule and deadlines', url: 'https://calendar.google.com' },
  { id: 'email', name: 'Email', category: 'productivity', level: 'pwa', icon: 'email', description: 'Gmail and school email', url: 'https://mail.google.com' },
  { id: 'drive', name: 'Google Drive', category: 'productivity', level: 'pwa', icon: 'drive', description: 'Cloud storage and sync', url: 'https://drive.google.com' },
  { id: 'docs', name: 'Docs', category: 'productivity', level: 'pwa', icon: 'docs', description: 'Word processing', url: 'https://docs.google.com' },
  { id: 'sheets', name: 'Sheets', category: 'productivity', level: 'pwa', icon: 'sheets', description: 'Spreadsheets', url: 'https://sheets.google.com' },
  { id: 'slides', name: 'Slides', category: 'productivity', level: 'pwa', icon: 'slides', description: 'Presentations', url: 'https://slides.google.com' },
  { id: 'd2l', name: 'Brightspace D2L', category: 'learning', level: 'pwa', icon: 'lms', description: 'Learning management system', url: 'https://www.d2l.com' },
  { id: 'notebooklm', name: 'NotebookLM', category: 'ai', level: 'pwa', icon: 'notebook', description: 'AI study notebooks', url: 'https://notebooklm.google.com' },
  { id: 'chatgpt', name: 'ChatGPT', category: 'ai', level: 'pwa', icon: 'ai', description: 'AI learning assistant', url: 'https://chat.openai.com' },
  { id: 'ai-assistant', name: 'GunnchAI', category: 'ai', level: 'native', icon: 'ai', description: 'Built-in AI study companion', offline: true },
  { id: 'vscode-web', name: 'VS Code Web', category: 'coding', level: 'pwa', icon: 'code', description: 'Browser-based coding', url: 'https://vscode.dev' },
  { id: 'github', name: 'GitHub', category: 'coding', level: 'pwa', icon: 'github', description: 'Repos, issues, and Pages', url: 'https://github.com' },
  { id: 'terminal', name: 'Terminal', category: 'coding', level: 'linux', icon: 'terminal', description: 'Shell, Git, SSH', offline: true },
  { id: 'jupyter', name: 'Jupyter', category: 'stem', level: 'linux', icon: 'jupyter', description: 'STEM notebooks', offline: true },
  { id: 'stem-hub', name: 'STEM Hub', category: 'stem', level: 'native', icon: 'stem', description: 'MATLAB, CAD, simulation tools' },
  { id: 'creative-hub', name: 'Creative Hub', category: 'creative', level: 'native', icon: 'creative', description: 'Krita, GIMP, Blender, Kdenlive' },
  { id: 'camera', name: 'Camera', category: 'media', level: 'native', icon: 'camera', description: 'Photo and scan capture', offline: true },
  { id: 'recorder', name: 'Audio Recorder', category: 'media', level: 'native', icon: 'mic', description: 'Voice notes and podcasts', offline: true },
  { id: 'screen-recorder', name: 'Screen Recorder', category: 'media', level: 'native', icon: 'screen', description: 'Record presentations and demos', offline: true },
  { id: 'video-editor', name: 'Video Editor', category: 'creative', level: 'linux', icon: 'video', description: 'Kdenlive-style editing', offline: true },
  { id: 'pdf', name: 'PDF Reader', category: 'productivity', level: 'native', icon: 'pdf', description: 'Read and annotate PDFs', offline: true },
  { id: 'settings', name: 'Settings', category: 'system', level: 'native', icon: 'settings', description: 'System preferences' },
  { id: 'game-mode', name: 'Game Mode', category: 'games', level: 'native', icon: 'gamepad', description: 'Console-style game launcher' },
]

export const CAMPUS_DOCK_IDS = [
  'browser', 'files', 'notes', 'drive', 'ai-assistant', 'vscode-web', 'github', 'd2l', 'settings', 'game-mode',
]

export function getApp(id: string): GunnchApp | undefined {
  return GUNNCH_APPS.find(a => a.id === id)
}
