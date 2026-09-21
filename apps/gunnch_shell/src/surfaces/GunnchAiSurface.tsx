import { useMemo, useState } from 'react'
import Icon from '../design/icons/Icon'
import { SurfaceHeader } from '../design/primitives/SurfaceChrome'
import { localDeterministicReply, resolveAiRuntime } from '../platform/aiRuntime'
import { capsuleInvoke, isCapsuleBridgeAvailable } from '../platform/capsuleBridge'
import { recordContinuity } from '../platform/continuityStore'

type Turn = {
  id: string
  role: 'user' | 'assistant' | 'system'
  text: string
  provenance: string
}

export default function GunnchAiSurface({
  offline,
  onError,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
}) {
  const runtime = useMemo(
    () => resolveAiRuntime({ offline, remoteAvailable: !offline, nearbyEdgeAvailable: false }),
    [offline],
  )
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [turns, setTurns] = useState<Turn[]>([
    {
      id: 'sys-0',
      role: 'system',
      text: `Runtime: ${runtime.label}. ${runtime.detail}`,
      provenance: runtime.kind,
    },
  ])

  const push = (turn: Turn) => setTurns((t) => [...t, turn])

  const ask = async () => {
    const prompt = input.trim()
    if (!prompt) {
      onError('Enter a question')
      return
    }
    setBusy(true)
    onError(null)
    push({ id: `u-${Date.now()}`, role: 'user', text: prompt, provenance: 'user' })
    setInput('')
    try {
      let reply = localDeterministicReply(prompt)
      let provenance = `local_deterministic:${runtime.kind}`
      if (isCapsuleBridgeAvailable()) {
        const res = await capsuleInvoke('gunnchai_launch', { prompt, offline: Boolean(offline) })
        if (res.ok && res.result && typeof res.result === 'object') {
          const r = res.result as Record<string, unknown>
          if (typeof r.reply === 'string' && r.reply.trim()) {
            reply = r.reply
          } else {
            reply = `${reply}\n\n(Host launch metadata: offlineFallback=${String(r.offlineFallback ?? true)}; kirby=${String(r.kirbyEnabled ?? false)})`
          }
          provenance = String(r.provenance || provenance)
        } else if (!res.ok) {
          reply = `${localDeterministicReply(prompt)}\n\nHost bridge note: ${res.error || 'launch failed'} — fell back to local deterministic help.`
          provenance = 'fallback:local_deterministic'
        }
      }
      // Never claim on-device for nearby edge
      if (runtime.kind === 'nearby_mac' && /on-device/i.test(reply)) {
        reply = reply.replace(/on-device/gi, 'nearby edge')
      }
      push({ id: `a-${Date.now()}`, role: 'assistant', text: reply, provenance })
      recordContinuity({
        id: 'gunnchai-session',
        domain: 'gunnchai',
        title: 'gunnchAI conversation',
        subtitle: runtime.label,
        surface: 'gunnchai',
      })
    } catch (err: any) {
      onError(err?.message || 'Assistant failed')
      push({
        id: `a-${Date.now()}`,
        role: 'assistant',
        text: localDeterministicReply(prompt),
        provenance: 'fallback:local_deterministic',
      })
    } finally {
      setBusy(false)
    }
  }

  const retryLast = () => {
    const lastUser = [...turns].reverse().find((t) => t.role === 'user')
    if (!lastUser) return
    setInput(lastUser.text)
  }

  return (
    <section className="cx2-panel vxp-gunnchai" aria-labelledby="cx2-gunnchai-title" data-testid="gunnchai-surface">
      <SurfaceHeader
        titleId="cx2-gunnchai-title"
        title="gunnchAI"
        lead="Ask for help with cancel, retry, and honest provenance. Runtime labels stay truthful."
        meta={
          <p className="vxp-provider-line" data-testid="gunnchai-runtime">
            Runtime: {runtime.label} · Privacy: {runtime.privacy}
          </p>
        }
      />

      <ul className="cx2-list vxp-chat" aria-label="Conversation" data-testid="gunnchai-turns">
        {turns.map((t) => (
          <li key={t.id} className={`cx2-row vxp-chat-turn role-${t.role}`}>
            <div>
              <strong>{t.role}</strong>
              <p>{t.text}</p>
              <span className="vxp-app-meta">provenance: {t.provenance}</span>
            </div>
          </li>
        ))}
      </ul>

      <div className="cx2-actions" role="group" aria-label="Ask gunnchAI">
        <label htmlFor="gunnchai-input">Message</label>
        <textarea
          id="gunnchai-input"
          className="cx2-field"
          style={{ minHeight: 80 }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={busy}
        />
        <button type="button" className="cx2-action primary" onClick={() => void ask()} disabled={busy}>
          <Icon name="assist" size={16} />
          <span>{busy ? 'Working…' : 'Ask'}</span>
        </button>
        <button type="button" className="cx2-action" onClick={() => setBusy(false)} disabled={!busy}>
          Cancel
        </button>
        <button type="button" className="cx2-action" onClick={retryLast}>
          <Icon name="refresh" size={16} />
          <span>Retry last</span>
        </button>
      </div>
    </section>
  )
}
