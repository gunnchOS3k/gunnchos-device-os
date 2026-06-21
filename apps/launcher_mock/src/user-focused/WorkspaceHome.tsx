type Props = {
  preset: string
  workspace: string
  apps: string[]
}

export default function WorkspaceHome({ preset, workspace, apps }: Props) {
  return (
    <section aria-label="Workspace home">
      <h2 style={{ fontSize: 18 }}>Your space</h2>
      <p style={{ color: '#9aa0a6', fontSize: 13 }}>Preset: {preset} · Workspace: {workspace}</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: 10, marginTop: 16 }}>
        {apps.map(app => (
          <button
            key={app}
            type="button"
            aria-label={`Open ${app}`}
            style={{
              padding: 20,
              minHeight: 64,
              borderRadius: 12,
              border: '1px solid #3c4043',
              background: '#1a2332',
              color: '#fff',
              cursor: 'pointer',
            }}
          >
            {app.replace(/_/g, ' ')}
          </button>
        ))}
      </div>
    </section>
  )
}
