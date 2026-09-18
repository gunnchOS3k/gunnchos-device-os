import { useState } from 'react'
import GunnchOSShell from './shell/GunnchOSShell'
import UserFocusedView from './user-focused/UserFocusedView'
import FleetView from './FleetView'
import CompleteExperienceShell from './cx2/CompleteExperienceShell'

type DevView = 'gunnchos' | 'fleet' | 'user-focused' | 'cx2'

export default function App() {
  const [devView, setDevView] = useState<DevView>('gunnchos')

  if (devView === 'gunnchos') {
    return (
      <GunnchOSShell
        devMode
        onOpenDevTools={() => setDevView('fleet')}
        onOpenCx2={() => setDevView('cx2')}
      />
    )
  }

  if (devView === 'user-focused') {
    return (
      <div>
        <DevBar current="user-focused" onSwitch={setDevView} />
        <UserFocusedView />
      </div>
    )
  }

  if (devView === 'cx2') {
    return (
      <div>
        <DevBar current="cx2" onSwitch={setDevView} />
        <div style={{ paddingTop: 40 }}>
          <CompleteExperienceShell onExit={() => setDevView('gunnchos')} />
        </div>
      </div>
    )
  }

  return (
    <div>
      <DevBar current="fleet" onSwitch={setDevView} />
      <FleetView />
    </div>
  )
}

function DevBar({ current, onSwitch }: { current: DevView; onSwitch: (v: DevView) => void }) {
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      zIndex: 999,
      display: 'flex',
      gap: 8,
      padding: '6px 12px',
      background: '#1a1a2e',
      borderBottom: '1px solid #333',
      fontSize: 12,
    }}>
      <span style={{ color: '#888', alignSelf: 'center' }}>Dev views:</span>
      {(['gunnchos', 'fleet', 'user-focused', 'cx2'] as DevView[]).map(v => (
        <button
          key={v}
          type="button"
          onClick={() => onSwitch(v)}
          style={{
            padding: '4px 10px',
            borderRadius: 4,
            border: current === v ? '1px solid #4a9eff' : '1px solid #444',
            background: current === v ? '#1e3a5f' : '#222',
            color: '#fff',
            cursor: 'pointer',
          }}
        >
          {v}
        </button>
      ))}
    </div>
  )
}
