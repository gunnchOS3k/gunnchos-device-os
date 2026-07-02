import { useEffect, useState } from 'react'

export const SETTINGS_STORAGE_KEY = 'gunnchos-settings-v1'

export interface GunnchSettings {
  theme: 'default' | 'dark' | 'high-contrast'
  largeText: boolean
  highContrast: boolean
  reducedMotion: boolean
  offlineMode: boolean
  aiPrivacy: boolean
}

export const DEFAULT_SETTINGS: GunnchSettings = {
  theme: 'default',
  largeText: false,
  highContrast: false,
  reducedMotion: false,
  offlineMode: false,
  aiPrivacy: true,
}

export function loadSettings(): GunnchSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_STORAGE_KEY)
    if (!raw) return { ...DEFAULT_SETTINGS }
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
  } catch {
    return { ...DEFAULT_SETTINGS }
  }
}

export function saveSettings(settings: GunnchSettings): void {
  localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings))
}

export function useSettings(): [GunnchSettings, (patch: Partial<GunnchSettings>) => void] {
  const [settings, setSettings] = useState<GunnchSettings>(() => loadSettings())

  useEffect(() => {
    saveSettings(settings)
  }, [settings])

  const patch = (updates: Partial<GunnchSettings>) => {
    setSettings(prev => ({ ...prev, ...updates }))
  }

  return [settings, patch]
}
