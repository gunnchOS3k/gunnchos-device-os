# Design system (VXP-0 / VXP-1)

Living Workspace tokens, geometric icons, and primitives for `gunnch_shell`.

## Layout

- `tokens.css` / `tokens.ts` — color, type, space, motion
- `icons/` — SVG path family (no emoji product icons)
- `primitives/` — ActionButton, EmptyState, SurfaceHeader
- `layout/` — reserved for shell chrome helpers

## Rules

- No network fonts required for shell
- Preserve surface IDs and `data-action` semantics
- High contrast / reduce motion / UI scale remain Assist authority
- `CANONICAL_LOGO_ASSET_PENDING=true` until branding intake lands (see capsule `branding/README.md`)
