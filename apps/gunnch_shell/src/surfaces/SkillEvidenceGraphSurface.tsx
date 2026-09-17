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
    throw new Error(`skill graph provider ${res.status}: ${bodyText.slice(0, 200)}`)
  }
  if (data && typeof data === 'object' && 'ok' in data && data.ok === false) {
    throw new Error(`skill graph action failed: ${bodyText.slice(0, 200)}`)
  }
  return data
}

export default function SkillEvidenceGraphSurface({
  offline,
  onError,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
}) {
  const [skills, setSkills] = useState<any[]>([])
  const [why, setWhy] = useState<string[]>([])
  const [note, setNote] = useState<string | null>(null)
  const [providerLabel, setProviderLabel] = useState('connecting…')

  const refresh = useCallback(async () => {
    try {
      const health = await providerFetch('/api/health')
      const data = await providerFetch('/api/skill_graph/get')
      setSkills(data.graph?.skills || [])
      setProviderLabel(health.provider || 'cx3_3-digital-closure')
      onError(null)
    } catch (err: any) {
      setProviderLabel('unavailable')
      onError(err?.message || 'Skill graph provider unreachable')
    }
  }, [onError])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const runJourney = async () => {
    if (offline) {
      onError('Offline — skill graph still viewable from last save')
      return
    }
    try {
      const data = await providerFetch('/api/journey/skill_graph', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      setWhy(data.explain?.why || [])
      setNote(
        data.ok
          ? 'Skill evidence graph rebuilt · text entry alone cannot verify · HUMAN_VALIDATION_PENDING'
          : 'Skill graph journey failed (fail-closed)',
      )
      await refresh()
      onError(null)
    } catch (err: any) {
      onError(err?.message || 'Skill graph journey failed')
    }
  }

  return (
    <main className="cx3-panel" aria-label="Skill Evidence Graph">
      <header>
        <h1 id="cx33-skill-title">Skill Evidence Graph</h1>
      </header>
      <p className="lead">
        Inspect why a skill appears. Evidence-backed and self-declared skills stay visibly distinct.
      </p>
      <p data-testid="provider-label">Provider: {providerLabel}</p>
      <nav aria-label="Skill graph actions">
        <div className="cx2-actions" role="group" aria-label="Skill graph actions">
          <button type="button" className="cx2-action primary" onClick={() => void runJourney()}>
            Rebuild skill graph
          </button>
          <button type="button" className="cx2-action" onClick={() => void refresh()} tabIndex={0}>
            Refresh
          </button>
        </div>
      </nav>
      <ul aria-label="Skills">
        {skills.map((s) => (
          <li key={s.skill_id} data-verified={String(!!s.verified)} data-self-declared={String(!!s.self_declared)}>
            <button
              type="button"
              aria-label={`Why is skill ${s.label} here?`}
              onClick={() => setWhy(s.why || [])}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') setWhy(s.why || [])
              }}
            >
              {s.label}
            </button>{' '}
            <span className="badge">{s.status}</span>
          </li>
        ))}
      </ul>
      {why.length > 0 && (
        <section aria-labelledby="why-title">
          <h2 id="why-title">Why is this skill here?</h2>
          <ul>
            {why.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </section>
      )}
      {note && <p role="status">{note}</p>}
    </main>
  )
}
