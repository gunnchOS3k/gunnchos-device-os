export interface LocalStorageSurface {
  /** Browser localStorage key — prototype only; not OS encrypted storage. */
  key: string
  purpose: string
  sentToServer: false
}

export const LOCAL_STORAGE_SURFACES: LocalStorageSurface[] = [
  { key: 'gunnchos-profile', purpose: 'Onboarding profile and mode flags', sentToServer: false },
  { key: 'gunnchos-settings-v1', purpose: 'Theme, accessibility, offline, AI privacy toggles', sentToServer: false },
  { key: 'gunnchos-workspace-v1', purpose: 'File manager folders and text file metadata/content', sentToServer: false },
  { key: 'gunnchos-notes-v1', purpose: 'Notes app content and pins', sentToServer: false },
  { key: 'gunnchos-local-media-recent', purpose: 'Recent local media metadata (no blobs)', sentToServer: false },
  { key: 'gunnchos-deployment-mode', purpose: 'Policy test deployment mode override', sentToServer: false },
]

export interface PrivacyStatusSummary {
  prototypeOnly: true
  legalCertificationClaimed: false
  aiAssistantBackend: 'ui_shell_only'
  localOnly: true
  surfaces: LocalStorageSurface[]
}

export function getPrivacyStatus(): PrivacyStatusSummary {
  return {
    prototypeOnly: true,
    legalCertificationClaimed: false,
    aiAssistantBackend: 'ui_shell_only',
    localOnly: true,
    surfaces: LOCAL_STORAGE_SURFACES,
  }
}
