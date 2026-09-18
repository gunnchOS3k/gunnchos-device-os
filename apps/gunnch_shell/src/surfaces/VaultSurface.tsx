import { useCallback, useEffect, useState } from 'react'

export type VaultFile = {
  path: string
  size: number
  sha256: string
  modified_at: number
  mime: string
}

const PROVIDER_BASE = 'http://127.0.0.1:8767'

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
    throw new Error(`vault provider ${res.status}: ${bodyText.slice(0, 200)}`)
  }
  if (data && typeof data === 'object' && 'ok' in data && data.ok === false) {
    throw new Error(`vault action failed: ${bodyText.slice(0, 200)}`)
  }
  return data
}

export default function VaultSurface({
  offline,
  onError,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
}) {
  const [files, setFiles] = useState<VaultFile[]>([])
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<string | null>(null)
  const [providerLabel, setProviderLabel] = useState('connecting…')
  const [lastBackup, setLastBackup] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      const data = await providerFetch('/api/files')
      setFiles(Array.isArray(data.files) ? data.files : [])
      setProviderLabel(data.provider || 'cx2h2-vault')
      onError(null)
    } catch (err: any) {
      setFiles([])
      setProviderLabel('unavailable')
      onError(err?.message || 'Vault provider unreachable')
    }
  }, [onError])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const visible = files.filter((f) => f.path.toLowerCase().includes(query.toLowerCase()))

  const backup = async () => {
    if (offline) {
      onError('Backup queued offline')
      return
    }
    if (!selected) {
      onError('Select a file to backup')
      return
    }
    try {
      const data = await providerFetch('/api/backup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: selected }),
      })
      setLastBackup(data.backup_id || null)
      onError(null)
      await refresh()
    } catch (err: any) {
      onError(err?.message || 'Backup failed')
    }
  }

  const remove = async (path: string) => {
    try {
      await providerFetch('/api/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      })
      if (selected === path) setSelected(null)
      await refresh()
      onError(null)
    } catch (err: any) {
      onError(err?.message || 'Delete failed')
    }
  }

  const openWithWriter = async (path: string) => {
    try {
      await providerFetch('/api/writer/launch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      })
      onError(null)
    } catch (err: any) {
      onError(err?.message || 'Open with Writer failed')
    }
  }

  return (
    <section className="cx2-panel" aria-labelledby="cx2-vault-title">
      <h1 id="cx2-vault-title">Vault</h1>
      <p className="lead">
        Provider-backed files with hash, MIME, backup, and open-with Writer.
      </p>
      <p data-testid="vault-provider-label" className="lead">
        Provider: {providerLabel}
        {lastBackup ? ` · last backup ${lastBackup}` : ''}
      </p>
      <div className="cx2-actions">
        <button type="button" className="cx2-action primary" data-action="refresh" onClick={() => void refresh()}>
          Refresh
        </button>
        <button type="button" className="cx2-action" data-action="backup" onClick={() => void backup()}>
          Backup
        </button>
        <button
          type="button"
          className="cx2-action"
          data-action="open-writer"
          disabled={!selected}
          onClick={() => selected && void openWithWriter(selected)}
        >
          Open with Writer
        </button>
      </div>
      <label htmlFor="vault-search">Search Vault</label>{' '}
      <input
        id="vault-search"
        className="cx2-field"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search files"
      />
      {visible.length === 0 ? (
        <div className="cx2-empty" role="status">
          No files yet — save from Writer into Vault.
        </div>
      ) : (
        <ul className="cx2-list" aria-label="Vault files">
          {visible.map((f) => (
            <li
              key={f.path}
              className="cx2-row"
              data-path={f.path}
              data-selected={selected === f.path ? 'true' : 'false'}
              onClick={() => setSelected(f.path)}
            >
              <span>
                {f.path} · {f.size}B · {f.mime} · {f.sha256.slice(0, 12)}
              </span>
              <button
                type="button"
                className="cx2-action"
                data-action="delete"
                onClick={(e) => {
                  e.stopPropagation()
                  void remove(f.path)
                }}
                aria-label={`Move ${f.path} to trash`}
              >
                Trash
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
