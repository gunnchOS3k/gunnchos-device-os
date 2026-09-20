import { useCallback, useEffect, useMemo, useState } from 'react'
import Icon from '../design/icons/Icon'
import { EmptyState, SurfaceHeader } from '../design/primitives/SurfaceChrome'
import {
  FIRST_PARTY_LIBRARY,
  LIBRARY_CATEGORY_ORDER,
  type AppLibraryCategory,
} from '../platform/appLibraryCatalog'
import type { Cx2Surface } from '../shellSurfaces'

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
  onOpenSurface,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
  onOpenSurface?: (id: Cx2Surface) => void
}) {
  const [apps, setApps] = useState<AppRow[]>([])
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<AppLibraryCategory | 'All'>('All')
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

  const firstParty = useMemo(() => {
    return FIRST_PARTY_LIBRARY.filter((e) => {
      if (category !== 'All' && e.category !== category) return false
      const q = query.toLowerCase()
      if (!q) return true
      return e.name.toLowerCase().includes(q) || e.purpose.toLowerCase().includes(q) || e.category.toLowerCase().includes(q)
    })
  }, [category, query])

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
    <section className="cx2-panel vxp-apps" aria-labelledby="cx2-apps-title">
      <SurfaceHeader
        titleId="cx2-apps-title"
        title="App Library"
        lead="First-party categories plus provider-backed installs. Provenance stays secondary — no SHA in primary UI."
        meta={
          <p data-testid="provider-label" className="vxp-provider-line">
            Provider: {providerLabel}
            {loading ? ' · refreshing…' : ''}
          </p>
        }
      />

      <div className="vxp-search-row">
        <label htmlFor="app-search">Search apps</label>
        <input
          id="app-search"
          className="cx2-field"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search apps"
        />
        <button type="button" className="cx2-action" onClick={() => void refresh()}>
          <Icon name="refresh" size={18} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="vxp-category-row" role="tablist" aria-label="App Library categories" data-testid="app-library-categories">
        <button
          type="button"
          role="tab"
          aria-selected={category === 'All'}
          className={category === 'All' ? 'vxp-chip active' : 'vxp-chip'}
          onClick={() => setCategory('All')}
        >
          All
        </button>
        {LIBRARY_CATEGORY_ORDER.map((c) => (
          <button
            key={c}
            type="button"
            role="tab"
            aria-selected={category === c}
            className={category === c ? 'vxp-chip active' : 'vxp-chip'}
            onClick={() => setCategory(c)}
          >
            {c}
          </button>
        ))}
      </div>

      <h3 className="vxp-section-title">First-party</h3>
      {firstParty.length === 0 ? (
        <EmptyState icon="app_center" title="No first-party matches" detail="Try another category or search." />
      ) : (
        <ul className="cx2-list vxp-app-list" aria-label="First-party catalog">
          {firstParty.map((e) => (
            <li key={e.id} className="cx2-row vxp-app-row" data-app-id={e.id}>
              <div className="vxp-app-identity">
                <span className="vxp-app-glyph" aria-hidden="true">
                  <Icon name="app_glyph" size={28} />
                </span>
                <div>
                  <strong>{e.name}</strong>
                  <div className="vxp-app-status">
                    {e.category} · {e.installState}
                  </div>
                  <div className="vxp-app-meta">{e.purpose}</div>
                </div>
              </div>
              <div className="cx2-actions">
                {e.surface && (
                  <button
                    type="button"
                    className="cx2-action primary"
                    onClick={() => onOpenSurface?.(e.surface!)}
                  >
                    <Icon name="open" size={16} />
                    <span>Open</span>
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <h3 className="vxp-section-title">Provider catalog</h3>
      {providerLabel === 'unavailable' ? (
        <EmptyState
          icon="error"
          title="App Center provider unavailable"
          detail="First-party library above still works. We will not invent a provider catalog."
        />
      ) : filtered.length === 0 ? (
        <EmptyState icon="app_center" title="No provider apps match" detail="Try another search. Empty results stay empty." />
      ) : (
        <ul className="cx2-list vxp-app-list" aria-label="Provider catalog">
          {filtered.map((a) => (
            <li
              key={a.id}
              className="cx2-row vxp-app-row"
              data-app-id={a.id}
              data-installed={a.installed ? '1' : '0'}
              data-version={a.version}
            >
              <div className="vxp-app-identity">
                <span className="vxp-app-glyph" aria-hidden="true">
                  <Icon name="app_glyph" size={28} />
                </span>
                <div>
                  <strong>{a.name}</strong>
                  <div className="vxp-app-status">
                    {a.installed ? 'Installed' : 'Available'}
                    {a.progress ? ` · ${a.progress}` : ''}
                    {` · v${a.version}`}
                  </div>
                  <div className="vxp-app-meta">
                    {a.source}
                    {a.provenance ? ` · ${a.provenance}` : ''}
                    {a.permissions?.length ? ` · ${a.permissions.join(', ')}` : ''}
                  </div>
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
                    <Icon name="install" size={16} />
                    <span>Install</span>
                  </button>
                ) : (
                  <>
                    <button
                      type="button"
                      className="cx2-action primary"
                      data-action="open"
                      onClick={() => void openApp(a.id)}
                    >
                      <Icon name="open" size={16} />
                      <span>Open</span>
                    </button>
                    <button type="button" className="cx2-action" data-action="update" onClick={() => void updateApp(a.id)}>
                      <Icon name="update" size={16} />
                      <span>Update</span>
                    </button>
                    <button
                      type="button"
                      className="cx2-action"
                      data-action="rollback"
                      onClick={() => void rollbackApp(a.id)}
                    >
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
