import { useCallback, useEffect, useState } from 'react'

const PROVIDER_BASE = 'http://127.0.0.1:8771'

type Artifact = {
  artifact_id: string
  title?: string
  visibility?: string
  summary?: string
  certification_claimed?: boolean
}

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
    throw new Error(`portfolio provider ${res.status}: ${bodyText.slice(0, 200)}`)
  }
  if (data && typeof data === 'object' && 'ok' in data && data.ok === false) {
    throw new Error(`portfolio action failed: ${bodyText.slice(0, 200)}`)
  }
  return data
}

export default function PortfolioSurface({
  offline,
  onError,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
}) {
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [selected, setSelected] = useState<string[]>([])
  const [exportNote, setExportNote] = useState<string | null>(null)
  const [providerLabel, setProviderLabel] = useState('connecting…')

  const refresh = useCallback(async () => {
    try {
      const health = await providerFetch('/api/health')
      const data = await providerFetch('/api/portfolio/list')
      setArtifacts(Array.isArray(data.artifacts) ? data.artifacts : [])
      setProviderLabel(health.provider || 'cx3-portfolio')
      onError(null)
    } catch (err: any) {
      setArtifacts([])
      setProviderLabel('unavailable')
      onError(err?.message || 'Portfolio provider unreachable')
    }
  }, [onError])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const toggle = (id: string) => {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  const selectiveExport = async () => {
    if (offline) {
      onError('Offline — portable export queued locally when online')
      return
    }
    if (selected.length === 0) {
      onError('Select at least one artifact for privacy-selective export')
      return
    }
    try {
      const data = await providerFetch('/api/portfolio/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selected_artifact_ids: selected,
          title: 'Portable learning portfolio',
        }),
      })
      setExportNote(
        `Exported ${data.export?.export_id || 'package'} · files=${(data.files || []).join(', ')} · certification_claimed=false`,
      )
      onError(null)
    } catch (err: any) {
      onError(err?.message || 'Portfolio export failed')
    }
  }

  return (
    <section className="cx2-panel vxp-surface" aria-labelledby="cx3-portfolio-title">
      <h1 id="cx3-portfolio-title">Portfolio</h1>
      <p className="lead">
        Privacy-selective portable package (HTML + manifest). Provider {providerLabel}. No accreditation claims.
      </p>
      <div className="cx2-actions" role="group" aria-label="Portfolio actions">
        <button type="button" className="cx2-action primary" data-action="selective-export" onClick={selectiveExport}>
          Selective portable export
        </button>
        <button type="button" className="cx2-action" data-action="refresh" onClick={() => void refresh()}>
          Refresh
        </button>
      </div>
      {exportNote && (
        <p role="status" data-testid="portfolio-export-note">
          {exportNote}
        </p>
      )}
      <ul className="cx2-file-list" aria-label="Portfolio artifacts">
        {artifacts.map((a) => (
          <li key={a.artifact_id}>
            <label>
              <input
                type="checkbox"
                checked={selected.includes(a.artifact_id)}
                onChange={() => toggle(a.artifact_id)}
              />{' '}
              {a.title || a.artifact_id} · {a.visibility || 'private'} · claim=false
            </label>
          </li>
        ))}
        {artifacts.length === 0 && <li>No artifacts yet — issue a credential from Wallet first.</li>}
      </ul>
    </section>
  )
}
