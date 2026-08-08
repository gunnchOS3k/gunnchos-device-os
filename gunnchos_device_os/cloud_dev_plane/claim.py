"""Claim boundary for the runnable cloud/fleet DEV plane."""

CLAIM_BOUNDARY = (
    "Runnable LOCAL DEV plane only (compose/containers or in-process HTTP). "
    "Not a production multi-tenant cloud, not campus MDM, not carrier-certified. "
    "Modes LOCAL/DISCONNECTED/CAMPUS_EDGE/CLOUD are software adapters with "
    "DEV tokens and privacy redaction — no production secrets."
)

REALM = "DEV"
