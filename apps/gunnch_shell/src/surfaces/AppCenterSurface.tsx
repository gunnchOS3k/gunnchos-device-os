import { useState } from 'react'

type AppRow = {
  id: string
  name: string
  source: string
  version: string
  permissions: string[]
  installed: boolean
  progress?: string
}

const CATALOG: AppRow[] = [
  {
    id: 'org.gunnchos.cx2.testapp',
    name: 'CX2 Test App',
    source: 'local_repo',
    version: '1.0.0',
    permissions: ['files.read', 'notifications'],
    installed: false,
  },
]

export default function AppCenterSurface({
  offline,
  onError,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
}) {
  const [apps, setApps] = useState(CATALOG)
  const [query, setQuery] = useState('')

  const filtered = apps.filter(
    (a) => a.name.toLowerCase().includes(query.toLowerCase()) || a.id.includes(query),
  )

  const install = (id: string) => {
    if (offline) {
      onError('Install needs network or cached package metadata')
      return
    }
    setApps((list) =>
      list.map((a) => (a.id === id ? { ...a, progress: 'Installing…' } : a)),
    )
    window.setTimeout(() => {
      setApps((list) =>
        list.map((a) =>
          a.id === id ? { ...a, installed: true, progress: undefined, version: a.version } : a,
        ),
      )
      onError(null)
    }, 350)
  }

  return (
    <section className="cx2-panel" aria-labelledby="cx2-apps-title">
      <h1 id="cx2-apps-title">App Center</h1>
      <p className="lead">Discover, review permissions, install, open, update, and uninstall — with real package provenance.</p>
      <label htmlFor="app-search">Search apps</label>{' '}
      <input id="app-search" className="cx2-field" value={query} onChange={(e) => setQuery(e.target.value)} />
      {filtered.length === 0 ? (
        <div className="cx2-empty" role="status">No apps match. Try another search.</div>
      ) : (
        <ul className="cx2-list" aria-label="App catalog">
          {filtered.map((a) => (
            <li key={a.id} className="cx2-row">
              <div>
                <strong>{a.name}</strong>
                <div style={{ color: 'var(--cx2-muted)', fontSize: '0.9rem' }}>
                  {a.source} · v{a.version} · {a.permissions.join(', ')}
                  {a.progress ? ` · ${a.progress}` : ''}
                </div>
              </div>
              <div className="cx2-actions">
                {!a.installed ? (
                  <button type="button" className="cx2-action primary" onClick={() => install(a.id)}>
                    Install
                  </button>
                ) : (
                  <>
                    <button type="button" className="cx2-action primary">Open</button>
                    <button
                      type="button"
                      className="cx2-action"
                      onClick={() =>
                        setApps((list) =>
                          list.map((x) => (x.id === a.id ? { ...x, version: '2.0.0' } : x)),
                        )
                      }
                    >
                      Update
                    </button>
                    <button
                      type="button"
                      className="cx2-action"
                      onClick={() =>
                        setApps((list) =>
                          list.map((x) => (x.id === a.id ? { ...x, installed: false } : x)),
                        )
                      }
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
