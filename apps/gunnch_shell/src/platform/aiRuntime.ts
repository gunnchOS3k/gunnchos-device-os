/**
 * Truthful AI / Assist runtime labeling.
 * Nearby Mac / Edge is never "On-device".
 */

export type AiRuntimeKind =
  | 'nearby_mac'
  | 'local_deterministic'
  | 'remote'
  | 'unavailable'

export type AiRuntimeStatus = {
  kind: AiRuntimeKind
  label: string
  detail: string
  privacy: string
}

export function resolveAiRuntime(opts?: {
  offline?: boolean
  nearbyEdgeAvailable?: boolean
  remoteAvailable?: boolean
}): AiRuntimeStatus {
  if (opts?.nearbyEdgeAvailable) {
    return {
      kind: 'nearby_mac',
      label: 'Nearby Mac',
      detail: 'Requests may run on a nearby Edge / Mac host over the local network. This is not on-device AI.',
      privacy: 'Prompts leave this device for the nearby host you paired.',
    }
  }
  if (opts?.offline || opts?.remoteAvailable === false) {
    return {
      kind: 'local_deterministic',
      label: 'Local deterministic',
      detail: 'On-device rule/help responses only. No generative model is claimed.',
      privacy: 'Stays on this device.',
    }
  }
  if (opts?.remoteAvailable) {
    return {
      kind: 'remote',
      label: 'Remote',
      detail: 'Cloud or remote assistant endpoint when configured and reachable.',
      privacy: 'Prompts leave this device for the configured remote endpoint.',
    }
  }
  return {
    kind: 'unavailable',
    label: 'Unavailable',
    detail: 'No assistant runtime is configured or reachable right now.',
    privacy: 'Nothing is sent.',
  }
}

/** Deterministic local help — never pretends to be a frontier model. */
export function localDeterministicReply(prompt: string): string {
  const q = prompt.trim().toLowerCase()
  if (!q) return 'Ask a short question about gunnchOS spaces, Vault, WAIKE, or Connect.'
  if (q.includes('waike') || q.includes('learn')) {
    return 'Open WAIKE from More or App Library → Learning. Offline honesty is shown when the hub cannot sync.'
  }
  if (q.includes('vault') || q.includes('file')) {
    return 'Vault keeps files you recover locally. Use Care for backups — we do not invent documents.'
  }
  if (q.includes('game')) {
    return 'Games live under App Library → Games. Launch records Continuity so Home can offer Continue.'
  }
  if (q.includes('on-device') || q.includes('nearby')) {
    return 'Nearby Mac is an edge runtime, not on-device AI. Local deterministic help stays on this device.'
  }
  return 'I can point you to wired spaces only. Try Settings for Appearance and AI/Assist runtime labels, or Search to jump to a real destination.'
}
