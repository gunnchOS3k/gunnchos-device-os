import { useState } from 'react'
import { DEVICES, MODES, DEVICE_ID_MAP, MODE_ID_MAP } from './deviceProfiles'
import { APPS } from './appRegistry'

const CAMPUSES = ['Gary', 'Ghana', 'Guyana', 'Gaza', 'Geelong', 'Graham Land', 'Germany'] as const
const CAMPUS_BLURBS: Record<string, { mode: string; privacy: string; waike: string; edge: string }> = {
  Gary: { mode: 'school / community', privacy: 'aggregate telemetry', waike: 'youth builder track', edge: 'library kiosk safe' },
  Ghana: { mode: 'low-bandwidth research', privacy: 'mobile-money hygiene', waike: 'workforce track', edge: 'solar hub aggregate' },
  Guyana: { mode: 'hinterland resilience', privacy: 'community-governed data', waike: 'e-government navigator', edge: 'flood-mode restrictions' },
  Gaza: { mode: 'crisis privacy', privacy: 'no location tracking', waike: 'remote education continuity', edge: 'remote-first only' },
  Geelong: { mode: 'accessibility-first', privacy: 'a11y checks enabled', waike: 'creative-tech studio', edge: 'inclusive metrics' },
  'Graham Land': { mode: 'offline science', privacy: 'no human monitoring', waike: 'polar operator track', edge: 'delay simulation' },
  Germany: { mode: 'privacy lab', privacy: 'GDPR-minimized', waike: 'Industry 4.0 apprentice', edge: 'audit-friendly exports' },
}

const MOCK_TELEMETRY = {
  latency_ms: 12.5,
  jitter_ms: 1.2,
  packet_loss_pct: 0.05,
  qos: 'urllc_strict',
}

export default function FleetView() {
  const [device, setDevice] = useState(DEVICES[0])
  const [mode, setMode] = useState(MODES[0])
  const [campus, setCampus] = useState<string>(CAMPUSES[0])
  const campusInfo = CAMPUS_BLURBS[campus] ?? CAMPUS_BLURBS.Gary
  const deviceId = DEVICE_ID_MAP[device]
  const modeId = MODE_ID_MAP[mode]

  return (
    <div style={{ fontFamily: 'system-ui', padding: 24, paddingTop: 48, maxWidth: 1100, margin: '0 auto', background: '#0f1419', color: '#e8eaed', minHeight: '100vh' }}>
      <div>
        <h1 style={{ margin: 0 }}>gunnchOS Fleet Launcher</h1>
        <p style={{ color: '#9aa0a6' }}>Research prototype · 7GC campus deployment · Synthetic telemetry</p>
      </div>

      <section style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 16 }}>
        <label>7GC Campus <select value={campus} onChange={e => setCampus(e.target.value)}>{CAMPUSES.map(c => <option key={c}>{c}</option>)}</select></label>
        <label>Device <select value={device} onChange={e => setDevice(e.target.value)}>{DEVICES.map(d => <option key={d}>{d}</option>)}</select></label>
        <label>Mode <select value={mode} onChange={e => setMode(e.target.value)}>{MODES.map(m => <option key={m}>{m}</option>)}</select></label>
      </section>
      <div style={{ marginTop: 12, padding: 12, background: '#1a2332', borderRadius: 10, fontSize: 13 }}>
        <strong>{campus}</strong> — recommended: {campusInfo.mode} · {campusInfo.privacy} · WAIKE: {campusInfo.waike} · Edge-IO: {campusInfo.edge}
      </div>

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
        </Panel>
        <Panel title="Security / boot">
          <p>Secure boot: target · TPM2: target · Fleet lock: {modeId === 'school' || modeId === 'fleet_admin' ? 'on' : 'off'}</p>
        </Panel>
        <Panel title="Fleet / school">
          <p>Enrolled: 120 · Online: 98 · Policy: fleet-v0-mock</p>
        </Panel>
      </div>
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
