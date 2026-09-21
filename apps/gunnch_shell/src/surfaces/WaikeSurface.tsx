import { useCallback, useEffect, useState } from 'react'
import Icon from '../design/icons/Icon'
import { EmptyState, SurfaceHeader } from '../design/primitives/SurfaceChrome'
import { capsuleInvoke, isCapsuleBridgeAvailable } from '../platform/capsuleBridge'
import { recordContinuity } from '../platform/continuityStore'

type WaikeState = {
  mode: string
  offline: boolean
  hubUrl?: string
  message: string
  opened?: string
}

export default function WaikeSurface({
  offline,
  onError,
  onReturnHome,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
  onReturnHome: () => void
}) {
  const [state, setState] = useState<WaikeState>({
    mode: 'ADAPTER',
    offline: Boolean(offline),
    message: 'Preparing WAIKE learning route…',
  })
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      if (isCapsuleBridgeAvailable()) {
        const res = await capsuleInvoke('waike_launch', {
          mode: 'WEB_PWA',
          offline: Boolean(offline),
        })
        if (!res.ok) {
          setState({
            mode: 'UNAVAILABLE',
            offline: Boolean(offline),
            message: res.error || 'WAIKE bridge unavailable',
          })
          onError(res.error || 'WAIKE bridge unavailable')
          return
        }
        const result = (res.result || {}) as Record<string, unknown>
        const mode = String(result.mode || 'WEB_PWA')
        const opened = typeof result.opened === 'string' ? result.opened : undefined
        setState({
          mode,
          offline: Boolean(offline) || Boolean(result.offlineHubProvenance),
          hubUrl: typeof result.urlHint === 'string' ? result.urlHint : undefined,
          opened,
          message: opened
            ? 'Opened WAIKE hub via adapter. Use Back to return to gunnchOS.'
            : 'WAIKE adapter ready. Configure WAIKE_HUB_URL (https or loopback http for adb-reverse demo) for handoff, or use the offline learning stub below.',
        })
        recordContinuity({
          id: 'waike-session',
          domain: 'waike',
          title: 'WAIKE learning',
          subtitle: mode,
          surface: 'waike',
        })
        onError(null)
      } else {
        setState({
          mode: 'FULL_VIA_ADAPTER',
          offline: Boolean(offline),
          message: offline
            ? 'Offline — showing local WAIKE stub. Sync to Learning OS SoR when connectivity returns.'
            : 'Browser shell: WAIKE runs as an in-OS adapter surface with honest offline/session controls.',
        })
        recordContinuity({
          id: 'waike-session',
          domain: 'waike',
          title: 'WAIKE learning',
          subtitle: 'adapter stub',
          surface: 'waike',
        })
        onError(null)
      }
    } finally {
      setLoading(false)
    }
  }, [offline, onError])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return (
    <section className="cx2-panel vxp-waike" aria-labelledby="cx2-waike-title" data-testid="waike-surface">
      <SurfaceHeader
        titleId="cx2-waike-title"
        title="WAIKE"
        lead="Learning OS entry on Capsule. Product depth stays in WAIKE; Capsule hosts the full route via adapter when needed."
        meta={
          <p className="vxp-provider-line" data-testid="waike-mode">
            Mode: {state.mode}
            {loading ? ' · connecting…' : ''}
            {state.offline ? ' · offline honesty on' : ''}
          </p>
        }
      />

      <div className="vxp-waike-frame" role="region" aria-label="WAIKE learning session">
        <p className="lead">{state.message}</p>
        {state.hubUrl && (
          <p className="vxp-identity-meta">
            Hub hint: {state.hubUrl}
          </p>
        )}
        {state.opened && (
          <p className="vxp-identity-meta" data-testid="waike-opened">
            Opened: {state.opened}
          </p>
        )}

        <div className="vxp-waike-stub" data-testid="waike-stub">
          <h3>Continue lesson</h3>
          <p>
            {state.offline
              ? 'No remote lesson sync while offline. Local stub keeps the route usable.'
              : state.opened
                ? 'Learning client handed off. Sign in if needed, then open a track/lesson.'
                : 'Open the learning client when the hub URL is configured. We will not invent progress you have not earned.'}
          </p>
          <ul className="cx2-list" aria-label="Local learning actions">
            <li className="cx2-row">
              <span>Session lifecycle: active in Capsule</span>
            </li>
            <li className="cx2-row">
              <span>Back / return: returns to gunnchOS shell</span>
            </li>
            <li className="cx2-row">
              <span>Errors: shown honestly above — no screenshot placeholders</span>
            </li>
          </ul>
        </div>
      </div>

      <div className="cx2-actions">
        <button
          type="button"
          className="cx2-action primary"
          data-testid="waike-continue-lesson"
          onClick={() => void refresh()}
        >
          <Icon name="open" size={16} />
          <span>Continue lesson</span>
        </button>
        <button type="button" className="cx2-action" onClick={() => void refresh()}>
          <Icon name="refresh" size={16} />
          <span>Retry adapter</span>
        </button>
        <button type="button" className="cx2-action" onClick={onReturnHome}>
          <Icon name="home" size={16} />
          <span>Return to gunnchOS</span>
        </button>
      </div>

      {state.mode === 'UNAVAILABLE' && (
        <EmptyState
          icon="error"
          title="WAIKE unavailable"
          detail="The learning adapter could not start. Retry when the hub or bridge is ready."
        />
      )}
    </section>
  )
}
