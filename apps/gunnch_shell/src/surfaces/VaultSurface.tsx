import { useCallback, useEffect, useState } from 'react'
import Icon from '../design/icons/Icon'
import { EmptyState, SurfaceHeader } from '../design/primitives/SurfaceChrome'

export type VaultFile = {
  path: string
  size: number
  sha256: string
  modified_at: number
  mime: string
}

const PROVIDER_BASE = 'http://127.0.0.1:8767'

function formatBytes(n: number): string {
  if (!Number.isFinite(n) || n < 0) return '—'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

function formatModified(ts: number): string {
  if (!ts) return '—'
  try {
    return new Date(ts * (ts < 1e12 ? 1000 : 1)).toLocaleString()
  } catch {
    return '—'
  }
}

function fileTypeLabel(path: string, mime: string): string {
  const base = path.split('/').pop() || path
  const ext = base.includes('.') ? base.split('.').pop()!.toUpperCase() : ''
  if (ext) return ext
  if (mime) return mime.split('/').pop() || mime
  return 'FILE'
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
  const [detailsOpen, setDetailsOpen] = useState(false)

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
  const selectedFile = files.find((f) => f.path === selected) || null

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
    <section className="cx2-panel vxp-vault" aria-labelledby="cx2-vault-title">
      <SurfaceHeader
        titleId="cx2-vault-title"
        title="Vault"
        lead="Your files — name, type, size, and modified first. Hashes and provider details stay in the details pane."
        meta={
          <p data-testid="vault-provider-label" className="vxp-provider-line">
            Provider: {providerLabel}
            {lastBackup ? ` · last backup ${lastBackup}` : ''}
          </p>
        }
      />

      <div className="cx2-actions">
        <button type="button" className="cx2-action primary" data-action="refresh" onClick={() => void refresh()}>
          <Icon name="refresh" size={18} />
          <span>Refresh</span>
        </button>
        <button type="button" className="cx2-action" data-action="backup" onClick={() => void backup()}>
          <Icon name="backup" size={18} />
          <span>Backup</span>
        </button>
        <button
          type="button"
          className="cx2-action"
          data-action="open-writer"
          disabled={!selected}
          onClick={() => selected && void openWithWriter(selected)}
        >
          <Icon name="open" size={18} />
          <span>Open with Writer</span>
        </button>
      </div>

      <div className="vxp-search-row">
        <label htmlFor="vault-search">Search Vault</label>
        <input
          id="vault-search"
          className="cx2-field"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search files"
        />
      </div>

      {providerLabel === 'unavailable' ? (
        <EmptyState
          icon="error"
          title="Vault provider unavailable"
          detail="Start the local Vault provider or work offline with previously cached files when available."
        />
      ) : visible.length === 0 ? (
        <EmptyState
          icon="vault"
          title="No files yet"
          detail="Save from Writer into Vault. We will not show sample documents."
        />
      ) : (
        <ul className="cx2-list vxp-file-list" aria-label="Vault files">
          {visible.map((f) => {
            const name = f.path.split('/').pop() || f.path
            return (
              <li
                key={f.path}
                className={selected === f.path ? 'cx2-row vxp-file-row selected' : 'cx2-row vxp-file-row'}
                data-path={f.path}
                data-selected={selected === f.path ? 'true' : 'false'}
                onClick={() => {
                  setSelected(f.path)
                  setDetailsOpen(true)
                }}
              >
                <div className="vxp-file-primary">
                  <Icon name="file" size={20} />
                  <div>
                    <strong className="vxp-file-name">{name}</strong>
                    <div className="vxp-file-meta">
                      <span>{fileTypeLabel(f.path, f.mime)}</span>
                      <span>{formatBytes(f.size)}</span>
                      <span>{formatModified(f.modified_at)}</span>
                    </div>
                  </div>
                </div>
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
                  <Icon name="trash" size={16} />
                  <span>Trash</span>
                </button>
              </li>
            )
          })}
        </ul>
      )}

      {selectedFile && detailsOpen && (
        <aside className="vxp-details" aria-label="File details">
          <h2>Details</h2>
          <dl className="vxp-dl">
            <div>
              <dt>Path</dt>
              <dd>{selectedFile.path}</dd>
            </div>
            <div>
              <dt>MIME</dt>
              <dd>{selectedFile.mime || '—'}</dd>
            </div>
            <div>
              <dt>SHA-256</dt>
              <dd className="vxp-mono">{selectedFile.sha256}</dd>
            </div>
            <div>
              <dt>Provider</dt>
              <dd>{providerLabel}</dd>
            </div>
          </dl>
        </aside>
      )}
    </section>
  )
}
