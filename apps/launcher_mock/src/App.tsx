import { useState } from 'react'
import { DEVICES, MODES, DEVICE_ID_MAP, MODE_ID_MAP } from './deviceProfiles'
import { APPS } from './appRegistry'

const MOCK_TELEMETRY = {
  latency_ms: 12.5,
  jitter_ms: 1.2,
  packet_loss_pct: 0.05,
  qos: 'urllc_strict',
}

export default function App() {
  const [device, setDevice] = useState(DEVICES[0])
  const [mode, setMode] = useState(MODES[0])
  const deviceId = DEVICE_ID_MAP[device]
  const modeId = MODE_ID_MAP[mode]

  return (
    <div style={{ fontFamily: 'system-ui', padding: 24, maxWidth: 1100, margin: '0 auto', background: '#0f1419', color: '#e8eaed', minHeight: '100vh' }}>
      <h1 style={{ margin: 0 }}>gunnchOS Launcher</h1>
      <p style={{ color: '#9aa0a6' }}>IMT-2030-aligned research prototype · Not certified 6G hardware · Synthetic telemetry</p>

      <section style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 16 }}>
        <label>Device <select value={device} onChange={e => setDevice(e.target.value)}>{DEVICES.map(d => <option key={d}>{d}</option>)}</select></label>
        <label>Mode <select value={mode} onChange={e => setMode(e.target.value)}>{MODES.map(m => <option key={m}>{m}</option>)}</select></label>
      </section>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginTop: 20 }}>
        {APPS.map(app => (
          <button key={app} style={{ padding: 16, borderRadius: 12, border: '1px solid #3c4043', background: '#1a2332', color: '#fff', cursor: 'pointer' }}>{app}</button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 20 }}>
        <Panel title="Telemetry (mock)">
          <p>Device ID: {deviceId}</p>
          <p>Latency: {MOCK_TELEMETRY.latency_ms} ms · Jitter: {MOCK_TELEMETRY.jitter_ms} ms</p>
          <p>Packet loss: {MOCK_TELEMETRY.packet_loss_pct}% · QoS: {modeId === 'play' ? 'urllc_strict' : 'balanced'}</p>
        </Panel>
        <Panel title="Privacy">
          <p>Opt-in: active · No PII · Tier: synthetic_a</p>
          <p>Aligns with edge-io-measurement-node contract (research)</p>
        </Panel>
        <Panel title="Security / boot">
          <p>Secure boot: target · TPM2: target · Fleet lock: {modeId === 'school' || modeId === 'fleet_admin' ? 'on' : 'off'}</p>
        </Panel>
        <Panel title="Fleet / school">
          <p>Enrolled: 120 · Online: 98 · Policy: fleet-v0-mock</p>
        </Panel>
        <Panel title="Research links">
          <p>7GC export · Edge-IO session · AI-RAN / Beam / NTN labs</p>
          <p>Mode: {modeId}</p>
        </Panel>
        <Panel title="Deploy (DS-XL → device)">
          <p>Source: ds_xl_coder → Target: {deviceId}</p>
          <button style={btnStyle}>Deploy build-once package (mock)</button>
        </Panel>
      </div>

      <p style={{ marginTop: 24, fontSize: 13, color: '#9aa0a6' }}>
        Offline-ready ✓ · Wi-Fi 6E/7 stepping stone · Private 5G/6G modular roadmap — not operational 6G claims
      </p>
    </div>
  )
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ padding: 14, background: '#1e2a3a', borderRadius: 10, border: '1px solid #2d3a4d' }}>
      <h3 style={{ margin: '0 0 8px', fontSize: 14 }}>{title}</h3>
      <div style={{ fontSize: 13 }}>{children}</div>
    </div>
  )
}

const btnStyle: React.CSSProperties = { marginTop: 8, padding: '8px 12px', borderRadius: 8, border: 'none', background: '#4a9eff', color: '#000', cursor: 'pointer' }
