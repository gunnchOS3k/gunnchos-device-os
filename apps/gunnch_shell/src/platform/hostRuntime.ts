/**
 * Host runtime adapter for production gunnch_shell.
 * Experience parity only — not kernel/hardware identity.
 */

export type HostKind = 'GUNNCHOS_LINUX' | 'ANDROID_CAPSULE' | 'WEB_TEST'

export type HostCapabilities = {
  files: boolean
  share: boolean
  clipboard: boolean
  camera: boolean
  microphone: boolean
  notifications: boolean
  network: boolean
  battery: boolean
  thermal: boolean
  bluetooth: boolean
  usb_metadata: boolean
  display: boolean
  haptics: boolean
  permissions: boolean
  open_url: boolean
  open_android_app: boolean
  file_picker: boolean
  document_create: boolean
  document_open: boolean
  downloads: boolean
  linux_guest: boolean
}

export type HostRuntime = {
  host: HostKind
  profile: 'student_14_5' | 'handheld_hybrid' | 'ds_xl' | 'docked' | 'ci_qemu' | 'android_capsule'
  fullscreenOsExperience: boolean
  bridgeAvailable: boolean
  capabilities: HostCapabilities
}

declare global {
  interface Window {
    __GUNNCH_HOST__?: HostKind
    __GUNNCH_CAPSULE_BRIDGE__?: boolean
    CapsuleBridge?: {
      post: (capability: string, payload?: Record<string, unknown>) => Promise<unknown>
    }
    AndroidCapsuleBridge?: {
      invoke: (requestJson: string) => string
    }
  }
}

const DEFAULT_CAPS: HostCapabilities = {
  files: false,
  share: false,
  clipboard: true,
  camera: false,
  microphone: false,
  notifications: false,
  network: true,
  battery: false,
  thermal: false,
  bluetooth: false,
  usb_metadata: false,
  display: true,
  haptics: false,
  permissions: false,
  open_url: true,
  open_android_app: false,
  file_picker: false,
  document_create: false,
  document_open: false,
  downloads: false,
  linux_guest: false,
}

export function detectHost(): HostKind {
  if (typeof window !== 'undefined' && window.__GUNNCH_HOST__) {
    return window.__GUNNCH_HOST__
  }
  if (typeof window !== 'undefined' && window.AndroidCapsuleBridge) {
    return 'ANDROID_CAPSULE'
  }
  if (typeof navigator !== 'undefined' && /Android/i.test(navigator.userAgent)) {
    return 'ANDROID_CAPSULE'
  }
  // Linux guest / gunnchOS lab often reports Linux without Android WebView markers
  if (typeof navigator !== 'undefined' && /Linux/i.test(navigator.userAgent) && !/Android/i.test(navigator.userAgent)) {
    return 'GUNNCHOS_LINUX'
  }
  return 'WEB_TEST'
}

export function resolveHostRuntime(): HostRuntime {
  const host = detectHost()
  if (host === 'ANDROID_CAPSULE') {
    return {
      host,
      profile: 'android_capsule',
      fullscreenOsExperience: true,
      bridgeAvailable: Boolean(window.AndroidCapsuleBridge || window.__GUNNCH_CAPSULE_BRIDGE__),
      capabilities: {
        ...DEFAULT_CAPS,
        files: true,
        share: true,
        clipboard: true,
        camera: true,
        microphone: true,
        notifications: true,
        battery: true,
        thermal: true,
        bluetooth: true,
        usb_metadata: true,
        haptics: true,
        permissions: true,
        open_android_app: true,
        file_picker: true,
        document_create: true,
        document_open: true,
        downloads: true,
        linux_guest: true,
      },
    }
  }
  if (host === 'GUNNCHOS_LINUX') {
    return {
      host,
      profile: 'student_14_5',
      fullscreenOsExperience: true,
      bridgeAvailable: false,
      capabilities: {
        ...DEFAULT_CAPS,
        files: true,
        file_picker: true,
        document_create: true,
        document_open: true,
        downloads: true,
        linux_guest: true,
      },
    }
  }
  return {
    host: 'WEB_TEST',
    profile: 'ci_qemu',
    fullscreenOsExperience: false,
    bridgeAvailable: false,
    capabilities: { ...DEFAULT_CAPS },
  }
}
