import { useCallback, useEffect, useState } from 'react'

const PROVIDER_BASE = 'http://127.0.0.1:8773'

async function providerFetch(path: string, init?: RequestInit): Promise<any> {
  const res = await fetch(`${PROVIDER_BASE}${path}`, {
    ...init,
    headers: { Accept: 'application/json', ...(init?.headers || {}) },
  })
  const bodyText = await res.text()
  let data: any = null
  try {
    data = bodyText ? JSON.parse(bodyText) : null
  } catch {
    data = { raw: bodyText.slice(0, 400) }
  }
  if (!res.ok) {
    throw new Error(`education provider ${res.status}: ${bodyText.slice(0, 200)}`)
  }
  if (data && typeof data === 'object' && 'ok' in data && data.ok === false) {
    throw new Error(`education action failed: ${bodyText.slice(0, 200)}`)
  }
  return data
}

export default function EducationTimelineSurface({
  offline,
  onError,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
}) {
  const [entries, setEntries] = useState<any[]>([])
  const [note, setNote] = useState<string | null>(null)
  const [providerLabel, setProviderLabel] = useState('connecting…')

  const refresh = useCallback(async () => {
    try {
      const health = await providerFetch('/api/health')
      const data = await providerFetch('/api/education/get')
      setEntries(data.timeline?.entries || [])
      setProviderLabel(health.provider || 'cx3_3-digital-closure')
      onError(null)
    } catch (err: any) {
      setProviderLabel('unavailable')
      onError(err?.message || 'Education provider unreachable')
    }
  }, [onError])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const runJourney = async () => {
    if (offline) {
      onError('Offline — education timeline still viewable from last save')
      return
    }
    try {
      const data = await providerFetch('/api/journey/education_timeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      setNote(
        data.ok
          ? 'Education timeline updated · verified vs user-entered distinguished · certification_claimed=false'
          : 'Education timeline journey failed (fail-closed)',
      )
      await refresh()
      onError(null)
    } catch (err: any) {
      onError(err?.message || 'Education timeline journey failed')
    }
  }

  return (
    <main className="cx3-panel" aria-label="Education and Achievements">
      <header>
        <h1 id="cx33-edu-title">Education &amp; Achievements</h1>
      </header>
      <p className="lead">
        Verified credentials stay distinct from user-entered education. No fake institutional verification.
        HUMAN_VALIDATION_PENDING for accessibility user study.
      </p>
      <p data-testid="provider-label">Provider: {providerLabel}</p>
      <nav aria-label="Education timeline actions">
        <div className="cx2-actions" role="group" aria-label="Education actions">
          <button type="button" className="cx2-action primary" onClick={() => void runJourney()}>
            Update education timeline
          </button>
          <button type="button" className="cx2-action" onClick={() => void refresh()}>
            Refresh
          </button>
        </div>
      </nav>
      <ul aria-label="Timeline entries">
        {entries.map((e) => (
          <li key={e.entry_id} data-verified={String(!!e.verified)}>
            <span>{e.label}</span>{' '}
            <span className="badge">{e.status_badge || e.source}</span>
          </li>
        ))}
      </ul>
      {note && <p role="status">{note}</p>}
    </main>
  )
}
