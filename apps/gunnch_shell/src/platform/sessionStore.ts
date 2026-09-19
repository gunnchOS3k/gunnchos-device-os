/**
 * Capsule session persistence helpers (shell-side).
 * Android host persists durable state via bridge session_get/session_put.
 */

import { capsuleInvoke, isCapsuleBridgeAvailable } from './capsuleBridge'

export type CapsuleSession = {
  version: 1
  surface: string
  history: string[]
  offline: boolean
  highContrast: boolean
  reduceMotion: boolean
  scale: number
  updatedAt: string
}

const LOCAL_KEY = 'gunnchos.capsule.session.v1'

export function loadLocalSession(): CapsuleSession | null {
  try {
    const raw = localStorage.getItem(LOCAL_KEY)
    if (!raw) return null
    return JSON.parse(raw) as CapsuleSession
  } catch {
    return null
  }
}

export function saveLocalSession(session: CapsuleSession): void {
  try {
    localStorage.setItem(LOCAL_KEY, JSON.stringify(session))
  } catch {
    // ignore quota / private mode
  }
}

export async function loadSession(): Promise<CapsuleSession | null> {
  if (isCapsuleBridgeAvailable()) {
    const res = await capsuleInvoke('session_get')
    if (res.ok && res.result) return res.result as CapsuleSession
  }
  return loadLocalSession()
}

export async function saveSession(session: CapsuleSession): Promise<void> {
  saveLocalSession(session)
  if (isCapsuleBridgeAvailable()) {
    await capsuleInvoke('session_put', { session: session as unknown as Record<string, unknown> })
  }
}
