export interface PwaTarget {
  id: string
  name: string
  category: string
  url: string
  pinned?: boolean
}

export const PWA_TARGETS: PwaTarget[] = [
  { id: 'google-search', name: 'Google Search', category: 'Web', url: 'https://www.google.com', pinned: true },
  { id: 'drive', name: 'Google Drive', category: 'Google Workspace', url: 'https://drive.google.com', pinned: true },
  { id: 'docs', name: 'Google Docs', category: 'Google Workspace', url: 'https://docs.google.com', pinned: true },
  { id: 'sheets', name: 'Google Sheets', category: 'Google Workspace', url: 'https://sheets.google.com', pinned: true },
  { id: 'slides', name: 'Google Slides', category: 'Google Workspace', url: 'https://slides.google.com', pinned: true },
  { id: 'gmail', name: 'Gmail', category: 'Google Workspace', url: 'https://mail.google.com', pinned: true },
  { id: 'calendar', name: 'Google Calendar', category: 'Google Workspace', url: 'https://calendar.google.com', pinned: true },
  { id: 'meet', name: 'Google Meet', category: 'Google Workspace', url: 'https://meet.google.com' },
  { id: 'd2l', name: 'Brightspace D2L', category: 'Learning', url: 'https://www.d2l.com', pinned: true },
  { id: 'notebooklm', name: 'NotebookLM', category: 'AI Learning', url: 'https://notebooklm.google.com', pinned: true },
  { id: 'chatgpt', name: 'ChatGPT', category: 'AI Learning', url: 'https://chat.openai.com', pinned: true },
  { id: 'github', name: 'GitHub', category: 'Coding', url: 'https://github.com', pinned: true },
  { id: 'vscode-web', name: 'VS Code Web', category: 'Coding', url: 'https://vscode.dev', pinned: true },
  { id: 'cursor-web', name: 'Cursor Web', category: 'Coding', url: 'https://cursor.com' },
  { id: 'canvas', name: 'Canvas LMS', category: 'Learning', url: 'https://www.instructure.com/canvas' },
  { id: 'blackboard', name: 'Blackboard', category: 'Learning', url: 'https://www.blackboard.com' },
  { id: 'moodle', name: 'Moodle', category: 'Learning', url: 'https://moodle.org' },
  { id: 'm365', name: 'Microsoft 365', category: 'Productivity', url: 'https://www.office.com' },
  { id: 'zoom', name: 'Zoom Web', category: 'Communication', url: 'https://zoom.us' },
  { id: 'matlab', name: 'MATLAB Online', category: 'STEM', url: 'https://matlab.mathworks.com' },
  { id: 'onshape', name: 'Onshape', category: 'STEM', url: 'https://www.onshape.com' },
  { id: 'overleaf', name: 'Overleaf', category: 'STEM', url: 'https://www.overleaf.com' },
  { id: 'canva', name: 'Canva', category: 'Creative', url: 'https://www.canva.com' },
  { id: 'figma', name: 'Figma', category: 'Creative', url: 'https://www.figma.com' },
  { id: 'photopea', name: 'Photopea', category: 'Creative', url: 'https://www.photopea.com' },
]
