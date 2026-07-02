import { useState } from 'react'
import { theme } from '../styles/gunnchosTheme'
import { StudentProfile } from '../data/studentProfile'
import AppIcon from '../components/AppIcon'

interface SettingsPanelProps {
  profile: StudentProfile
  onBack: () => void
  onResetOnboarding: () => void
}

type SettingsTab = 'profile' | 'display' | 'privacy' | 'network' | 'system'

export default function SettingsPanel({ profile, onBack, onResetOnboarding }: SettingsPanelProps) {
  const [tab, setTab] = useState<SettingsTab>('profile')
  const [largeText, setLargeText] = useState(profile.accessibility.includes('large_text'))
  const [highContrast, setHighContrast] = useState(profile.accessibility.includes('high_contrast'))
  const [offlineMode, setOfflineMode] = useState(profile.offline)
  const [aiPrivacy, setAiPrivacy] = useState(true)

  const tabs: { id: SettingsTab; label: string }[] = [
    { id: 'profile', label: 'Profile' },
    { id: 'display', label: 'Display' },
    { id: 'privacy', label: 'Privacy' },
    { id: 'network', label: 'Network' },
    { id: 'system', label: 'System' },
  ]

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <aside style={sidebar}>
        <button type="button" onClick={onBack} style={backBtn}>
          <AppIcon name="back" size={18} /> Campus
        </button>
        <h1 style={{ fontSize: 20, margin: '16px 0' }}>Settings</h1>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {tabs.map(t => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              style={{
                ...navBtn,
                background: tab === t.id ? theme.accentMuted : 'transparent',
                borderLeft: tab === t.id ? `3px solid ${theme.accent}` : '3px solid transparent',
              }}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </aside>

      <main style={{ flex: 1, padding: 24, overflow: 'auto' }}>
        {tab === 'profile' && (
          <>
            <SettingGroup title="Student profile">
              <SettingRow label="Name" value={profile.displayName || '—'} />
              <SettingRow label="Profile type" value={profile.who.replace('_', ' ')} />
              <SettingRow label="Primary goal" value={profile.goal} />
              <SettingRow label="UI depth" value={profile.control} />
              <SettingRow label="Guardian controls" value={profile.guardian ? 'On' : 'Off'} />
            </SettingGroup>
            <button type="button" onClick={onResetOnboarding} style={dangerBtn}>
              Re-run first boot setup
            </button>
          </>
        )}

        {tab === 'display' && (
          <>
            <SettingGroup title="Accessibility">
              <Toggle label="Large text" checked={largeText} onChange={() => setLargeText(v => !v)} />
              <Toggle label="High contrast" checked={highContrast} onChange={() => setHighContrast(v => !v)} />
              <Toggle label="Reduced motion" checked={false} onChange={() => {}} />
              <Toggle label="Dyslexia-friendly reading" checked={profile.accessibility.includes('dyslexia')} onChange={() => {}} />
            </SettingGroup>
            <SettingGroup title="Language">
              <SettingRow label="Interface" value="English" />
              <p style={{ fontSize: 13, color: theme.textMuted }}>Spanish, Arabic, French, Finnish — Phase 1</p>
            </SettingGroup>
          </>
        )}

        {tab === 'privacy' && (
          <>
            <SettingGroup title="Student data">
              <Toggle label="AI privacy mode — no training on my data" checked={aiPrivacy} onChange={() => setAiPrivacy(v => !v)} />
              <SettingRow label="Camera indicator" value="Always visible when active" />
              <SettingRow label="Microphone indicator" value="Always visible when active" />
              <SettingRow label="App permissions" value="Per-app sandbox" />
            </SettingGroup>
            <SettingGroup title="Profiles">
              <SettingRow label="Guest mode" value="Available" />
              <SettingRow label="School mode" value="Configurable by admin" />
              <SettingRow label="Data export" value="Available" />
            </SettingGroup>
          </>
        )}

        {tab === 'network' && (
          <>
            <SettingGroup title="Connectivity">
              <Toggle label="Offline-first mode" checked={offlineMode} onChange={() => setOfflineMode(v => !v)} />
              <SettingRow label="Wi-Fi" value="Connected (mock)" />
              <SettingRow label="Bluetooth" value="Keyboard + controller paired" />
              <SettingRow label="Cloud backup" value="Enabled" />
            </SettingGroup>
          </>
        )}

        {tab === 'system' && (
          <>
            <SettingGroup title="Device">
              <SettingRow label="OS version" value="GunnchOS 0.1 (Phase 0 prototype)" />
              <SettingRow label="Storage" value="128 GB · 42 GB free (mock)" />
              <SettingRow label="RAM" value="16 GB (mock)" />
              <SettingRow label="Secure boot" value="Target — not verified on this build" />
            </SettingGroup>
            <SettingGroup title="Updates">
              <SettingRow label="Last update" value="System image 0.1.0-prototype" />
              <SettingRow label="Rollback" value="Available after failed update" />
              <button type="button" style={primaryBtn}>Check for updates (mock)</button>
            </SettingGroup>
          </>
        )}
      </main>
    </div>
  )
}

function SettingGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginBottom: 28 }}>
      <h2 style={{ fontSize: 14, color: theme.textMuted, textTransform: 'uppercase', margin: '0 0 12px' }}>{title}</h2>
      <div style={{ background: theme.surfaceRaised, borderRadius: theme.radius, border: `1px solid ${theme.border}` }}>
        {children}
      </div>
    </section>
  )
}

function SettingRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={row}>
      <span>{label}</span>
      <span style={{ color: theme.textMuted }}>{value}</span>
    </div>
  )
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: () => void }) {
  return (
    <button type="button" onClick={onChange} style={{ ...row, width: '100%', cursor: 'pointer', border: 'none', background: 'transparent', color: theme.text }}>
      <span>{label}</span>
      <span style={{
        width: 44,
        height: 24,
        borderRadius: 12,
        background: checked ? theme.accent : theme.border,
        position: 'relative',
        flexShrink: 0,
      }}>
        <span style={{
          position: 'absolute',
          top: 2,
          left: checked ? 22 : 2,
          width: 20,
          height: 20,
          borderRadius: '50%',
          background: '#fff',
          transition: 'left 0.15s',
        }} />
      </span>
    </button>
  )
}

const sidebar: React.CSSProperties = {
  width: 220,
  padding: 16,
  borderRight: `1px solid ${theme.border}`,
  background: theme.surface,
}

const backBtn: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 6,
  padding: '8px 10px',
  borderRadius: 8,
  border: `1px solid ${theme.border}`,
  background: theme.surfaceRaised,
  color: theme.text,
  cursor: 'pointer',
  fontSize: 13,
}

const navBtn: React.CSSProperties = {
  padding: '10px 12px',
  border: 'none',
  borderRadius: 8,
  color: theme.text,
  cursor: 'pointer',
  textAlign: 'left',
  fontSize: 14,
}

const row: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '14px 16px',
  borderBottom: `1px solid ${theme.border}`,
  fontSize: 14,
}

const primaryBtn: React.CSSProperties = {
  margin: '12px 16px',
  padding: '10px 16px',
  borderRadius: 8,
  border: 'none',
  background: theme.accent,
  color: '#000',
  fontWeight: 600,
  cursor: 'pointer',
}

const dangerBtn: React.CSSProperties = {
  padding: '10px 16px',
  borderRadius: 8,
  border: `1px solid ${theme.danger}`,
  background: 'transparent',
  color: theme.danger,
  cursor: 'pointer',
}
