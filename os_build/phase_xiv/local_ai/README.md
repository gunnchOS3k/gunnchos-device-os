# Phase XIV local AI tiers

`micro_model.bin` is a deterministic hashed local-tier artifact used for
registry/hash/timeout/fallback digital proof.

Optional llama.cpp GGUFs are enabled via `GUNNCHOS_ENABLE_LLAMA_TIER=1`
(or `include_llama=True`) when present. Labels match gunnchAI3k:

| Label | Role | What is real today |
| --- | --- | --- |
| **Nano/fallback** | `NANO_LOCAL` | SmolLM2-135M-Instruct Q4_K_M **512-ctx** when the GGUF is on disk. Not daily intelligence. |
| **Local Fast** | `LOCAL_FAST` | 360M-class GGUF. **OPEN** until weights are present. |
| **Local Pro** | `LOCAL_PRO` | 1.5B-class GGUF. **OPEN** until weights are present. |
| **micro** | `MICRO` | Always-on deterministic hashed blob. |

Claiming SmolLM2 as Local Fast or Local Pro **fails closed** (registry reject).

`GUNNCHAI_APP_PRODUCT_COMPLETE` stays false. `HUMAN_E6` stays false.

Not an HTTP stub. Apps must call OS AI System API, never model paths.
PHYSICAL_EXECUTION_FREEZE=ACTIVE; GUNNCHOS_FRONTIER_OS_PARITY remains false.
