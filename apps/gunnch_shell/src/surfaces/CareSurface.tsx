import { useCallback, useEffect, useState } from 'react'
import Icon from '../design/icons/Icon'
import { EmptyState, SurfaceHeader } from '../design/primitives/SurfaceChrome'

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
  const [providerOk, setProviderOk] = useState<boolean | null>(null)

  const refresh = useCallback(async () => {
    try {
      const data = await providerFetch('/api/backups')
      setBackups(Array.isArray(data.backups) ? data.backups : [])
      setProviderOk(true)
      onError(null)
    } catch (err: any) {
      setBackups([])
      setProviderOk(false)
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
    <section className="cx2-panel vxp-care" aria-labelledby="cx2-care-title">
      <SurfaceHeader
        titleId="cx2-care-title"
        title="Care"
        lead="Health summary, backups, then recovery. Software Care does not grant warranty or RMA."
      />

      <section className="vxp-care-summary" aria-labelledby="vxp-health-title">
        <h2 id="vxp-health-title">Health summary</h2>
        <ul className="vxp-status-list">
          <li>
            <Icon name={providerOk === false ? 'error' : providerOk ? 'status_ok' : 'status_warn'} size={18} />
            <span>
              Backup provider:{' '}
              {providerOk === null ? 'checking…' : providerOk ? 'reachable' : 'unavailable'}
            </span>
          </li>
          <li>
            <Icon name={offline ? 'offline' : 'status_ok'} size={18} />
            <span>{offline ? 'Offline — restore uses local backups when present' : 'Online for provider calls'}</span>
          </li>
          <li>
            <Icon name="care" size={18} />
            <span>Backup count: {backups.length}</span>
          </li>
        </ul>
      </section>

      <section className="vxp-home-section" aria-labelledby="vxp-backup-title">
        <h2 id="vxp-backup-title">Backups</h2>
        <div className="cx2-actions">
          <button type="button" className="cx2-action" data-action="refresh" onClick={() => void refresh()}>
            <Icon name="refresh" size={18} />
            <span>Refresh backups</span>
          </button>
          <button type="button" className="cx2-action primary" data-action="restore" onClick={() => void restore()}>
            <Icon name="backup" size={18} />
            <span>Restore from backup</span>
          </button>
        </div>
        {lastRestore ? (
          <p className="lead" role="status">
            Restored: {lastRestore}
          </p>
        ) : null}
        {backups.length === 0 ? (
          <EmptyState icon="care" title="No backups yet" detail="Create one from Vault. Care will not invent recovery points." />
        ) : (
          <ul className="cx2-list" aria-label="Vault backups">
            {backups.map((b) => (
              <li
                key={b.backup_id}
                className={selected === b.backup_id ? 'cx2-row selected' : 'cx2-row'}
                data-backup-id={b.backup_id}
                data-selected={selected === b.backup_id ? 'true' : 'false'}
                onClick={() => setSelected(b.backup_id)}
              >
                <span>
                  <strong>{b.path}</strong>
                  <span className="vxp-file-meta">
                    {' '}
                    · {b.backup_id} · {b.size}B
                  </span>
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <p className="lead vxp-care-honesty">
        Offline help: restore a Vault backup or repair an app through App Center when providers are available.
        Warranty and RMA are not granted by this software alone.
      </p>
    </section>
  )
}
