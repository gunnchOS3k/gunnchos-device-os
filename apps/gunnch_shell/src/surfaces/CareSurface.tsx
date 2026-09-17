import { useCallback, useEffect, useState } from 'react'

const PROVIDER_BASE = 'http://127.0.0.1:8767'

type Backup = {
  backup_id: string
  path: string
  sha256: string
  size: number
  created_at: number
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
    throw new Error(`care provider ${res.status}: ${bodyText.slice(0, 200)}`)
  }
  if (data && typeof data === 'object' && 'ok' in data && data.ok === false) {
    throw new Error(`care action failed: ${bodyText.slice(0, 200)}`)
  }
  return data
}

export default function CareSurface({
  offline,
  onError,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
}) {
  const [backups, setBackups] = useState<Backup[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [lastRestore, setLastRestore] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      const data = await providerFetch('/api/backups')
      setBackups(Array.isArray(data.backups) ? data.backups : [])
      onError(null)
    } catch (err: any) {
      setBackups([])
      onError(err?.message || 'Care/Vault backup provider unreachable')
    }
  }, [onError])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const restore = async () => {
    if (offline) {
      onError('Restore uses local Vault backup')
      return
    }
    if (!selected) {
      onError('Select a backup to restore')
      return
    }
    try {
      const data = await providerFetch('/api/restore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ backup_id: selected }),
      })
      setLastRestore(data.path || selected)
      onError(null)
      await refresh()
    } catch (err: any) {
      onError(err?.message || 'Restore failed')
    }
  }

  return (
    <section className="cx2-panel" aria-labelledby="cx2-care-title">
      <h1 id="cx2-care-title">Care</h1>
      <p className="lead">Diagnostics, backup/restore through the Vault provider, and offline help.</p>
      <div className="cx2-actions">
        <button type="button" className="cx2-action" data-action="refresh" onClick={() => void refresh()}>
          Refresh backups
        </button>
        <button
          type="button"
          className="cx2-action primary"
          data-action="restore"
          onClick={() => void restore()}
        >
          Restore from backup
        </button>
      </div>
      {lastRestore ? (
        <p className="lead" role="status">
          Restored: {lastRestore}
        </p>
      ) : null}
      {backups.length === 0 ? (
        <div className="cx2-empty" role="status">
          No backups yet — create one from Vault.
        </div>
      ) : (
        <ul className="cx2-list" aria-label="Vault backups">
          {backups.map((b) => (
            <li
              key={b.backup_id}
              className="cx2-row"
              data-backup-id={b.backup_id}
              data-selected={selected === b.backup_id ? 'true' : 'false'}
              onClick={() => setSelected(b.backup_id)}
            >
              <span>
                {b.backup_id} · {b.path} · {b.sha256.slice(0, 12)}
              </span>
            </li>
          ))}
        </ul>
      )}
      <p className="lead">
        Offline help: restore Vault backup or repair an app. Warranty/RMA is not granted by software alone.
      </p>
    </section>
  )
}
