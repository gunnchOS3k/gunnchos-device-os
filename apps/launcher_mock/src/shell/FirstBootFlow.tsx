import { useState } from 'react'
import { theme } from '../styles/gunnchosTheme'
import {
  StudentProfile,
  WHO_OPTIONS,
  GOAL_OPTIONS,
  CONTROL_OPTIONS,
  ACCESSIBILITY_OPTIONS,
} from '../data/studentProfile'

interface FirstBootFlowProps {
  onComplete: (profile: StudentProfile) => void
}

type Step = 'welcome' | 'who' | 'goal' | 'control' | 'accessibility' | 'offline' | 'name' | 'done'

export default function FirstBootFlow({ onComplete }: FirstBootFlowProps) {
  const [step, setStep] = useState<Step>('welcome')
  const [profile, setProfile] = useState<StudentProfile>({
    displayName: '',
    who: 'college',
    goal: 'all',
    control: 'guided',
    accessibility: [],
    offline: false,
    guardian: false,
    onboarded: false,
  })

  const next = (updates: Partial<StudentProfile>, nextStep: Step) => {
    setProfile(p => ({ ...p, ...updates }))
    setStep(nextStep)
  }

  const finish = () => {
    onComplete({ ...profile, onboarded: true })
  }

  const toggleA11y = (id: string) => {
    setProfile(p => ({
      ...p,
      accessibility: p.accessibility.includes(id)
        ? p.accessibility.filter(x => x !== id)
        : [...p.accessibility, id],
    }))
  }

  return (
    <div style={shell}>
      <div style={card}>
        <div style={logo}>G</div>
        <h1 style={{ margin: '0 0 8px', fontSize: 28 }}>Welcome to GunnchOS</h1>
        <p style={{ color: theme.textMuted, margin: '0 0 24px' }}>
          Education-first · Creator-first · Gamer-first
        </p>

        {step === 'welcome' && (
          <>
            <p style={{ lineHeight: 1.6 }}>
              One affordable device for school, coding, creativity, STEM labs, and games.
              Let&apos;s set up your student profile — this takes about a minute.
            </p>
            <ActionButton label="Get started" onClick={() => setStep('who')} />
          </>
        )}

        {step === 'who' && (
          <>
            <StepTitle>Who is this device for?</StepTitle>
            <OptionGrid
              options={WHO_OPTIONS}
              selected={profile.who}
              onSelect={id => next({ who: id }, 'goal')}
            />
          </>
        )}

        {step === 'goal' && (
          <>
            <StepTitle>What do you want to do first?</StepTitle>
            <OptionGrid
              options={GOAL_OPTIONS}
              selected={profile.goal}
              onSelect={id => next({ goal: id }, 'control')}
            />
          </>
        )}

        {step === 'control' && (
          <>
            <StepTitle>How much control do you want?</StepTitle>
            <OptionGrid
              options={CONTROL_OPTIONS}
              selected={profile.control}
              onSelect={id => next({ control: id as StudentProfile['control'] }, 'accessibility')}
            />
          </>
        )}

        {step === 'accessibility' && (
          <>
            <StepTitle>Accessibility support needed?</StepTitle>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {ACCESSIBILITY_OPTIONS.map(opt => (
                <ToggleRow
                  key={opt.id}
                  label={opt.label}
                  checked={profile.accessibility.includes(opt.id)}
                  onToggle={() => toggleA11y(opt.id)}
                />
              ))}
            </div>
            <ActionButton label="Continue" onClick={() => setStep('offline')} />
          </>
        )}

        {step === 'offline' && (
          <>
            <StepTitle>Will you use this offline often?</StepTitle>
            <ToggleRow
              label="Yes — prioritize offline tools and local storage"
              checked={profile.offline}
              onToggle={() => setProfile(p => ({ ...p, offline: !p.offline }))}
            />
            <ToggleRow
              label="Guardian controls needed (for younger users)"
              checked={profile.guardian}
              onToggle={() => setProfile(p => ({ ...p, guardian: !p.guardian }))}
            />
            <ActionButton label="Continue" onClick={() => setStep('name')} />
          </>
        )}

        {step === 'name' && (
          <>
            <StepTitle>What should we call you?</StepTitle>
            <input
              type="text"
              value={profile.displayName}
              onChange={e => setProfile(p => ({ ...p, displayName: e.target.value }))}
              placeholder="Your name"
              style={inputStyle}
              autoFocus
            />
            <ActionButton
              label="Enter Campus Mode"
              onClick={finish}
              disabled={!profile.displayName.trim()}
            />
          </>
        )}

        <Progress step={step} />
      </div>
    </div>
  )
}

function StepTitle({ children }: { children: React.ReactNode }) {
  return <h2 style={{ margin: '0 0 16px', fontSize: 20 }}>{children}</h2>
}

function OptionGrid({
  options,
  selected,
  onSelect,
}: {
  options: { id: string; label: string }[]
  selected: string
  onSelect: (id: string) => void
}) {
  return (
    <div style={{ display: 'grid', gap: 10 }}>
      {options.map(opt => (
        <button
          key={opt.id}
          type="button"
          onClick={() => onSelect(opt.id)}
          style={{
            padding: '14px 16px',
            minHeight: theme.touchMin,
            borderRadius: theme.radius,
            border: selected === opt.id ? `2px solid ${theme.accent}` : `1px solid ${theme.border}`,
            background: selected === opt.id ? theme.accentMuted : theme.surfaceRaised,
            color: theme.text,
            cursor: 'pointer',
            textAlign: 'left',
            fontSize: 16,
          }}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}

function ToggleRow({
  label,
  checked,
  onToggle,
}: {
  label: string
  checked: boolean
  onToggle: () => void
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '12px 16px',
        minHeight: theme.touchMin,
        borderRadius: theme.radius,
        border: `1px solid ${theme.border}`,
        background: checked ? theme.accentMuted : theme.surfaceRaised,
        color: theme.text,
        cursor: 'pointer',
        textAlign: 'left',
        width: '100%',
      }}
    >
      <span style={{
        width: 22,
        height: 22,
        borderRadius: 6,
        border: `2px solid ${checked ? theme.accent : theme.border}`,
        background: checked ? theme.accent : 'transparent',
        flexShrink: 0,
      }} />
      {label}
    </button>
  )
}

function ActionButton({
  label,
  onClick,
  disabled,
}: {
  label: string
  onClick: () => void
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      style={{
        marginTop: 20,
        width: '100%',
        padding: '14px 20px',
        minHeight: theme.touchMin,
        borderRadius: theme.radius,
        border: 'none',
        background: disabled ? theme.border : theme.accent,
        color: disabled ? theme.textMuted : '#000',
        fontWeight: 600,
        fontSize: 16,
        cursor: disabled ? 'not-allowed' : 'pointer',
      }}
    >
      {label}
    </button>
  )
}

const STEPS: Step[] = ['welcome', 'who', 'goal', 'control', 'accessibility', 'offline', 'name']

function Progress({ step }: { step: Step }) {
  const idx = STEPS.indexOf(step)
  return (
    <div style={{ display: 'flex', gap: 6, marginTop: 24, justifyContent: 'center' }}>
      {STEPS.map((s, i) => (
        <div
          key={s}
          style={{
            width: i <= idx ? 24 : 8,
            height: 4,
            borderRadius: 2,
            background: i <= idx ? theme.accent : theme.border,
            transition: 'width 0.2s',
          }}
        />
      ))}
    </div>
  )
}

const shell: React.CSSProperties = {
  minHeight: '100vh',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  background: `radial-gradient(ellipse at top, ${theme.accentMuted} 0%, ${theme.bg} 60%)`,
  fontFamily: theme.font,
  color: theme.text,
  padding: 24,
}

const card: React.CSSProperties = {
  width: '100%',
  maxWidth: 480,
  padding: 32,
  background: theme.surface,
  borderRadius: 16,
  border: `1px solid ${theme.border}`,
}

const logo: React.CSSProperties = {
  width: 56,
  height: 56,
  borderRadius: 14,
  background: `linear-gradient(135deg, ${theme.accent}, ${theme.gameAccent})`,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: 28,
  fontWeight: 700,
  color: '#fff',
  marginBottom: 16,
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '14px 16px',
  borderRadius: theme.radius,
  border: `1px solid ${theme.border}`,
  background: theme.surfaceRaised,
  color: theme.text,
  fontSize: 16,
  boxSizing: 'border-box',
}
