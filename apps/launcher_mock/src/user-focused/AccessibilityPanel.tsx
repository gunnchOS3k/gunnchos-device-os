type Props = {
  highContrast: boolean
  largeText: boolean
  reducedMotion: boolean
  onToggle: (key: 'highContrast' | 'largeText' | 'reducedMotion') => void
}

export default function AccessibilityPanel({ highContrast, largeText, reducedMotion, onToggle }: Props) {
  const items = [
    { key: 'highContrast' as const, label: 'High contrast', value: highContrast },
    { key: 'largeText' as const, label: 'Large text', value: largeText },
    { key: 'reducedMotion' as const, label: 'Reduced motion', value: reducedMotion },
  ]
  return (
    <section aria-label="Accessibility settings">
      <h2 style={{ fontSize: 18 }}>Accessibility</h2>
      <p style={{ fontSize: 13, color: '#9aa0a6' }}>Keyboard, controller, and touch navigation supported.</p>
      {items.map(item => (
        <label key={item.key} style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 12, minHeight: 44 }}>
          <input
            type="checkbox"
            checked={item.value}
            aria-label={item.label}
            onChange={() => onToggle(item.key)}
            style={{ width: 24, height: 24 }}
          />
          <span>{item.label}</span>
        </label>
      ))}
    </section>
  )
}
