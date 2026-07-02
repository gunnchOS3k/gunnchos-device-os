import { getModePolicy } from '../hooks/useLauncherContract'

export type PolicyDecision =
  | 'allowed'
  | 'blocked_by_mode'
  | 'blocked_by_guardian'
  | 'blocked_by_school'
  | 'unavailable'
  | 'warning_only'

export interface PolicyContext {
  schoolModeDefault?: string
  requiresNetwork?: boolean
  offlineSupported?: boolean
  isNativeShellApp?: boolean
  isFirstPartyGame?: boolean
}

export interface PolicyResult {
  decision: PolicyDecision
  appId: string
  mode: string
  message: string
  canLaunch: boolean
}

const CAMPUS_NATIVE = new Set(['files', 'notes', 'browser', 'settings', 'game-mode', 'media-mode'])
const GUARDIAN_BLOCKED = new Set(['chatgpt', 'cursor-web', 'netflix', 'hulu', 'steam'])
const SCHOOL_BLOCKED = new Set(['chatgpt', 'cursor-web', 'vscode', 'terminal', 'netflix', 'hulu', 'steam'])

const POLICY_ID_MAP: Record<string, string> = {
  'vscode-web': 'vscode',
  'cursor-web': 'vscode',
  github: 'git_placeholder',
  drive: 'browser',
  docs: 'browser',
  sheets: 'browser',
  slides: 'browser',
  email: 'browser',
  calendar: 'browser',
  d2l: 'browser',
  notebooklm: 'browser',
  chatgpt: 'chatgpt',
  terminal: 'terminal',
  jupyter: 'vscode',
}

export function resolvePolicyAppId(appId: string): string {
  return POLICY_ID_MAP[appId] ?? appId
}

export function evaluateAppPolicy(
  appId: string,
  mode: string,
  context: PolicyContext = {},
): PolicyResult {
  const policyAppId = resolvePolicyAppId(appId)
  const pol = getModePolicy(mode)

  if (context.isFirstPartyGame) {
    if (mode === 'School' || mode === 'Guardian') {
      return {
        decision: 'warning_only',
        appId,
        mode,
        message: `${appId} allowed in Game Mode with guardian awareness in ${mode} context`,
        canLaunch: true,
      }
    }
    return { decision: 'allowed', appId, mode, message: 'First-party game allowed', canLaunch: true }
  }

  if (context.isNativeShellApp || CAMPUS_NATIVE.has(appId)) {
    if (pol?.blocked_apps.includes(policyAppId)) {
      return blocked(mode, appId, policyAppId, 'blocked_by_mode')
    }
    return { decision: 'allowed', appId, mode, message: 'Native shell app allowed', canLaunch: true }
  }

  if (mode === 'School' && (SCHOOL_BLOCKED.has(appId) || context.schoolModeDefault === 'blocked')) {
    return blocked(mode, appId, policyAppId, 'blocked_by_school')
  }

  if (mode === 'Guardian' && GUARDIAN_BLOCKED.has(appId)) {
    return blocked(mode, appId, policyAppId, 'blocked_by_guardian')
  }

  if (mode === 'Offline' && context.requiresNetwork && !context.offlineSupported) {
    return blocked(mode, appId, policyAppId, 'blocked_by_mode', 'Streaming unavailable in Offline Mode')
  }

  if (pol?.blocked_apps.includes(policyAppId)) {
    const decision = mode === 'School' ? 'blocked_by_school' : mode === 'Guardian' ? 'blocked_by_guardian' : 'blocked_by_mode'
    return blocked(mode, appId, policyAppId, decision)
  }

  if (pol?.allowed_apps.length && !pol.allowed_apps.includes(policyAppId)) {
    if (policyAppId === 'browser' || pol.allowed_apps.includes('browser')) {
      return { decision: 'allowed', appId, mode, message: 'Allowed via browser route', canLaunch: true }
    }
    if (CAMPUS_NATIVE.has(appId)) {
      return { decision: 'allowed', appId, mode, message: 'Campus native app', canLaunch: true }
    }
    return blocked(mode, appId, policyAppId, 'blocked_by_mode')
  }

  if (mode === 'Library' && ['netflix', 'hulu', 'youtube'].includes(appId)) {
    return {
      decision: 'warning_only',
      appId,
      mode,
      message: 'Library Mode: personal login warning — no saved passwords by default',
      canLaunch: true,
    }
  }

  return { decision: 'allowed', appId, mode, message: 'Allowed', canLaunch: true }
}

function blocked(
  mode: string,
  appId: string,
  policyAppId: string,
  decision: PolicyDecision,
  customMessage?: string,
): PolicyResult {
  return {
    decision,
    appId,
    mode,
    message: customMessage ?? `${policyAppId} is blocked in ${mode} Mode`,
    canLaunch: false,
  }
}

export const DEPLOYMENT_MODE_KEY = 'gunnchos-deployment-mode'

export const DEPLOYMENT_MODES = [
  'Media',
  'School',
  'Library',
  'Guardian',
  'Offline',
  'Developer',
  'Play',
] as const

export type DeploymentMode = (typeof DEPLOYMENT_MODES)[number]

export function loadDeploymentMode(): DeploymentMode {
  const raw = localStorage.getItem(DEPLOYMENT_MODE_KEY)
  if (raw && DEPLOYMENT_MODES.includes(raw as DeploymentMode)) {
    return raw as DeploymentMode
  }
  return 'Media'
}

export function saveDeploymentMode(mode: DeploymentMode): void {
  localStorage.setItem(DEPLOYMENT_MODE_KEY, mode)
}

export function resolveDeploymentMode(profile: { offline?: boolean; guardian?: boolean }): DeploymentMode {
  if (profile.offline) return 'Offline'
  if (profile.guardian) return 'Guardian'
  return loadDeploymentMode()
}
