import { useState } from 'react'
import { theme } from '../styles/gunnchosTheme'
import { FIRST_PARTY_GAMES } from '../data/firstPartyGames'
import AppIcon from '../components/AppIcon'

interface GameModeProps {
  onExit: () => void
}

type PerfProfile = 'battery' | 'balanced' | 'performance'

export default function GameMode({ onExit }: GameModeProps) {
  const [selected, setSelected] = useState<string | null>(null)
  const [profile, setProfile] = useState<PerfProfile>('balanced')
  const [showOverlay, setShowOverlay] = useState(false)
  const [controllerConnected] = useState(true)

  const game = FIRST_PARTY_GAMES.find(g => g.id === selected)

  if (game) {
    return (
      <div style={gameShell}>
        <div style={{ ...gameHero, borderColor: game.accent }}>
          <button type="button" onClick={() => setSelected(null)} style={backBtn}>
            <AppIcon name="back" size={20} /> Library
          </button>
          <div style={{ textAlign: 'center', flex: 1 }}>
            <h1 style={{ margin: 0, fontSize: 32 }}>{game.title}</h1>
            <p style={{ color: theme.textMuted }}>{game.genre}</p>
          </div>
          <button type="button" onClick={onExit} style={exitBtn}>Exit Game Mode</button>
        </div>

        <div style={playArea}>
          <div style={{ ...playCard, borderColor: game.accent }}>
            <AppIcon name="game" size={64} color={game.accent} />
            <h2 style={{ margin: '20px 0 8px' }}>Prototype Launch</h2>
            <p style={{ color: theme.textMuted, maxWidth: 420, textAlign: 'center', lineHeight: 1.5 }}>
              {game.description}
            </p>
            <div style={badgeRow}>
              <Badge label={`${game.fpsTarget} FPS target`} />
              {game.offline && <Badge label="Offline play" />}
              {game.supportsController && <Badge label="Controller" />}
              {game.supportsTouch && <Badge label="Touch" />}
            </div>
            <button type="button" style={{ ...launchBtn, background: game.accent }}>
              Launch (mock)
            </button>
            <p style={{ fontSize: 12, color: theme.textMuted, marginTop: 12 }}>
              Vertical slice in Phase 4 · Save sync · Tournament mode coming
            </p>
          </div>

          {showOverlay && (
            <div style={fpsOverlay}>
              <span>60 FPS</span>
              <span>GPU 42%</span>
              <span>Battery 78%</span>
            </div>
          )}
        </div>

        <footer style={gameFooter}>
          <Toggle label="Performance overlay" checked={showOverlay} onChange={() => setShowOverlay(v => !v)} />
          <PerfSelector profile={profile} onChange={setProfile} />
        </footer>
      </div>
    )
  }

  return (
    <div style={gameShell}>
      <header style={gameHeader}>
        <div>
          <h1 style={{ margin: 0, fontSize: 28, color: theme.gameAccent }}>Game Mode</h1>
          <p style={{ color: theme.textMuted, margin: '4px 0 0' }}>
            {controllerConnected ? '🎮 Controller connected' : 'Touch navigation active'}
          </p>
        </div>
        <button type="button" onClick={onExit} style={exitBtn}>Exit to Campus</button>
      </header>

      <div style={heroBanner}>
        <h2 style={{ margin: 0, fontSize: 18 }}>First-party exclusives</h2>
        <p style={{ color: theme.textMuted, margin: '4px 0 0', fontSize: 14 }}>Built for GunnchOS handhelds</p>
      </div>

      <div style={gameGrid}>
        {FIRST_PARTY_GAMES.map(g => (
          <button
            key={g.id}
            type="button"
            onClick={() => setSelected(g.id)}
            style={{ ...gameTile, borderColor: g.accent }}
          >
            <div style={{ ...gameIconWrap, background: `${g.accent}22` }}>
              <AppIcon name="game" size={40} color={g.accent} />
            </div>
            <h3 style={{ margin: '12px 0 4px', fontSize: 16 }}>{g.title}</h3>
            <p style={{ margin: 0, fontSize: 13, color: theme.textMuted }}>{g.genre}</p>
            <div style={{ ...badgeRow, marginTop: 10, justifyContent: 'center' }}>
              <Badge label={`${g.fpsTarget} FPS`} small />
              {g.offline && <Badge label="Offline" small />}
            </div>
          </button>
        ))}
      </div>

      <section style={features}>
        <Feature icon="gamepad" title="Controller-first" desc="Full navigation with gamepad or touch" />
        <Feature icon="cloud" title="Cloud saves" desc="Sync progress across devices (Phase 3)" />
        <Feature icon="settings" title="Parental controls" desc="Guardian limits for younger players" />
        <Feature icon="screen" title="Battery saver" desc="Extend play time on the go" />
      </section>

      <footer style={gameFooter}>
        <PerfSelector profile={profile} onChange={setProfile} />
        <span style={{ fontSize: 13, color: theme.textMuted }}>Local multiplayer · Tournament mode · Phase 3</span>
      </footer>
    </div>
  )
}

function Badge({ label, small }: { label: string; small?: boolean }) {
  return (
    <span style={{
      padding: small ? '2px 8px' : '4px 10px',
      borderRadius: 20,
      fontSize: small ? 11 : 12,
      background: theme.surfaceRaised,
      border: `1px solid ${theme.border}`,
      color: theme.textMuted,
    }}>
      {label}
    </span>
  )
}

function Feature({ icon, title, desc }: { icon: string; title: string; desc: string }) {
  return (
    <div style={featureCard}>
      <AppIcon name={icon} size={24} color={theme.gameAccent} />
      <div>
        <strong style={{ fontSize: 14 }}>{title}</strong>
        <p style={{ margin: '2px 0 0', fontSize: 12, color: theme.textMuted }}>{desc}</p>
      </div>
    </div>
  )
}

function PerfSelector({ profile, onChange }: { profile: PerfProfile; onChange: (p: PerfProfile) => void }) {
  const options: { id: PerfProfile; label: string }[] = [
    { id: 'battery', label: 'Battery saver' },
    { id: 'balanced', label: 'Balanced' },
    { id: 'performance', label: 'Performance' },
  ]
  return (
    <div style={{ display: 'flex', gap: 6 }}>
      {options.map(o => (
        <button
          key={o.id}
          type="button"
          onClick={() => onChange(o.id)}
          style={{
            padding: '6px 12px',
            borderRadius: 20,
            border: `1px solid ${profile === o.id ? theme.gameAccent : theme.border}`,
            background: profile === o.id ? `${theme.gameAccent}33` : 'transparent',
            color: theme.text,
            fontSize: 12,
            cursor: 'pointer',
          }}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: () => void }) {
  return (
    <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer' }}>
      <input type="checkbox" checked={checked} onChange={onChange} />
      {label}
    </label>
  )
}

const gameShell: React.CSSProperties = {
  minHeight: '100vh',
  background: theme.gameBg,
  color: theme.text,
  fontFamily: theme.font,
  display: 'flex',
  flexDirection: 'column',
}

const gameHeader: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '20px 28px',
  borderBottom: `1px solid ${theme.border}`,
}

const heroBanner: React.CSSProperties = {
  padding: '16px 28px',
  background: `linear-gradient(90deg, ${theme.gameAccent}22, transparent)`,
}

const gameGrid: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
  gap: 16,
  padding: '20px 28px',
  flex: 1,
}

const gameTile: React.CSSProperties = {
  padding: 20,
  borderRadius: 16,
  border: '2px solid',
  background: theme.surface,
  color: theme.text,
  cursor: 'pointer',
  textAlign: 'center',
}

const gameIconWrap: React.CSSProperties = {
  width: 72,
  height: 72,
  borderRadius: 16,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  margin: '0 auto',
}

const badgeRow: React.CSSProperties = { display: 'flex', gap: 8, flexWrap: 'wrap' }

const features: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
  gap: 12,
  padding: '0 28px 20px',
}

const featureCard: React.CSSProperties = {
  display: 'flex',
  gap: 12,
  padding: 14,
  background: theme.surface,
  borderRadius: 12,
  border: `1px solid ${theme.border}`,
}

const gameFooter: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '14px 28px',
  borderTop: `1px solid ${theme.border}`,
  background: theme.surface,
}

const exitBtn: React.CSSProperties = {
  padding: '10px 16px',
  borderRadius: 8,
  border: `1px solid ${theme.border}`,
  background: theme.surfaceRaised,
  color: theme.text,
  cursor: 'pointer',
}

const backBtn: React.CSSProperties = { ...exitBtn, display: 'flex', alignItems: 'center', gap: 6 }

const gameHero: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  padding: '16px 28px',
  borderBottom: '2px solid',
  gap: 16,
}

const playArea: React.CSSProperties = {
  flex: 1,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  position: 'relative',
  padding: 32,
}

const playCard: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: 40,
  borderRadius: 20,
  border: '2px solid',
  background: theme.surface,
  maxWidth: 520,
}

const launchBtn: React.CSSProperties = {
  marginTop: 24,
  padding: '14px 32px',
  borderRadius: 12,
  border: 'none',
  color: '#000',
  fontWeight: 700,
  fontSize: 16,
  cursor: 'pointer',
  minWidth: 200,
}

const fpsOverlay: React.CSSProperties = {
  position: 'absolute',
  top: 16,
  right: 16,
  display: 'flex',
  gap: 12,
  padding: '8px 12px',
  background: 'rgba(0,0,0,0.7)',
  borderRadius: 8,
  fontSize: 12,
  fontFamily: 'monospace',
}
