import { useCallback, useEffect, useState } from 'react'

export type AppRow = {
  id: string
  name: string
  source: string
  version: string
  permissions: string[]
  installed: boolean
  progress?: string
  provenance?: string
  branch?: string
  provider?: string
}

const PROVIDER_BASE = 'http://127.0.0.1:8766'

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
    throw new Error(`provider ${res.status}: ${bodyText.slice(0, 200)}`)
  }
  if (data && typeof data === 'object' && 'ok' in data && data.ok === false) {
    throw new Error(`provider action failed: ${bodyText.slice(0, 200)}`)
  }
  return data
}

export default function AppCenterSurface({
  offline,
  onError,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
}) {
  const [apps, setApps] = useState<AppRow[]>([])
  const [query, setQuery] = useState('')
  const [providerLabel, setProviderLabel] = useState('connecting…')
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const data = await providerFetch(`/api/apps?q=${encodeURIComponent(query)}`)
      setApps(Array.isArray(data.apps) ? data.apps : [])
      setProviderLabel(data.provider || 'flatpak')
      onError(null)
    } catch (err: any) {
      setApps([])
      setProviderLabel('unavailable')
      onError(err?.message || 'App Center provider unreachable')
    } finally {
      setLoading(false)
    }
  }, [onError, query])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const filtered = apps.filter(
    (a) =>
      a.name.toLowerCase().includes(query.toLowerCase()) ||
      a.id.toLowerCase().includes(query.toLowerCase()),
  )

  const install = async (id: string) => {
    if (offline) {
      onError('Install needs network or cached package metadata')
      return
    }
    setApps((list) => list.map((a) => (a.id === id ? { ...a, progress: 'Installing…' } : a)))
    try {
      await providerFetch('/api/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_id: id, version: '1.0.0' }),
      })
      await refresh()
    } catch (err: any) {
      onError(err?.message || 'Install failed')
      await refresh()
    }
  }

  const openApp = async (id: string) => {
    try {
      await providerFetch('/api/launch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_id: id }),
      })
      onError(null)
    } catch (err: any) {
      onError(err?.message || 'Launch failed')
    }
  }

  const updateApp = async (id: string) => {
    setApps((list) => list.map((a) => (a.id === id ? { ...a, progress: 'Updating…' } : a)))
    try {
      await providerFetch('/api/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_id: id, version: '2.0.0' }),
      })
      await refresh()
    } catch (err: any) {
      onError(err?.message || 'Update failed')
      await refresh()
    }
  }

  const rollbackApp = async (id: string) => {
    setApps((list) => list.map((a) => (a.id === id ? { ...a, progress: 'Rolling back…' } : a)))
    try {
      await providerFetch('/api/rollback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_id: id, version: '1.0.0' }),
      })
      await refresh()
    } catch (err: any) {
      onError(err?.message || 'Rollback failed')
      await refresh()
    }
  }

  const uninstall = async (id: string) => {
    setApps((list) => list.map((a) => (a.id === id ? { ...a, progress: 'Uninstalling…' } : a)))
    try {
      await providerFetch('/api/uninstall', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_id: id }),
      })
      await refresh()
    } catch (err: any) {
      onError(err?.message || 'Uninstall failed')
      await refresh()
    }
  }

  return (
    <section className="cx2-panel" aria-labelledby="cx2-apps-title">
      <h1 id="cx2-apps-title">App Center</h1>
      <p className="lead">
        Discover, review permissions, install, open, update, and uninstall — with real package provenance.
      </p>
      <p data-testid="provider-label" style={{ color: 'var(--cx2-muted)', fontSize: '0.9rem' }}>
        Provider: {providerLabel}
        {loading ? ' · refreshing…' : ''}
      </p>
      <label htmlFor="app-search">Search apps</label>{' '}
      <input
        id="app-search"
        className="cx2-field"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        aria-label="Search apps"
      />
      <button type="button" className="cx2-action" onClick={() => void refresh()} style={{ marginLeft: 8 }}>
        Refresh
      </button>
      {filtered.length === 0 ? (
        <div className="cx2-empty" role="status">
          No apps match. Try another search.
        </div>
      ) : (
        <ul className="cx2-list" aria-label="App catalog">
          {filtered.map((a) => (
            <li key={a.id} className="cx2-row" data-app-id={a.id} data-installed={a.installed ? '1' : '0'} data-version={a.version}>
              <div>
                <strong>{a.name}</strong>
                <div style={{ color: 'var(--cx2-muted)', fontSize: '0.9rem' }}>
                  {a.source} · v{a.version}
                  {a.provenance ? ` · ${a.provenance}` : ''}
                  {a.permissions?.length ? ` · ${a.permissions.join(', ')}` : ''}
                  {a.progress ? ` · ${a.progress}` : ''}
                </div>
              </div>
              <div className="cx2-actions">
                {!a.installed ? (
                  <button
                    type="button"
                    className="cx2-action primary"
                    data-action="install"
                    onClick={() => void install(a.id)}
                  >
                    Install
                  </button>
                ) : (
                  <>
                    <button type="button" className="cx2-action primary" data-action="open" onClick={() => void openApp(a.id)}>
                      Open
                    </button>
                    <button type="button" className="cx2-action" data-action="update" onClick={() => void updateApp(a.id)}>
                      Update
                    </button>
                    <button type="button" className="cx2-action" data-action="rollback" onClick={() => void rollbackApp(a.id)}>
                      Rollback
                    </button>
                    <button
                      type="button"
                      className="cx2-action"
                      data-action="uninstall"
                      onClick={() => void uninstall(a.id)}
                    >
                      Uninstall
                    </button>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
