import { GunnchSettings } from './settingsStore'

export interface AccessibilityAuditResult {
  keyboardNavigationDocumented: boolean
  focusIndicatorsEnabled: boolean
  largeTextEnabled: boolean
  highContrastEnabled: boolean
  reducedMotionEnabled: boolean
  certificationClaimed: false
}

export function auditAccessibilitySettings(settings: GunnchSettings): AccessibilityAuditResult {
  return {
    keyboardNavigationDocumented: true,
    focusIndicatorsEnabled: settings.highContrast || settings.largeText,
    largeTextEnabled: settings.largeText,
    highContrastEnabled: settings.highContrast,
    reducedMotionEnabled: settings.reducedMotion,
    certificationClaimed: false,
  }
}

export function applyAccessibilityClasses(settings: GunnchSettings): string {
  const classes: string[] = []
  if (settings.largeText) classes.push('gunnch-a11y-large-text')
  if (settings.highContrast) classes.push('gunnch-a11y-high-contrast')
  if (settings.reducedMotion) classes.push('gunnch-a11y-reduced-motion')
  return classes.join(' ')
}
