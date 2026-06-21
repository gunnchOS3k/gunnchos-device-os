type Props = {
  enabled: boolean
  onToggle: () => void
}

export default function OfflineModePanel({ enabled, onToggle }: Props) {
  return (
    <section aria-label="Offline mode">
      <h2 style={{ fontSize: 18 }}>Offline mode</h2>
      <p style={{ fontSize: 13, color: '#9aa0a6' }}>
        Lessons, writing, sketching, and coding templates work without internet. Sync when connected.
      </p>
      <label style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 12, minHeight: 44 }}>
        <input
          type="checkbox"
          checked={enabled}
          aria-label="Enable offline-first mode"
          onChange={onToggle}
          style={{ width: 24, height: 24 }}
        />
        <span>Offline-first mode</span>
      </label>
    </section>
  )
}
