import contract from '../generated/launcherContract.json'

export interface MediaAppMeta {
  id: string
  name: string
  category: string
  route_url: string
  launch_type: string
  requires_network: boolean
  requires_drm: boolean
  requires_hdcp_for_external_display: boolean
  offline_supported: boolean
  guardian_controlled: boolean
  school_mode_default: string
  claim_status: string
  notes: string
}

export interface ModePolicy {
  allowed_apps: string[]
  blocked_apps: string[]
  media_mode?: boolean
  streaming_priority?: boolean
  library_login_warning?: boolean
  no_saved_passwords_default?: boolean
}

export interface LauncherContract {
  version: string
  generated_at: string
  claim_boundary: {
    drm_circumvention_supported: boolean
    service_certification_claimed: boolean
    drm_disclaimer: string
  }
  apps: Record<string, Record<string, unknown>>
  categories: string[]
  media_apps: Record<string, MediaAppMeta>
  media_app_ids: string[]
  modes: Record<string, ModePolicy>
  policy_samples: Record<string, boolean>
}

const data = contract as LauncherContract

export function useLauncherContract(): LauncherContract {
  return data
}

export function getMediaApps(): MediaAppMeta[] {
  return data.media_app_ids.map(id => data.media_apps[id]).filter(Boolean)
}

export function getModePolicy(mode: string): ModePolicy | undefined {
  return data.modes[mode]
}

export function isAppAllowedInMode(appId: string, mode: string): boolean {
  const pol = data.modes[mode]
  if (!pol) return false
  if (pol.blocked_apps.includes(appId)) return false
  return pol.allowed_apps.includes(appId)
}
