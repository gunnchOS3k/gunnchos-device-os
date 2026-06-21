import { PERSONAS, PersonaId } from './personaData'

type Props = {
  selected: PersonaId
  onSelect: (id: PersonaId) => void
  reducedMotion?: boolean
}

export default function PersonaSelector({ selected, onSelect, reducedMotion }: Props) {
  return (
    <section aria-label="Choose who this device is for">
      <h2 style={{ fontSize: 18, marginBottom: 12 }}>Who is this device for?</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10 }}>
        {PERSONAS.map(p => (
          <button
            key={p.id}
            type="button"
            aria-label={`Select persona ${p.label}`}
            aria-pressed={selected === p.id}
            onClick={() => onSelect(p.id)}
            style={{
              padding: '16px 12px',
              minHeight: 56,
              borderRadius: 12,
              border: selected === p.id ? '2px solid #4a9eff' : '1px solid #3c4043',
              background: selected === p.id ? '#1e3a5f' : '#1a2332',
              color: '#fff',
              cursor: 'pointer',
              fontSize: 14,
              transition: reducedMotion ? 'none' : 'border-color 0.2s',
            }}
          >
            {p.label}
          </button>
        ))}
      </div>
    </section>
  )
}
