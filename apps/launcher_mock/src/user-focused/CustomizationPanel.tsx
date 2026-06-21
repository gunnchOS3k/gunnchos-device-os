type Props = {
  depth: 'simple' | 'guided' | 'full' | 'power_user'
  onDepthChange: (d: 'simple' | 'guided' | 'full' | 'power_user') => void
  theme: string
  onThemeChange: (t: string) => void
}

const THEMES = ['default', 'high_contrast', 'large_text', 'writer_focus', 'kid_safe']

export default function CustomizationPanel({ depth, onDepthChange, theme, onThemeChange }: Props) {
  return (
    <section aria-label="Customization settings">
      <h2 style={{ fontSize: 18 }}>Make it yours</h2>
      <label style={{ display: 'block', marginTop: 12 }}>
        <span id="depth-label">Settings depth</span>
        <select
          aria-labelledby="depth-label"
          value={depth}
          onChange={e => onDepthChange(e.target.value as Props['depth'])}
          style={{ marginLeft: 8, padding: 8, minHeight: 44 }}
        >
          <option value="simple">Simple</option>
          <option value="guided">Guided</option>
          <option value="full">Full control</option>
          <option value="power_user">More control (power user)</option>
        </select>
      </label>
      <label style={{ display: 'block', marginTop: 12 }}>
        <span id="theme-label">Theme</span>
        <select
          aria-labelledby="theme-label"
          value={theme}
          onChange={e => onThemeChange(e.target.value)}
          style={{ marginLeft: 8, padding: 8, minHeight: 44 }}
        >
          {THEMES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
        </select>
      </label>
      <p style={{ fontSize: 13, color: '#9aa0a6', marginTop: 12 }}>
        Advanced settings are behind &quot;More control&quot;. Nothing here is a dead end.
      </p>
    </section>
  )
}
