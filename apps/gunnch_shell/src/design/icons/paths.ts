import type { VxpIconName } from '../tokens'

/** Geometric SVG path set — product icons, never emoji. */
const PATHS: Record<VxpIconName, string> = {
  home: 'M4 11.5 12 4l8 7.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-8.5z',
  vault:
    'M5 7h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2zm3 4h8v2H8v-2zm0 4h5v2H8v-2z',
  app_center:
    'M5 5h6v6H5V5zm8 0h6v6h-6V5zM5 13h6v6H5v-6zm8 0h6v6h-6v-6z',
  connect:
    'M8 12a4 4 0 0 1 4-4h2v2h-2a2 2 0 1 0 0 4h2v2h-2a4 4 0 0 1-4-4zm4-2h2a4 4 0 1 1 0 8h-2v-2h2a2 2 0 1 0 0-4h-2V10z',
  more: 'M6 12a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm6 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm6 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z',
  assist:
    'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zm0 4a1.25 1.25 0 1 1 0 2.5A1.25 1.25 0 0 1 12 7zm-1.5 4.5h3V17h-3v-5.5z',
  care: 'M12 21s-7-4.4-7-10a4 4 0 0 1 7-2.5A4 4 0 0 1 19 11c0 5.6-7 10-7 10z',
  wallet:
    'M4 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v2H4V7zm0 4h16v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-6zm11 2.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3z',
  portfolio:
    'M8 6V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v1h3a1 1 0 0 1 1 1v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a1 1 0 0 1 1-1h3zm2 0h4V5h-4v1z',
  career:
    'M12 3 4 7v2h16V7L12 3zm-6 8v7h4v-4h4v4h4v-7H6z',
  verifier:
    'M12 2 4 5v6c0 5 3.4 8.4 8 10 4.6-1.6 8-5 8-10V5l-8-3zm-1 13-3.5-3.5 1.4-1.4L11 12.2l4.1-4.1 1.4 1.4L11 15z',
  back: 'M14 6 8 12l6 6 1.4-1.4L10.8 12l4.6-4.6L14 6z',
  exit: 'M10 4h8v16h-8v-2h6V6h-6V4zM4 12l4-4v3h6v2H8v3l-4-4z',
  search:
    'M10.5 4a6.5 6.5 0 1 1 0 13 6.5 6.5 0 0 1 0-13zm0 2a4.5 4.5 0 1 0 0 9 4.5 4.5 0 0 0 0-9zm6.2 9.3 3.5 3.5-1.4 1.4-3.5-3.5 1.4-1.4z',
  refresh:
    'M12 5a7 7 0 0 1 6.3 4H16v2h5.5V5.5H19V7a9 9 0 1 0 1.7 6.2l-1.9-.6A7 7 0 1 1 12 5z',
  backup:
    'M12 3 6 8h3v6h6V8h3L12 3zm-6 14h12v2H6v-2z',
  trash:
    'M9 4h6l1 2h4v2H4V6h4l1-2zm1 6h2v8h-2v-8zm4 0h2v8h-2v-8zM7 10h2v8H7v-8z',
  install: 'M11 3h2v10h3l-4 5-4-5h3V3zm-6 15h14v2H5v-2z',
  open: 'M14 4h6v6h-2V7.4l-7.3 7.3-1.4-1.4L16.6 6H14V4zM4 6h8v2H6v10h10v-6h2v8H4V6z',
  update:
    'M12 4v8l4 2-1 1.7-5-2.5V4h2zm7 8a7 7 0 0 1-11.9 5H9v-2H4.5v4.5H6.5V18a9 9 0 1 0 2.1-15.7L7.7 4.1A7 7 0 0 1 19 12z',
  offline:
    'M3.3 4.7 4.7 3.3 20.7 19.3l-1.4 1.4-2.2-2.2A9 9 0 0 1 5.1 8.9L3.3 4.7zM12 4a8 8 0 0 1 7.5 5.2l-1.9.7A6 6 0 0 0 8.4 6.4L6.9 4.9A7.9 7.9 0 0 1 12 4z',
  error:
    'M12 3 2 21h20L12 3zm0 5.5 5.5 10.5h-11L12 8.5zM11 13h2v3h-2v-3zm0 4h2v2h-2v-2z',
  empty:
    'M4 6h16v12H4V6zm2 2v8h12V8H6zm3 2h6v2H9v-2z',
  status_ok: 'M12 3a9 9 0 1 1 0 18 9 9 0 0 1 0-18zm-1.2 10.4 4.7-4.7 1.4 1.4-6.1 6.1-3.3-3.3 1.4-1.4 1.9 1.9z',
  status_warn:
    'M12 3 2 21h20L12 3zm0 5 5.2 10H6.8L12 8zm-1 4h2v3h-2v-3zm0 4h2v2h-2v-2z',
  chevron: 'M9 6l6 6-6 6-1.4-1.4L12.2 12 7.6 7.4 9 6z',
  file: 'M7 3h7l5 5v13H7V3zm7 1.5V9h4.5L14 4.5z',
  app_glyph:
    'M6 6h5v5H6V6zm7 0h5v5h-5V6zM6 13h5v5H6v-5zm7 2.5 2.5-2.5 2.5 2.5-2.5 2.5-2.5-2.5z',
}

export function iconPath(name: VxpIconName): string {
  return PATHS[name]
}

export { PATHS as ICON_PATHS }
