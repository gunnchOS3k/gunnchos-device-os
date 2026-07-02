export interface LocalMediaEntry {
  id: string
  name: string
  mimeType: string
  sizeBytes: number
  lastOpenedAt: string
  objectUrl?: string
}

const RECENT_KEY = 'gunnchos-local-media-recent'
const MAX_RECENT = 10

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function formatMimeType(mime: string): string {
  if (!mime) return 'unknown'
  return mime
}

export function listRecentMedia(): LocalMediaEntry[] {
  try {
    const raw = localStorage.getItem(RECENT_KEY)
    return raw ? (JSON.parse(raw) as LocalMediaEntry[]) : []
  } catch {
    return []
  }
}

export function rememberMedia(entry: Omit<LocalMediaEntry, 'id' | 'lastOpenedAt'>): LocalMediaEntry {
  const full: LocalMediaEntry = {
    ...entry,
    id: `media-${Date.now()}`,
    lastOpenedAt: new Date().toISOString(),
  }
  const recent = listRecentMedia().filter(r => r.name !== full.name)
  recent.unshift(full)
  localStorage.setItem(RECENT_KEY, JSON.stringify(recent.slice(0, MAX_RECENT)))
  return full
}

export function clearRecentMedia(): void {
  localStorage.removeItem(RECENT_KEY)
}

export const VIDEO_ACCEPT = 'video/mp4,video/webm,video/ogg'
export const AUDIO_ACCEPT = 'audio/mpeg,audio/mp3,audio/wav,audio/ogg,audio/webm'
