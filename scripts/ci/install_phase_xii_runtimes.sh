#!/usr/bin/env bash
# Install Godot + llama-server + pinned SmolLM2 GGUF for Phase XII Wave 0 CI.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CACHE="${PHASE_XII_RUNTIME_CACHE:-$ROOT/.cache/phase_xii_runtimes}"
BIN="$CACHE/bin"
MODELS="$ROOT/artifacts/phase_xii/models"
mkdir -p "$BIN" "$MODELS" "$CACHE"

GODOT_VER="${GODOT_CI_VERSION:-4.4.1-stable}"
GODOT_ZIP="Godot_v${GODOT_VER}_linux.x86_64.zip"
GODOT_URL="https://github.com/godotengine/godot/releases/download/${GODOT_VER}/${GODOT_ZIP}"

LLAMA_TAG="${LLAMA_CI_TAG:-b10333}"
LLAMA_TGZ="llama-${LLAMA_TAG}-bin-ubuntu-x64.tar.gz"
LLAMA_URL="https://github.com/ggml-org/llama.cpp/releases/download/${LLAMA_TAG}/${LLAMA_TGZ}"

GGUF_NAME="SmolLM2-135M-Instruct-Q4_K_M.gguf"
GGUF_URL="${GUNNCHAI_GGUF_URL:-https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF/resolve/main/${GGUF_NAME}}"

export PATH="$BIN:$PATH"

curl_retry() {
  # GitHub release CDN occasionally returns 503; fail closed after retries.
  local out="$1"
  shift
  local attempt=1
  local max=6
  local delay=3
  while true; do
    if curl -fsSL --retry 3 --retry-all-errors --retry-delay 2 -o "$out" "$@"; then
      return 0
    fi
    if (( attempt >= max )); then
      echo "curl_retry exhausted after ${max} attempts: $*" >&2
      return 1
    fi
    echo "curl_retry attempt ${attempt}/${max} failed; sleeping ${delay}s..." >&2
    sleep "$delay"
    attempt=$((attempt + 1))
    delay=$((delay * 2))
  done
}

if ! command -v godot >/dev/null 2>&1 && [[ ! -x "$BIN/godot" ]]; then
  echo "Downloading Godot ${GODOT_VER}..."
  curl_retry "$CACHE/$GODOT_ZIP" "$GODOT_URL"
  unzip -o "$CACHE/$GODOT_ZIP" -d "$CACHE/godot_extract" >/dev/null
  GODOT_BIN="$(find "$CACHE/godot_extract" -type f -name 'Godot*' ! -name '*.txt' | head -n1)"
  install -m 755 "$GODOT_BIN" "$BIN/godot"
fi

if ! command -v llama-server >/dev/null 2>&1 && [[ ! -x "$BIN/llama-server" ]]; then
  echo "Downloading llama.cpp ${LLAMA_TAG}..."
  curl_retry "$CACHE/$LLAMA_TGZ" "$LLAMA_URL"
  mkdir -p "$CACHE/llama_extract"
  tar -xzf "$CACHE/$LLAMA_TGZ" -C "$CACHE/llama_extract"
  LLAMA_BIN="$(find "$CACHE/llama_extract" -type f -name 'llama-server' | head -n1)"
  if [[ -z "$LLAMA_BIN" ]]; then
    echo "llama-server binary missing from $LLAMA_TGZ" >&2
    exit 1
  fi
  install -m 755 "$LLAMA_BIN" "$BIN/llama-server"
  # companion shared libs must be loadable (ubuntu tarball ships libllama*.so)
  find "$CACHE/llama_extract" -type f \( -name '*.so' -o -name '*.so.*' \) -exec cp -f {} "$BIN/" \; || true
  # also keep original layout dir on library path
  LLAMA_LIB_DIR="$(dirname "$LLAMA_BIN")"
  echo "$LLAMA_LIB_DIR" > "$CACHE/llama_lib_dir.txt"
fi

# Ensure llama shared libs are present even on cache hits
if [[ -x "$BIN/llama-server" ]]; then
  if ! LD_LIBRARY_PATH="$BIN${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" "$BIN/llama-server" --version >/dev/null 2>&1; then
    echo "Cached llama-server missing libs; re-fetching ${LLAMA_TAG}..."
    curl_retry "$CACHE/$LLAMA_TGZ" "$LLAMA_URL"
    rm -rf "$CACHE/llama_extract"
    mkdir -p "$CACHE/llama_extract"
    tar -xzf "$CACHE/$LLAMA_TGZ" -C "$CACHE/llama_extract"
    LLAMA_BIN="$(find "$CACHE/llama_extract" -type f -name 'llama-server' | head -n1)"
    install -m 755 "$LLAMA_BIN" "$BIN/llama-server"
    find "$CACHE/llama_extract" -type f \( -name '*.so' -o -name '*.so.*' \) -exec cp -f {} "$BIN/" \; || true
    dirname "$LLAMA_BIN" > "$CACHE/llama_lib_dir.txt"
  fi
fi

if [[ ! -f "$MODELS/$GGUF_NAME" ]]; then
  echo "Downloading $GGUF_NAME..."
  curl_retry "$MODELS/$GGUF_NAME" -L "$GGUF_URL"
fi

# Prefer cache bins on PATH for subsequent steps (GitHub Actions)
if [[ -n "${GITHUB_PATH:-}" ]]; then
  echo "$BIN" >> "$GITHUB_PATH"
fi
if [[ -n "${GITHUB_ENV:-}" ]]; then
  echo "GUNNCHAI_MODEL_PATH=$MODELS/$GGUF_NAME" >> "$GITHUB_ENV"
  echo "LLAMA_MODEL=$MODELS/$GGUF_NAME" >> "$GITHUB_ENV"
fi
export PATH="$BIN:$PATH"
export LD_LIBRARY_PATH="$BIN${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
if [[ -f "$CACHE/llama_lib_dir.txt" ]]; then
  libdir="$(cat "$CACHE/llama_lib_dir.txt")"
  export LD_LIBRARY_PATH="$libdir:$LD_LIBRARY_PATH"
fi
export GUNNCHAI_MODEL_PATH="$MODELS/$GGUF_NAME"
export LLAMA_MODEL="$MODELS/$GGUF_NAME"
if [[ -n "${GITHUB_ENV:-}" ]]; then
  echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH" >> "$GITHUB_ENV"
fi

godot --version || "$BIN/godot" --version
if ! LD_LIBRARY_PATH="$LD_LIBRARY_PATH" "$BIN/llama-server" --version >/tmp/llama_ver.txt 2>&1; then
  echo "llama-server failed to start:" >&2
  cat /tmp/llama_ver.txt >&2 || true
  ldd "$BIN/llama-server" >&2 || true
  exit 1
fi
cat /tmp/llama_ver.txt
ls -lh "$MODELS/$GGUF_NAME"
echo "Phase XII runtimes ready"
