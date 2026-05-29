import { useState } from 'react'
import { DEVICES, MODES } from './deviceProfiles'
import { APPS, WAIKE_LEARNING } from './appRegistry'

export default function App() {
  const [device, setDevice] = useState(DEVICES[0])
  const [mode, setMode] = useState(MODES[0])
  return (
    <div style={{ fontFamily: 'system-ui', padding: 24, maxWidth: 960, margin: '0 auto' }}>
      <h1>gunnchOS Launcher (Mock)</h1>
      <p style={{ color: '#666' }}>Research prototype — not a certified consumer product OS.</p>
      <section>
        <label>Device </label>
        <select value={device} onChange={e => setDevice(e.target.value)}>{DEVICES.map(d => <option key={d}>{d}</option>)}</select>
        <label style={{ marginLeft: 16 }}>Mode </label>
        <select value={mode} onChange={e => setMode(e.target.value)}>{MODES.map(m => <option key={m}>{m}</option>)}</select>
      </section>
      <p style={{ marginTop: 12 }}><strong>Offline mode ready</strong> ✓</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12, marginTop: 16 }}>
        {APPS.map(app => (
          <button key={app} style={{ padding: 24, borderRadius: 12, border: '1px solid #ccc', cursor: 'pointer' }}>{app}</button>
        ))}
      </div>
      <h2 style={{ marginTop: 24 }}>WAIKE + gunnchAI3k Learning</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 12 }}>
        {WAIKE_LEARNING.map(item => (
          <button key={item} style={{ padding: 16, borderRadius: 10, border: '1px solid #9cf', background: '#f0f8ff', cursor: 'pointer' }}>{item}</button>
        ))}
      </div>
      <div style={{ marginTop: 24, padding: 16, background: '#f5f5f5', borderRadius: 8 }}>
        <h3>Deploy from DS-XL (mock)</h3>
        <p>Target: {device} · Transport: Wi-Fi / USB-C</p>
        <button>Deploy build-once package</button>
      </div>
      <div style={{ marginTop: 16, padding: 16, background: '#eef6ff', borderRadius: 8 }}>
        <h3>Privacy-safe telemetry (mock)</h3>
        <p>Opt-in only · No PII · Aggregated metrics for 7GC research mode</p>
      </div>
    </div>
  )
}
