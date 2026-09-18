/**
 * Typed allowlisted bridge client for ANDROID_CAPSULE host.
 * No arbitrary JS→Kotlin — only named capabilities with schema validation on host.
 */

export type CapsuleCapability =
  | 'files'
  | 'share'
  | 'clipboard'
  | 'camera'
  | 'microphone'
  | 'notifications'
  | 'network'
  | 'battery'
  | 'thermal'
  | 'bluetooth'
  | 'usb_metadata'
  | 'display'
  | 'haptics'
  | 'permissions'
  | 'open_url'
  | 'open_android_app'
  | 'file_picker'
  | 'document_create'
  | 'document_open'
  | 'downloads'
  | 'session_get'
  | 'session_put'
  | 'care_snapshot'
  | 'linux_guest_status'
  | 'games_launch'
  | 'waike_launch'
  | 'gunnchai_launch'
  | 'app_center_list'
  | 'vault_list'
  | 'vault_op'
  | 'connect_action'
  | 'assist_settings'
  | 'exit_capsule'

export type BridgeRequest = {
  id: string
  capability: CapsuleCapability
  origin: string
  payload?: Record<string, unknown>
}

export type BridgeResponse = {
  id: string
  ok: boolean
  result?: unknown
  error?: string
  consent_required?: boolean
}

function nativeInvoke(request: BridgeRequest): BridgeResponse {
  const bridge = typeof window !== 'undefined' ? window.AndroidCapsuleBridge : undefined
  if (!bridge?.invoke) {
    return { id: request.id, ok: false, error: 'bridge_unavailable' }
  }
  try {
    const raw = bridge.invoke(JSON.stringify(request))
    return JSON.parse(raw) as BridgeResponse
  } catch (err: any) {
    return { id: request.id, ok: false, error: err?.message || 'bridge_invoke_failed' }
  }
}

let seq = 0

export async function capsuleInvoke(
  capability: CapsuleCapability,
  payload?: Record<string, unknown>,
): Promise<BridgeResponse> {
  const id = `cap-${Date.now()}-${++seq}`
  const origin =
    typeof window !== 'undefined' && window.location ? window.location.origin : 'file://capsule'
  const request: BridgeRequest = { id, capability, origin, payload }
  // Prefer async postMessage path if injected; fall back to sync WebView interface
  if (typeof window !== 'undefined' && window.CapsuleBridge?.post) {
    try {
      const result = await window.CapsuleBridge.post(capability, payload)
      return { id, ok: true, result }
    } catch (err: any) {
      return { id, ok: false, error: err?.message || 'bridge_post_failed' }
    }
  }
  return nativeInvoke(request)
}

export function isCapsuleBridgeAvailable(): boolean {
  return Boolean(
    typeof window !== 'undefined' &&
      (window.AndroidCapsuleBridge || window.CapsuleBridge || window.__GUNNCH_CAPSULE_BRIDGE__),
  )
}
