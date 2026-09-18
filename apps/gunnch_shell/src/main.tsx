import React, { useCallback, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import CompleteExperienceShell, { type Cx2Surface, type DeviceProfile } from './CompleteExperienceShell'
import { resolveHostRuntime } from './platform/hostRuntime'
import { loadSession, saveSession, type CapsuleSession } from './platform/sessionStore'
import {
  capsuleInvoke,
  installFatalHandlers,
  reportBootStage,
  reportShellReady,
} from './platform/capsuleBridge'

installFatalHandlers()
reportBootStage('JS_BUNDLE_STARTED')

function CapsuleRoot() {
  const runtime = resolveHostRuntime()
  const [ready, setReady] = useState(false)
  const [offline, setOffline] = useState(false)
  const [initialSurface, setInitialSurface] = useState<Cx2Surface | undefined>(undefined)
  const [sessionSeed, setSessionSeed] = useState<Partial<CapsuleSession> | null>(null)

  useEffect(() => {
    reportBootStage('SESSION_LOADING')
    let cancelled = false
    ;(async () => {
      const session = await loadSession()
      if (cancelled) return
      if (session) {
        setOffline(Boolean(session.offline))
        if (session.surface) setInitialSurface(session.surface as Cx2Surface)
        setSessionSeed(session)
      }
      setReady(true)
    })()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    const onOnline = () => setOffline(false)
    const onOffline = () => setOffline(true)
    window.addEventListener('online', onOnline)
    window.addEventListener('offline', onOffline)
    setOffline(typeof navigator !== 'undefined' ? !navigator.onLine : false)
    return () => {
      window.removeEventListener('online', onOnline)
      window.removeEventListener('offline', onOffline)
    }
  }, [])

  useEffect(() => {
    if (!ready) return
    reportBootStage('REACT_ROOT_MOUNTED')
    // Defer SHELL_READY one frame so Home paint can commit
    requestAnimationFrame(() => {
      reportBootStage('SHELL_READY')
      reportShellReady()
    })
  }, [ready])

  const persist = useCallback(
    (partial: Partial<CapsuleSession>) => {
      const next: CapsuleSession = {
        version: 1,
        surface: (partial.surface as string) || sessionSeed?.surface || 'home',
        history: (partial.history as string[]) || sessionSeed?.history || ['home'],
        offline,
        highContrast: Boolean(partial.highContrast ?? sessionSeed?.highContrast),
        reduceMotion: Boolean(partial.reduceMotion ?? sessionSeed?.reduceMotion),
        scale: Number(partial.scale ?? sessionSeed?.scale ?? 1),
        updatedAt: new Date().toISOString(),
      }
      setSessionSeed(next)
      void saveSession(next)
    },
    [offline, sessionSeed],
  )

  const onExit = useCallback(() => {
    void capsuleInvoke('exit_capsule')
  }, [])

  if (!ready) {
    return (
      <div
        role="status"
        aria-label="Loading gunnchOS"
        style={{
          minHeight: '100vh',
          margin: 0,
          padding: 24,
          fontFamily: 'system-ui, sans-serif',
          backgroundColor: '#0B1220',
          color: '#E8EEF7',
        }}
      >
        Loading gunnchOS…
      </div>
    )
  }

  const profile: DeviceProfile =
    runtime.host === 'ANDROID_CAPSULE' ? 'handheld_hybrid' : (runtime.profile as DeviceProfile)

  return (
    <CompleteExperienceShell
      profile={profile}
      offline={offline}
      onExit={runtime.host === 'ANDROID_CAPSULE' ? onExit : undefined}
      initialSurface={initialSurface}
      onSessionChange={persist}
      hostKind={runtime.host}
    />
  )
}

if (typeof window !== 'undefined' && window.AndroidCapsuleBridge) {
  window.__GUNNCH_HOST__ = 'ANDROID_CAPSULE'
  window.__GUNNCH_CAPSULE_BRIDGE__ = true
}

const rootEl = document.getElementById('root')
if (!rootEl) {
  reportBootStage('FATAL_NO_ROOT')
  throw new Error('gunnchOS root element missing')
}

createRoot(rootEl).render(
  <React.StrictMode>
    <CapsuleRoot />
  </React.StrictMode>,
)
