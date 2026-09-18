import { useState } from 'react'

export default function ConnectSurface({
  offline,
  onError,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
}) {
  const [to, setTo] = useState('peer@localhost')
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [inbox, setInbox] = useState<string[]>([])
  const [events, setEvents] = useState<string[]>([])

  const send = () => {
    if (!subject.trim()) {
      onError('Subject is required')
      return
    }
    if (offline) {
      setInbox((i) => [`Queued: ${subject}`, ...i])
      onError(null)
      return
    }
    setInbox((i) => [`Sent: ${subject}`, ...i])
    setSubject('')
    setBody('')
    onError(null)
  }

  return (
    <section className="cx2-panel" aria-labelledby="cx2-connect-title">
      <h1 id="cx2-connect-title">Connect</h1>
      <p className="lead">Mail, calendar, and contacts over local protocols — not Gmail/Outlook completeness.</p>
      <div className="cx2-actions" role="group" aria-label="Compose">
        <label htmlFor="mail-to">To</label>
        <input id="mail-to" className="cx2-field" value={to} onChange={(e) => setTo(e.target.value)} />
        <label htmlFor="mail-subject">Subject</label>
        <input id="mail-subject" className="cx2-field" value={subject} onChange={(e) => setSubject(e.target.value)} />
        <label htmlFor="mail-body">Message</label>
        <textarea id="mail-body" className="cx2-field" style={{ minHeight: 96 }} value={body} onChange={(e) => setBody(e.target.value)} />
        <button type="button" className="cx2-action primary" onClick={send}>
          {offline ? 'Queue send' : 'Send'}
        </button>
        <button
          type="button"
          className="cx2-action"
          onClick={() => setEvents((ev) => [`Meeting ${ev.length + 1}`, ...ev])}
        >
          Add calendar event
        </button>
      </div>
      {inbox.length === 0 ? (
        <div className="cx2-empty" role="status">Inbox empty — compose or sync when online.</div>
      ) : (
        <ul className="cx2-list" aria-label="Inbox">{inbox.map((m) => <li key={m} className="cx2-row"><span>{m}</span></li>)}</ul>
      )}
      {events.length > 0 && (
        <ul className="cx2-list" aria-label="Calendar events" style={{ marginTop: 12 }}>
          {events.map((e) => <li key={e} className="cx2-row"><span>{e}</span></li>)}
        </ul>
      )}
    </section>
  )
}
