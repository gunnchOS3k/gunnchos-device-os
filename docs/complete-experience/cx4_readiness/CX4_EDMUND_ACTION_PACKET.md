# CX4 Edmund Action Packet (preparation — not evidence)

Ordered to minimize context switches. Only non-automatable human/physical/external actions.

## 1) Human accessibility session
- **Steps:** Execute `HUMAN_A11Y_VALIDATION_PACKET.md` with planned participants; store evidence under `artifacts/complete_experience/cx4_0/human_a11y/`.
- **Estimate:** 6–8 hours total (plan).
- **Prerequisite:** `CX4_HUMAN_A11Y_PACKET_READY`
- **Evidence:** observation forms, issues, screenshots/logs
- **Unlocks:** human a11y PASS / J6 class upgrade (only after real sessions)

## 2) Physical printer session
- **Steps:** Connect named USB and/or LAN printer; run `PHYSICAL_PRINTER_VALIDATION_PACKET.md`; run cups collector.
- **Estimate:** 90–120 minutes.
- **Prerequisite:** real printer hardware
- **Evidence:** collector bundle + output photos/hashes
- **Unlocks:** `PHYSICAL_PRINTER_PENDING` clearance

## 3) Camera / mic / AV session
- **Steps:** Execute `CAMERA_MIC_AV_VALIDATION_PACKET.md` on physical devices; capture diagnostics.
- **Estimate:** ~2 hours.
- **Prerequisite:** physical camera/mic
- **Evidence:** AV diag + quality notes
- **Unlocks:** `PHYSICAL_CAMERA_MIC_AV_PENDING` clearance

## 4) Peripheral matrix session
- **Steps:** Run peripheral matrix with keyboard/mouse/touch/BT/dock/Ring as available.
- **Estimate:** 2–3 hours.
- **Prerequisite:** named peripherals
- **Evidence:** mutation/reconnect logs
- **Unlocks:** physical peripheral PASS

## 5) Device Quartet EVT → DVT → PVT
- **Steps:** Follow per-SKU EVT/DVT/PVT packets; do not fabricate hardware.
- **Estimate:** multi-day to multi-week (plan).
- **Prerequisite:** hardware availability
- **Evidence:** stage reports
- **Unlocks:** EVT/DVT/PVT pending clearance

## 6) External chat/meeting provider credentials
- **Steps:** Obtain provider account; run live validation against contracts.
- **Estimate:** ~2 hours once credentials exist.
- **Prerequisite:** provider access
- **Evidence:** live traces
- **Unlocks:** external provider integration evidence (may upgrade J4)

## 7) Institutional issuer engagement
- **Steps:** Follow `CX4_INSTITUTIONAL_ISSUER_ONBOARDING.md` with a real issuer org.
- **Estimate:** multi-day (plan).
- **Prerequisite:** willing issuer
- **Evidence:** trust exchange + verify + revocation
- **Unlocks:** external issuer evidence (`certification_claimed` stays false unless earned)

## 8) Legal / privacy / rights review
- **Steps:** Submit privacy + rights registers for counsel review.
- **Estimate:** calendar days (plan).
- **Prerequisite:** registers ready
- **Evidence:** signed review memo
- **Unlocks:** `legal_approval`

## 9) Certification lab engagement
- **Steps:** Engage labs per `CERTIFICATION_MATRIX.json` rows when hardware maturity allows.
- **Estimate:** multi-month (plan).
- **Prerequisite:** EVT+/DVT hardware
- **Evidence:** certificates/reports
- **Unlocks:** `certified` (never from matrix alone)

## 10) WAIKE release dependency (do not modify release)
- **Steps:** Wait for genuine WAIKE accepted-main earned evidence; then re-verify CX3 earned token.
- **Estimate:** blocked on release train.
- **Prerequisite:** WAIKE release owners
- **Evidence:** real earned completion artifacts
- **Unlocks:** `CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS`

This packet is preparation, not evidence. `CX4_OWNER_ACTION_PACKET_READY=true` does not complete any gate.
