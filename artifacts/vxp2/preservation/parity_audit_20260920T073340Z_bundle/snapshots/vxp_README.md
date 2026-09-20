# gunnchOS Visual Experience Program (VXP)

VXP-0 establishes the visual constitution, baseline inventory, and design system.
VXP-1 ships the **Living Workspace** production shell direction on the Android Capsule stack.

## VXP-2 override (universal device parity)

**Governing contract:** [`docs/product/GUNNCHOS_DEVICE_PARITY_CONTRACT.md`](../product/GUNNCHOS_DEVICE_PARITY_CONTRACT.md)

VXP-2 is **not** limited to Anime Aggressors branding, Android-only chrome, reduced mobile, or companion-app identity. Android Capsule is an Android-hosted expression of the **same gunnchOS**. Gates: `artifacts/vxp2/reports/GUNNCHOS_UNIVERSAL_PARITY_GATES.json`.

Prior notes that framed the next lane as “VXP-2 Anime Aggressors brand system only” are **superseded** for product identity; game visual audits remain valid as *game* art workstreams under the universal contract.

## Stacking

- Base branch for this work: `platform/android-gunnchos-capsule-v1` (PR #158)
- Work branch: `vxp/vxp-0-vxp-1-living-workspace`
- Do **not** merge this lane until Capsule PR #158 and visual gates agree.
- Do **not** set `GUNNCHOS_MERGE_AUTHORIZED` until universal parity owner checklist is answered.

## Flags

- `CANONICAL_LOGO_ASSET_PENDING=true` — capsule branding intake folder has README only; no canonical logo file yet.
- Pixel / human validation evidence is separate from digital fixture captures.

## Tree

See sibling docs in this folder. Experiments under `experiments/` are **EXPERIMENTAL — NOT PRODUCTION UI**.
Product parity docs live under `docs/product/`.
