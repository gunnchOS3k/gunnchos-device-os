import { theme } from '../styles/gunnchosTheme'
import { DEPLOYMENT_MODES, DeploymentMode } from '../services/policyEnforcementService'

interface ModeSelectorBarProps {
  mode: DeploymentMode
  onChange: (mode: DeploymentMode) => void
}

export default function ModeSelectorBar({ mode, onChange }: ModeSelectorBarProps) {
  return (
    <div
      data-testid="deployment-mode-selector"
      style={{
        padding: '8px 16px',
        borderBottom: `1px solid ${theme.border}`,
        background: theme.surfaceRaised,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        fontSize: 12,
      }}
    >
      <span style={{ color: theme.textMuted }}>Policy test mode:</span>
      <select
        aria-label="Deployment mode for policy testing"
        value={mode}
        onChange={e => onChange(e.target.value as DeploymentMode)}
        style={{
          padding: '4px 8px',
          borderRadius: 6,
          border: `1px solid ${theme.border}`,
          background: theme.surface,
          color: theme.text,
        }}
      >
        {DEPLOYMENT_MODES.map(m => (
          <option key={m} value={m}>{m}</option>
        ))}
      </select>
      <span style={{ color: theme.textMuted }}>Shell-level policy prototype — not production MDM</span>
    </div>
  )
}
