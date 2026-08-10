# Phase XIV local AI micro tier
#
# `micro_model.bin` is a deterministic hashed local-tier artifact used for
# registry/hash/timeout/fallback digital proof. Optional llama.cpp + SmolLM2
# GGUF is enabled via GUNNCHOS_ENABLE_LLAMA_TIER=1 when present.
#
# Not an HTTP stub. Apps must call OS AI System API, never model paths.
# PHYSICAL_EXECUTION_FREEZE=ACTIVE; GUNNCHOS_FRONTIER_OS_PARITY remains false.
