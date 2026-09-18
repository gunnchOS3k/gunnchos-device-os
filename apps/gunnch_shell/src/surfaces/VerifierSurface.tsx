import { useCallback, useEffect, useState } from 'react'

const PROVIDER_BASE = 'http://127.0.0.1:8772'

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
    throw new Error(`verifier provider ${res.status}: ${bodyText.slice(0, 200)}`)
  }
  if (data && typeof data === 'object' && 'ok' in data && data.ok === false) {
    throw new Error(`verifier action failed: ${bodyText.slice(0, 200)}`)
  }
  return data
}

export default function VerifierSurface({
  offline,
  onError,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
}) {
  const [note, setNote] = useState<string | null>(null)
  const [providerLabel, setProviderLabel] = useState('connecting…')

  const refresh = useCallback(async () => {
    try {
      const health = await providerFetch('/api/health')
      setProviderLabel(health.provider || 'cx3_2-verifier')
      onError(null)
    } catch (err: any) {
      setProviderLabel('unavailable')
      onError(err?.message || 'Verifier provider unreachable')
    }
  }, [onError])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const runVerifier = async () => {
    try {
      // Ensure a share exists first
      await providerFetch('/api/journey/share_package', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exclude_contact: true }),
      })
      const data = await providerFetch('/api/journey/verifier', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      const stale = offline || data.offline?.credentials?.[0]?.freshness === 'stale'
      setNote(
        [
          data.valid ? 'signature verified' : 'not valid',
          `tampered_valid=${data.tampered_valid}`,
          `wallet_db_used=${data.wallet_db_used}`,
          stale ? 'status freshness=stale (honest)' : 'status freshness=fresh',
          'certification_claimed=false',
        ].join(' · '),
      )
      onError(null)
    } catch (err: any) {
      onError(err?.message || 'Verifier journey failed')
    }
  }

  return (
    <section className="cx2-panel" aria-labelledby="cx32-verifier-title">
      <h1 id="cx32-verifier-title">Credential / Portfolio Verifier</h1>
      <p className="lead">
        Independent verification of share packages. Does not use Wallet internal DB as authority.
      </p>
      <p data-testid="provider-label">Provider: {providerLabel}</p>
      <div className="cx2-actions" role="group" aria-label="Verifier actions">
        <button type="button" className="cx2-action primary" onClick={() => void runVerifier()}>
          Verify share package
        </button>
        <button type="button" className="cx2-action" onClick={() => void refresh()}>
          Refresh
        </button>
      </div>
      {note && <p role="status">{note}</p>}
    </section>
  )
}
