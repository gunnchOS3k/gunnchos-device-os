# Human Accessibility Validation Packet (CX2)

HUMAN_A11Y_PENDING=true / HUMAN_VALIDATION_PENDING=true

## Checklist (human operator)

1. Keyboard-only traverse Home → Vault → App Center → Connect → Assist → Care
2. Focus ring visible on every control; tab order matches nav model
3. Screen reader (Orca/VoiceOver) announces accessible names/roles
4. Zoom 200% without clipping critical controls
5. High contrast + reduced motion settings apply in rendered UI
6. No keyboard traps in modals (install progress, compose, restore)
7. Touch targets ≥44px on Handheld / Student profiles

Record PASS/FAIL per item with date, profile, AT version. Do not auto-PASS from CI.
