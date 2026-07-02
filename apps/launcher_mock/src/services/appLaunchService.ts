import { getModePolicy } from '../hooks/useLauncherContract'

export type LaunchType = 'external_url' | 'internal_route' | 'local_app' | 'unavailable'

export type LaunchResultStatus =
  | 'launched'
  | 'blocked_by_policy'
  | 'missing_url'
  | 'unsupported'

export interface AppLaunchTarget {
  id: string
  name: string
  launchType: LaunchType
  url?: string
  internalRoute?: string
  localAppId?: string
  policyAppId?: string
}

export interface AppLaunchResult {
  status: LaunchResultStatus
  targetId: string
  message: string
  openedUrl?: string
}

/** Map PWA hub ids to contract app ids for mode policy checks. */
const POLICY_APP_MAP: Record<string, string> = {
  'vscode-web': 'vscode',
  'cursor-web': 'vscode',
  chatgpt: 'chatgpt',
  github: 'git_placeholder',
}

const SCHOOL_BLOCKED_PWA = new Set(['chatgpt', 'cursor-web'])

function isPolicyAllowed(policyAppId: string, mode: string): { allowed: boolean; reason?: string } {
  const pol = getModePolicy(mode)
  if (!pol) return { allowed: true }

  if (pol.blocked_apps.includes(policyAppId)) {
    return { allowed: false, reason: `${policyAppId} is blocked in ${mode} Mode` }
  }

  if (pol.allowed_apps.length > 0 && !pol.allowed_apps.includes(policyAppId)) {
    if (policyAppId === 'browser' || pol.allowed_apps.includes('browser')) {
      return { allowed: true }
    }
    return { allowed: false, reason: `${policyAppId} is not allowed in ${mode} Mode` }
  }

  return { allowed: true }
}

function checkPolicy(target: AppLaunchTarget, mode: string): { allowed: boolean; reason?: string } {
  const policyAppId = target.policyAppId ?? POLICY_APP_MAP[target.id] ?? 'browser'

  if ((mode === 'School' || mode === 'Guardian') && SCHOOL_BLOCKED_PWA.has(target.id)) {
    return { allowed: false, reason: `${target.name} requires guardian approval in ${mode} Mode` }
  }

  return isPolicyAllowed(policyAppId, mode)
}

export function launchApp(
  target: AppLaunchTarget,
  mode = 'Media',
  openWindow: (url: string) => Window | null = url => window.open(url, '_blank', 'noopener,noreferrer'),
): AppLaunchResult {
  const policy = checkPolicy(target, mode)
  if (!policy.allowed) {
    return {
      status: 'blocked_by_policy',
      targetId: target.id,
      message: policy.reason ?? 'Blocked by policy',
    }
  }

  switch (target.launchType) {
    case 'external_url': {
      if (!target.url) {
        return { status: 'missing_url', targetId: target.id, message: 'No URL configured for this app' }
      }
      const win = openWindow(target.url)
      if (win === null && typeof window !== 'undefined') {
        return {
          status: 'launched',
          targetId: target.id,
          message: `Opened ${target.name} in a new tab (popup may have been blocked — use the link below)`,
          openedUrl: target.url,
        }
      }
      return {
        status: 'launched',
        targetId: target.id,
        message: `Opened ${target.name} in a new browser tab`,
        openedUrl: target.url,
      }
    }
    case 'internal_route':
      if (!target.internalRoute) {
        return { status: 'missing_url', targetId: target.id, message: 'Internal route not configured' }
      }
      return {
        status: 'launched',
        targetId: target.id,
        message: `Navigating to ${target.name}`,
        openedUrl: target.internalRoute,
      }
    case 'local_app':
      if (!target.localAppId) {
        return { status: 'missing_url', targetId: target.id, message: 'Local app id not configured' }
      }
      return {
        status: 'launched',
        targetId: target.id,
        message: `Opening ${target.name} shell app`,
        openedUrl: `#local:${target.localAppId}`,
      }
    case 'unavailable':
      return {
        status: 'unsupported',
        targetId: target.id,
        message: `${target.name} is not available on this prototype build`,
      }
    default:
      return { status: 'unsupported', targetId: target.id, message: 'Unsupported launch type' }
  }
}

export function pwaTargetToLaunchTarget(pwa: {
  id: string
  name: string
  url: string
  launchType?: LaunchType
  policyAppId?: string
}): AppLaunchTarget {
  return {
    id: pwa.id,
    name: pwa.name,
    launchType: pwa.launchType ?? 'external_url',
    url: pwa.url,
    policyAppId: pwa.policyAppId,
  }
}
