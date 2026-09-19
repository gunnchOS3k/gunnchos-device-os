import { useCallback, useEffect, useState } from 'react'

const PROVIDER_BASE = 'http://127.0.0.1:8772'

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
    throw new Error(`career provider ${res.status}: ${bodyText.slice(0, 200)}`)
  }
  if (data && typeof data === 'object' && 'ok' in data && data.ok === false) {
    throw new Error(`career action failed: ${bodyText.slice(0, 200)}`)
  }
  return data
}

export default function CareerProfileSurface({
  offline,
  onError,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
}) {
  const [headline, setHeadline] = useState('')
  const [summary, setSummary] = useState('')
  const [note, setNote] = useState<string | null>(null)
  const [providerLabel, setProviderLabel] = useState('connecting…')

  const refresh = useCallback(async () => {
    try {
      const health = await providerFetch('/api/health')
      const data = await providerFetch('/api/career/get')
      const profile = data.profile
      if (profile) {
        setHeadline(profile.headline || '')
        setSummary(profile.summary || '')
      }
      setProviderLabel(health.provider || 'cx3_2-career')
      onError(null)
    } catch (err: any) {
      setProviderLabel('unavailable')
      onError(err?.message || 'Career provider unreachable')
    }
  }, [onError])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const runJourney = async () => {
    if (offline) {
      onError('Offline — career profile still viewable from last save; live edits limited')
      return
    }
    try {
      const data = await providerFetch('/api/journey/career_profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ headline, summary }),
      })
      setNote(
        data.ok
          ? `Career profile saved · certification_claimed=false · verified claims not creatable via UI alone`
          : 'Career profile journey failed (fail-closed)',
      )
      await refresh()
      onError(null)
    } catch (err: any) {
      onError(err?.message || 'Career profile journey failed')
    }
  }

  const exportResume = async () => {
    try {
      const data = await providerFetch('/api/career/resume_export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          include_fields: [
            'display_name',
            'headline',
            'summary',
            'skills',
            'projects',
            'credential_refs',
            'artifact_refs',
          ],
        }),
      })
      setNote(`Resume exported · sha256=${String(data.export_sha256 || '').slice(0, 16)}… · private contact excluded`)
      onError(null)
    } catch (err: any) {
      onError(err?.message || 'Resume export failed')
    }
  }

  const buildShare = async () => {
    try {
      const data = await providerFetch('/api/journey/share_package', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          exclude_contact: true,
          exclude_one_credential: true,
          exclude_one_artifact: true,
        }),
      })
      setNote(`Share package ${data.package_id} · selective disclosure applied`)
      onError(null)
    } catch (err: any) {
      onError(err?.message || 'Share package failed')
    }
  }

  return (
    <section className="cx2-panel vxp-surface" aria-labelledby="cx32-career-title">
      <h1 id="cx32-career-title">Career Profile</h1>
      <p className="lead">
        Compose Wallet credentials and Portfolio artifacts into a user-authored career surface.
        Private contact stays private. certification_claimed=false.
      </p>
      <p data-testid="provider-label">Provider: {providerLabel}</p>
      <label>
        Headline
        <input
          aria-label="Career headline"
          value={headline}
          onChange={(e) => setHeadline(e.target.value)}
        />
      </label>
      <label>
        Summary
        <textarea
          aria-label="Career summary"
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
        />
      </label>
      <div className="cx2-actions" role="group" aria-label="Career actions">
        <button type="button" className="cx2-action primary" onClick={() => void runJourney()}>
          Save career journey
        </button>
        <button type="button" className="cx2-action" onClick={() => void exportResume()}>
          Export resume
        </button>
        <button type="button" className="cx2-action" onClick={() => void buildShare()}>
          Build share package
        </button>
        <button type="button" className="cx2-action" onClick={() => void refresh()}>
          Refresh
        </button>
      </div>
      {note && <p role="status">{note}</p>}
    </section>
  )
}
