# CX2B — Real Provider Integrations

Live qualification snapshot (fail closed; no marker PASS).

See `CX2_PROVIDER_QUALIFICATION_LIVE.json` for evidence classes earned on this host.

## Boundaries

- Flatpak: EXTERNAL when absent (macOS CI hosts)
- Browser GUI download/chooser: HUMAN_VALIDATION_PENDING without automation proof
- CUPS queue: EXTERNAL when absent; PHYSICAL always pending
- xdg-desktop-portal: NOT_APPLICABLE outside Linux session bus
- Chat/video: EXTERNAL_PROVIDER_PENDING; HUMAN_AV + PHYSICAL camera/mic pending
