import { theme } from '../styles/gunnchosTheme'
import AppIcon from '../components/AppIcon'
import { GameLaunchMeta, GameLaunchResult } from '../services/gameLaunchService'

interface GameLaunchPanelProps {
  meta: GameLaunchMeta
  lastResult: GameLaunchResult | null
  onLaunch: () => void
  onBack: () => void
  accent: string
}

export default function GameLaunchPanel({ meta, lastResult, onLaunch, onBack, accent }: GameLaunchPanelProps) {
  const canLaunch = meta.readiness === 'playable_web_build'

  return (
    <div style={playCard} data-testid="game-launch-panel">
      <AppIcon name="game" size={64} color={accent} />
      <h2 style={{ margin: '20px 0 8px' }}>Game Launch</h2>
      <span data-testid="game-readiness" style={readinessBadge(meta.readiness)}>
        {meta.readiness.replace(/_/g, ' ')}
      </span>
      <p style={{ color: theme.textMuted, maxWidth: 420, textAlign: 'center', lineHeight: 1.5, marginTop: 12 }}>
        {meta.nextAction}
      </p>

      <section style={checklistSection} data-testid="launch-readiness-checklist">
        <h3 style={{ fontSize: 13, margin: '0 0 8px' }}>Launch readiness</h3>
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: theme.textMuted }}>
          <li>Build path: {meta.checklist.buildPath}</li>
          <li>Controller: {meta.checklist.controllerSupport}</li>
          <li>Save/load: {meta.checklist.saveLoad}</li>
          <li>Performance: {meta.checklist.performanceTarget}</li>
          <li>Offline: {meta.checklist.offlineSupport}</li>
        </ul>
      </section>

      <button
        type="button"
        style={{ ...launchBtn, background: canLaunch ? accent : theme.surfaceRaised, color: canLaunch ? '#000' : theme.textMuted }}
        onClick={onLaunch}
        data-testid="game-launch-button"
        disabled={!canLaunch}
      >
        {canLaunch ? 'Launch web build' : 'Not connected yet'}
      </button>

      {lastResult && (
        <p data-testid="game-launch-result" style={{ fontSize: 12, color: theme.textMuted, marginTop: 12 }}>
          {lastResult.message}
        </p>
      )}

      <p style={{ fontSize: 11, color: theme.textMuted, marginTop: 8 }}>
        Game launch adapter prototype — not a native sandbox launcher
      </p>
    </div>
  )
}

function readinessBadge(readiness: string): React.CSSProperties {
  return {
    padding: '4px 12px',
    borderRadius: 20,
    fontSize: 11,
    textTransform: 'capitalize',
    background: theme.surfaceRaised,
    border: `1px solid ${theme.border}`,
  }
}

const playCard: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: 40,
  borderRadius: 20,
  border: `2px solid ${theme.border}`,
  background: theme.surface,
  maxWidth: 520,
}

const checklistSection: React.CSSProperties = {
  width: '100%',
  marginTop: 16,
  padding: 12,
  background: theme.surfaceRaised,
  borderRadius: theme.radius,
}

const launchBtn: React.CSSProperties = {
  marginTop: 24,
  padding: '14px 32px',
  borderRadius: 12,
  border: 'none',
  fontWeight: 700,
  fontSize: 16,
  cursor: 'pointer',
  minWidth: 200,
}
