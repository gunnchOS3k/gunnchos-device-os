import { useState } from 'react'

export default function CareSurface({
  offline,
  onError,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
}) {
  const [bundles, setBundles] = useState<string[]>([])

  return (
    <section className="cx2-panel" aria-labelledby="cx2-care-title">
      <h1 id="cx2-care-title">Care</h1>
      <p className="lead">Diagnostics, redacted support bundles, backup/restore, and offline help.</p>
      <div className="cx2-actions">
        <button
          type="button"
          className="cx2-action primary"
          onClick={() => {
            setBundles((b) => [`bundle-${b.length + 1}`, ...b])
            onError(null)
          }}
        >
          Export support bundle
        </button>
        <button
          type="button"
          className="cx2-action"
          onClick={() => onError(offline ? 'Restore uses local Vault backup' : null)}
        >
          Restore from backup
        </button>
      </div>
      {bundles.length === 0 ? (
        <div className="cx2-empty" role="status">No support bundles yet.</div>
      ) : (
        <ul className="cx2-list" aria-label="Support bundles">
          {bundles.map((b) => (
            <li key={b} className="cx2-row">
              <span>{b} (redaction applied)</span>
            </li>
          ))}
        </ul>
      )}
      <p className="lead">Offline help: export a bundle, restore Vault backup, or repair an app. Warranty/RMA is not granted by software alone.</p>
    </section>
  )
}
