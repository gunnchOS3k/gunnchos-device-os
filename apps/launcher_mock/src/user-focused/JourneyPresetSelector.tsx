import { JOURNEY_PRESETS, PresetId } from './presetData'

type Props = {
  selected: PresetId
  onSelect: (id: PresetId) => void
  highContrast?: boolean
}

export default function JourneyPresetSelector({ selected, onSelect, highContrast }: Props) {
  const border = highContrast ? '#fff' : '#3c4043'
  const accent = highContrast ? '#ffff00' : '#4a9eff'
  return (
    <section aria-label="Choose your journey preset">
      <h2 style={{ fontSize: 18, marginBottom: 12 }}>Choose your journey</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 10 }}>
        {JOURNEY_PRESETS.map(p => (
          <button
            key={p.id}
            type="button"
            aria-label={`${p.label}: ${p.desc}`}
            aria-pressed={selected === p.id}
            onClick={() => onSelect(p.id)}
            style={{
              padding: 16,
              minHeight: 72,
              borderRadius: 12,
              border: selected === p.id ? `2px solid ${accent}` : `1px solid ${border}`,
              background: '#1a2332',
              color: '#fff',
              cursor: 'pointer',
              textAlign: 'left',
            }}
          >
            <strong>{p.label}</strong>
            <div style={{ fontSize: 12, color: '#9aa0a6', marginTop: 4 }}>{p.desc}</div>
          </button>
        ))}
      </div>
    </section>
  )
}
