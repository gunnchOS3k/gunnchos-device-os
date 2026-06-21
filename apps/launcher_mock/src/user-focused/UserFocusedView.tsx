import { useState } from 'react'
import PersonaSelector from './PersonaSelector'
import JourneyPresetSelector from './JourneyPresetSelector'
import CustomizationPanel from './CustomizationPanel'
import AccessibilityPanel from './AccessibilityPanel'
import AppPackSelector from './AppPackSelector'
import WorkspaceHome from './WorkspaceHome'
import GuardianPanel from './GuardianPanel'
import OfflineModePanel from './OfflineModePanel'
import { PERSONAS, PersonaId } from './personaData'
import { PresetId } from './presetData'
import { APP_PACKS } from './AppPackSelector'

type Tab = 'persona' | 'journey' | 'customize' | 'accessibility' | 'apps' | 'home' | 'guardian' | 'offline'

export default function UserFocusedView() {
  const [tab, setTab] = useState<Tab>('persona')
  const [persona, setPersona] = useState<PersonaId>('high_school_student')
  const [preset, setPreset] = useState<PresetId>('car')
  const [depth, setDepth] = useState<'simple' | 'guided' | 'full' | 'power_user'>('guided')
  const [theme, setTheme] = useState('default')
  const [highContrast, setHighContrast] = useState(false)
  const [largeText, setLargeText] = useState(false)
  const [reducedMotion, setReducedMotion] = useState(false)
  const [appPack, setAppPack] = useState('learn_pack')
  const [guardian, setGuardian] = useState(false)
  const [offline, setOffline] = useState(false)

  const personaMeta = PERSONAS.find(p => p.id === persona)
  const packMeta = APP_PACKS.find(p => p.id === appPack)
  const fontScale = largeText ? 1.25 : 1
  const bg = highContrast ? '#000' : '#0f1419'
  const fg = highContrast ? '#fff' : '#e8eaed'

  const onPersonaSelect = (id: PersonaId) => {
    setPersona(id)
    const p = PERSONAS.find(x => x.id === id)
    if (p) setPreset(p.preset as PresetId)
    setTab('journey')
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'persona', label: 'Who' },
    { id: 'journey', label: 'Journey' },
    { id: 'customize', label: 'Customize' },
    { id: 'accessibility', label: 'Accessibility' },
    { id: 'apps', label: 'Apps' },
    { id: 'home', label: 'Home' },
    { id: 'guardian', label: 'Guardian' },
    { id: 'offline', label: 'Offline' },
  ]

  return (
    <div style={{
      fontFamily: 'system-ui',
      padding: 24,
      maxWidth: 1100,
      margin: '0 auto',
      background: bg,
      color: fg,
      minHeight: '100vh',
      fontSize: `${fontScale}rem`,
    }}>
      <h1 style={{ margin: 0 }}>gunnchOS — Your Device</h1>
      <p style={{ color: highContrast ? '#ccc' : '#9aa0a6' }}>
        User-focused OS alpha · Scooter to spaceship · Not a finished shipping OS
      </p>

      <nav aria-label="User-focused sections" style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 16 }}>
        {tabs.map(t => (
          <button
            key={t.id}
            type="button"
            aria-label={`Go to ${t.label}`}
            aria-current={tab === t.id ? 'page' : undefined}
            onClick={() => setTab(t.id)}
            style={{
              padding: '10px 16px',
              minHeight: 44,
              borderRadius: 8,
              border: tab === t.id ? '2px solid #4a9eff' : '1px solid #3c4043',
              background: tab === t.id ? '#1e3a5f' : '#1a2332',
              color: fg,
              cursor: 'pointer',
            }}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div style={{ marginTop: 24 }}>
        {tab === 'persona' && (
          <PersonaSelector selected={persona} onSelect={onPersonaSelect} reducedMotion={reducedMotion} />
        )}
        {tab === 'journey' && (
          <JourneyPresetSelector selected={preset} onSelect={setPreset} highContrast={highContrast} />
        )}
        {tab === 'customize' && (
          <CustomizationPanel depth={depth} onDepthChange={setDepth} theme={theme} onThemeChange={setTheme} />
        )}
        {tab === 'accessibility' && (
          <AccessibilityPanel
            highContrast={highContrast}
            largeText={largeText}
            reducedMotion={reducedMotion}
            onToggle={key => {
              if (key === 'highContrast') setHighContrast(v => !v)
              if (key === 'largeText') setLargeText(v => !v)
              if (key === 'reducedMotion') setReducedMotion(v => !v)
            }}
          />
        )}
        {tab === 'apps' && <AppPackSelector selected={appPack} onSelect={setAppPack} />}
        {tab === 'home' && (
          <WorkspaceHome
            preset={preset}
            workspace={personaMeta?.label ?? 'Default'}
            apps={packMeta?.apps ?? ['browser']}
          />
        )}
        {tab === 'guardian' && <GuardianPanel enabled={guardian} onToggle={() => setGuardian(v => !v)} />}
        {tab === 'offline' && <OfflineModePanel enabled={offline} onToggle={() => setOffline(v => !v)} />}
      </div>

      <p style={{ marginTop: 24, fontSize: 13, color: highContrast ? '#ccc' : '#9aa0a6' }}>
        One clear action per screen · Large touch targets · Accessible labels · No color-only meaning
      </p>
    </div>
  )
}
