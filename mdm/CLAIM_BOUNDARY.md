# MDM Claim Boundary

## What this track is

Local policy schema, sample policies, and a Python prototype agent that applies a **static signed policy file**. **Not production MDM.**

## Allowed claims

| Claim | Allowed? |
|-------|----------|
| MDM policy schema defined | Yes |
| Sample policies for school/library/guardian modes | Yes |
| Local policy agent reads static JSON/YAML | Yes |
| Enrollment profile example (documentation) | Yes |

## Not allowed claims

| Claim | Required evidence (not present) |
|-------|----------------------------------|
| Production MDM | Remote enrollment server, device identity, certificate provisioning |
| Remote policy delivery | Live policy push, ACK, rollback from MDM server |
| Fleet inventory | Device heartbeat, compliance dashboard |
| Remote wipe / lock | Tested on reference hardware with audit log |

## Relationship to shell policy

`apps/launcher_mock/src/services/policyEnforcementService.ts` applies **UI-mode** rules in the browser shell.

`mdm/device_policy_agent.py` is the **OS-layer prototype** for loading a signed/static fleet policy file — not wired to a remote server in Phase 4D.

## Beta gate

`production_mdm` status must remain **prototype** until enrollment server evidence and remote policy delivery are implemented and validated.
