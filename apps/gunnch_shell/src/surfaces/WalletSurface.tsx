import { useCallback, useEffect, useState } from 'react'

const PROVIDER_BASE = 'http://127.0.0.1:8771'

type Credential = {
  credential_id: string
  name?: string
  status?: string
  issued_at?: string
  certification_claimed?: boolean
  evidence?: { artifact_sha256?: string; artifact_path?: string }
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
    throw new Error(`wallet provider ${res.status}: ${bodyText.slice(0, 200)}`)
  }
  if (data && typeof data === 'object' && 'ok' in data && data.ok === false) {
    throw new Error(`wallet action failed: ${bodyText.slice(0, 200)}`)
  }
  return data
}

export default function WalletSurface({
  offline,
  onError,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
}) {
  const [credentials, setCredentials] = useState<Credential[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [verifyNote, setVerifyNote] = useState<string | null>(null)
  const [providerLabel, setProviderLabel] = useState('connecting…')

  const refresh = useCallback(async () => {
    try {
      const health = await providerFetch('/api/health')
      const data = await providerFetch('/api/wallet/list')
      setCredentials(Array.isArray(data.credentials) ? data.credentials : [])
      setProviderLabel(health.provider || 'cx3-wallet')
      onError(null)
    } catch (err: any) {
      setCredentials([])
      setProviderLabel('unavailable')
      onError(err?.message || 'Wallet provider unreachable')
    }
  }, [onError])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const issueJourney = async () => {
    if (offline) {
      onError('Offline — cannot issue signed credential')
      return
    }
    try {
      const data = await providerFetch('/api/journey/signed_credential', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      setVerifyNote(
        data.verify?.verified
          ? `Verified offline · tamper_detected=${Boolean(data.tamper?.tamper_detected)} · certification_claimed=false`
          : 'Verification failed (fail-closed)',
      )
      await refresh()
      onError(null)
    } catch (err: any) {
      onError(err?.message || 'Signed credential journey failed')
    }
  }

  const revokeSelected = async () => {
    if (!selected) {
      onError('Select a credential to revoke')
      return
    }
    try {
      await providerFetch('/api/wallet/revoke', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential_id: selected }),
      })
      setVerifyNote(`Revoked ${selected}`)
      await refresh()
      onError(null)
    } catch (err: any) {
      onError(err?.message || 'Revoke failed')
    }
  }

  const verifySelected = async () => {
    if (!selected) {
      onError('Select a credential to verify')
      return
    }
    try {
      const data = await providerFetch(`/api/wallet/verify/${encodeURIComponent(selected)}`)
      setVerifyNote(
        data.verified
          ? 'Offline verify PASS · certification_claimed=false'
          : `Offline verify FAIL · ${JSON.stringify(data.reasons || [])}`,
      )
      onError(null)
    } catch (err: any) {
      onError(err?.message || 'Verify failed')
    }
  }

  return (
    <section className="cx2-panel" aria-labelledby="cx3-wallet-title">
      <h1 id="cx3-wallet-title">Credential Wallet</h1>
      <p className="lead">
        Signed learning evidence assertions. Provider {providerLabel}. Always{' '}
        <code>certification_claimed=false</code> — not a degree, diploma, or accreditation.
      </p>
      <div className="cx2-actions" role="group" aria-label="Wallet actions">
        <button type="button" className="cx2-action primary" data-action="signed-journey" onClick={issueJourney}>
          Signed credential journey
        </button>
        <button type="button" className="cx2-action" data-action="verify" onClick={verifySelected}>
          Offline verify
        </button>
        <button type="button" className="cx2-action" data-action="revoke" onClick={revokeSelected}>
          Revoke
        </button>
        <button type="button" className="cx2-action" data-action="refresh" onClick={() => void refresh()}>
          Refresh
        </button>
      </div>
      {verifyNote && (
        <p role="status" data-testid="wallet-verify-note">
          {verifyNote}
        </p>
      )}
      <ul className="cx2-file-list" aria-label="Credentials">
        {credentials.map((c) => (
          <li key={c.credential_id}>
            <button
              type="button"
              className={selected === c.credential_id ? 'cx2-action primary' : 'cx2-action'}
              onClick={() => setSelected(c.credential_id)}
            >
              {c.name || c.credential_id} · {c.status || 'active'} · claim=false
            </button>
          </li>
        ))}
        {credentials.length === 0 && <li>No credentials yet — run the signed journey.</li>}
      </ul>
    </section>
  )
}
