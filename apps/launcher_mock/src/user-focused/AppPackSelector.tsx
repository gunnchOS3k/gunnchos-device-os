const APP_PACKS = [
  { id: 'learn_pack', label: 'Learn Pack', apps: ['waike_offline', 'gunnchai3k'] },
  { id: 'write_pack', label: 'Write Pack', apps: ['write_placeholder'] },
  { id: 'art_pack', label: 'Art Pack', apps: ['sketch_placeholder'] },
  { id: 'music_pack', label: 'Music Pack', apps: ['music_notes_placeholder'] },
  { id: 'game_pack', label: 'Game Pack', apps: ['steam', 'scaly_wings'] },
  { id: 'cs_student_pack', label: 'CS Student Pack', apps: ['vscode', 'terminal'] },
  { id: 'research_pack', label: 'Research Pack', apps: ['field_measurement', 'edge_io'] },
  { id: 'offline_essentials_pack', label: 'Offline Essentials', apps: ['waike_offline'] },
]

type Props = {
  selected: string
  onSelect: (id: string) => void
}

export default function AppPackSelector({ selected, onSelect }: Props) {
  return (
    <section aria-label="Choose app pack">
      <h2 style={{ fontSize: 18 }}>App packs</h2>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 12 }}>
        {APP_PACKS.map(p => (
          <button
            key={p.id}
            type="button"
            aria-label={`Select ${p.label}`}
            aria-pressed={selected === p.id}
            onClick={() => onSelect(p.id)}
            style={{
              padding: '12px 16px',
              minHeight: 48,
              borderRadius: 10,
              border: selected === p.id ? '2px solid #4a9eff' : '1px solid #3c4043',
              background: '#1a2332',
              color: '#fff',
              cursor: 'pointer',
            }}
          >
            {p.label}
          </button>
        ))}
      </div>
    </section>
  )
}

export { APP_PACKS }
