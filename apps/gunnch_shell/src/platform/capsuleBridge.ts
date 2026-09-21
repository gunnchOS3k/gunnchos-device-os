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
  | 'games_list'
  | 'waike_launch'
  | 'gunnchai_launch'
  | 'app_center_list'
  | 'vault_list'
  | 'vault_op'
  | 'connect_action'
  | 'assist_settings'
  | 'exit_capsule'
  | 'shell_boot_stage'
  | 'shell_ready'
  | 'shell_fatal'

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
    typeof window !== 'undefined' && window.location ? window.location.origin : 'https://appassets.androidplatform.net'
  const request: BridgeRequest = { id, capability, origin, payload }
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

export function reportBootStage(stage: string): void {
  void capsuleInvoke('shell_boot_stage', { stage })
  try {
    console.log('GUNNCH_BOOT_STAGE', stage)
  } catch {
    // ignore
  }
}

export function reportShellReady(): void {
  void capsuleInvoke('shell_ready', { stage: 'GUNNCHOS_SHELL_READY' })
}

export function reportShellFatal(message: string): void {
  void capsuleInvoke('shell_fatal', { message })
}

export function isCapsuleBridgeAvailable(): boolean {
  return Boolean(
    typeof window !== 'undefined' &&
      (window.AndroidCapsuleBridge || window.CapsuleBridge || window.__GUNNCH_CAPSULE_BRIDGE__),
  )
}

export function installFatalHandlers(): void {
  if (typeof window === 'undefined') return
  const showEmergency = (msg: string) => {
    reportShellFatal(msg)
    const root = document.getElementById('root') || document.body
    if (!root) return
    root.innerHTML = ''
    const box = document.createElement('div')
    box.setAttribute('role', 'alert')
    box.style.cssText =
      'min-height:100vh;margin:0;padding:24px;background:#000;color:#fff;font:16px/1.4 system-ui,sans-serif;'
    box.innerHTML = `<h1 style="color:#ffeb3b;margin:0 0 12px">gunnchOS failed to start</h1><p>${msg}</p><p style="opacity:.8">Tap Android back or reopen Capsule. Retry from the native overlay if shown.</p>`
    root.appendChild(box)
  }
  window.addEventListener('error', (ev) => {
    showEmergency(`window.error: ${ev.message || 'unknown'}`)
  })
  window.addEventListener('unhandledrejection', (ev) => {
    const reason = (ev as PromiseRejectionEvent).reason
    showEmergency(`unhandledrejection: ${reason?.message || String(reason)}`)
  })
}
