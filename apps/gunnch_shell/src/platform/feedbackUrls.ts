/** Canonical ecosystem feedback hub — accepted-main URL (live after portal #39). Never bake feature-branch URLs. */
export const FEEDBACK_HUB_URL =
  'https://github.com/gunnchOS3k/gunnchos-research-portal/blob/main/FEEDBACK.md'

export const SECURITY_MD_URL =
  'https://github.com/gunnchOS3k/gunnchos-research-portal/blob/main/SECURITY.md'

/** Public-only marker. Never append serial, IP, account, token, or local paths. */
export function feedbackUrlForComponent(component: string): string {
  const safe = component.replace(/[^\w\s.\-]/g, '').trim().slice(0, 64)
  if (!safe) return FEEDBACK_HUB_URL
  return `${FEEDBACK_HUB_URL}?component=${encodeURIComponent(safe)}`
}
