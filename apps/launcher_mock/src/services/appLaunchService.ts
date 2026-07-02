import { evaluateAppPolicy, resolvePolicyAppId } from './policyEnforcementService'

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
  schoolModeDefault?: string
  requiresNetwork?: boolean
  offlineSupported?: boolean
}

export interface AppLaunchResult {
  status: LaunchResultStatus
  targetId: string
  message: string
  openedUrl?: string
  warning?: string
}

export function launchApp(
  target: AppLaunchTarget,
  mode = 'Media',
  openWindow: (url: string) => Window | null = url => window.open(url, '_blank', 'noopener,noreferrer'),
): AppLaunchResult {
  const policy = evaluateAppPolicy(target.id, mode, {
    schoolModeDefault: target.schoolModeDefault,
    requiresNetwork: target.requiresNetwork,
    offlineSupported: target.offlineSupported,
    isNativeShellApp: target.launchType === 'local_app',
  })

  if (!policy.canLaunch) {
    return {
      status: 'blocked_by_policy',
      targetId: target.id,
      message: policy.message,
    }
  }

  const warning = policy.decision === 'warning_only' ? policy.message : undefined

  switch (target.launchType) {
    case 'external_url': {
      if (!target.url) {
        return { status: 'missing_url', targetId: target.id, message: 'No URL configured for this app' }
      }
      openWindow(target.url)
      return {
        status: 'launched',
        targetId: target.id,
        message: `Opened ${target.name} in a new browser tab`,
        openedUrl: target.url,
        warning,
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
        warning,
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
        warning,
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
    policyAppId: pwa.policyAppId ?? resolvePolicyAppId(pwa.id),
  }
}
