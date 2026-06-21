type Props = {
  enabled: boolean
  onToggle: () => void
}

export default function GuardianPanel({ enabled, onToggle }: Props) {
  return (
    <section aria-label="Guardian controls">
      <h2 style={{ fontSize: 18 }}>Guardian controls</h2>
      <p style={{ fontSize: 13, color: '#9aa0a6' }}>
        Mock family safety — no private content inspection by default.
      </p>
      <label style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 12, minHeight: 44 }}>
        <input
          type="checkbox"
          checked={enabled}
          aria-label="Enable guardian controls"
          onChange={onToggle}
          style={{ width: 24, height: 24 }}
        />
        <span>Enable guardian controls</span>
      </label>
      {enabled && (
        <ul style={{ fontSize: 13, marginTop: 12, color: '#9aa0a6' }}>
          <li>School mode restrictions</li>
          <li>Play time window</li>
          <li>App approval list</li>
          <li>Emergency unlock path</li>
        </ul>
      )}
    </section>
  )
}
