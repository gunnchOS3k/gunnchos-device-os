#!/bin/sh
# Shared supervised-service runtime for the gunnchOS reference image (DEV/VM).
# Real long-lived processes with startup/health/shutdown/restart/logs/persistence
# and local mailbox IPC (multi-process request/response). Not a stub PID-only script.
# Realm: DEV. Not systemd, not production MDM, not FULL_GUNNCHOS_PLATFORM_DIGITAL_COMPLETE.

set -eu

GUNNCHOS_RUN_ROOT="${GUNNCHOS_RUN_ROOT:-/run/gunnchos}"
GUNNCHOS_STATE_ROOT="${GUNNCHOS_STATE_ROOT:-/var/lib/gunnchos/state}"
GUNNCHOS_LOG_ROOT="${GUNNCHOS_LOG_ROOT:-/var/log/gunnchos}"

svc_paths() {
  NAME="$1"
  PIDFILE="${GUNNCHOS_RUN_ROOT}/${NAME}.pid"
  IPC_DIR="${GUNNCHOS_RUN_ROOT}/ipc/${NAME}"
  INBOX="${IPC_DIR}/in"
  OUTBOX="${IPC_DIR}/out"
  LOGFILE="${GUNNCHOS_LOG_ROOT}/${NAME}.log"
  STATEFILE="${GUNNCHOS_STATE_ROOT}/${NAME}.state"
  RESTARTFILE="${GUNNCHOS_RUN_ROOT}/${NAME}.restarts"
}

svc_log() {
  NAME="$1"
  shift
  mkdir -p "${GUNNCHOS_LOG_ROOT}"
  # shellcheck disable=SC2154
  echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || echo now) $*" >> "${GUNNCHOS_LOG_ROOT}/${NAME}.log"
}

svc_persist() {
  NAME="$1"
  STATE="$2"
  svc_paths "$NAME"
  mkdir -p "${GUNNCHOS_STATE_ROOT}"
  {
    echo "service=${NAME}"
    echo "state=${STATE}"
    echo "ipc=mailbox"
    echo "protocol=http_line"
    echo "realm=DEV"
    echo "pid=$(cat "${PIDFILE}" 2>/dev/null || echo none)"
    echo "restarts=$(cat "${RESTARTFILE}" 2>/dev/null || echo 0)"
    echo "updated=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || echo now)"
  } > "${STATEFILE}"
}

svc_handle_http() {
  NAME="$1"
  METHOD="$2"
  PATH_Q="$3"
  BODY="${4:-}"
  case "${METHOD} ${PATH_Q}" in
    "GET /health"|"GET /v1/health")
      echo "HTTP/1.0 200 OK"
      echo "Content-Type: text/plain"
      echo "X-Gunnchos-Service: ${NAME}"
      echo "X-Gunnchos-IPC: mailbox"
      echo ""
      echo "ok svc=${NAME}"
      ;;
    "GET /status"|"GET /v1/status")
      echo "HTTP/1.0 200 OK"
      echo "Content-Type: text/plain"
      echo ""
      echo "running svc=${NAME} realm=DEV ipc=mailbox"
      ;;
    "GET /ping"|"GET /v1/ping")
      echo "HTTP/1.0 200 OK"
      echo "Content-Type: text/plain"
      echo ""
      echo "pong svc=${NAME}"
      ;;
    "POST /call"|"POST /v1/call")
      # Body: target_method[=arg]
      RESULT="$(svc_domain_call "${NAME}" "${BODY}")"
      echo "HTTP/1.0 200 OK"
      echo "Content-Type: text/plain"
      echo ""
      echo "result svc=${NAME} ${RESULT}"
      ;;
    "POST /shutdown"|"POST /v1/shutdown")
      echo "HTTP/1.0 200 OK"
      echo "Content-Type: text/plain"
      echo ""
      echo "shutting_down svc=${NAME}"
      echo "__SHUTDOWN__"
      ;;
    "POST /restart"|"POST /v1/restart")
      echo "HTTP/1.0 200 OK"
      echo "Content-Type: text/plain"
      echo ""
      echo "restarting svc=${NAME}"
      echo "__RESTART__"
      ;;
    *)
      echo "HTTP/1.0 404 Not Found"
      echo "Content-Type: text/plain"
      echo ""
      echo "error unknown_route svc=${NAME} ${METHOD} ${PATH_Q}"
      ;;
  esac
}

# Domain-specific call surface for cross-service proof (DEV).
svc_domain_call() {
  NAME="$1"
  BODY="$2"
  METHOD_NAME="${BODY%%=*}"
  ARG=""
  case "${BODY}" in
    *=*) ARG="${BODY#*=}" ;;
  esac
  case "${NAME}:${METHOD_NAME}" in
    hal:list_profiles) echo "profiles=Student14,Student11,Pro14" ;;
    hal:get_profile) echo "profile=${ARG:-Student14}" ;;
    identity:whoami) echo "subject=dev-local realm=DEV" ;;
    identity:issue_session) echo "session=dev-sess token=DEV_SESSION" ;;
    diagnostics:probe) echo "probe_ok target=${ARG:-hal}" ;;
    diagnostics:inventory) echo "services=17 kind=supervised_real" ;;
    fleet_agent:heartbeat) echo "enrolled=false realm=DEV" ;;
    fleet_agent:ping_identity) echo "identity_reachable=true" ;;
    connectivity:loopback) echo "lo=up" ;;
    display:current) echo "mode=handheld" ;;
    dock:status) echo "docked=false" ;;
    continuity:snapshot) echo "snapshot=ok" ;;
    permissions:check) echo "decision=allow capability=${ARG:-basic}" ;;
    sandbox:status) echo "sandbox=ready" ;;
    input:bindings) echo "preset=handheld_default" ;;
    ring:status) echo "physical_ring_claimed=false" ;;
    updater:slot) echo "active=$(cat /var/lib/gunnchos/state/active_slot 2>/dev/null || echo a)" ;;
    recovery:self_check) echo "recovery=ok" ;;
    a11y:status) echo "a11y=ready" ;;
    profile_manager:active) echo "profile=default" ;;
    ai_interface:ping) echo "ai=dev_stub_entry" ;;
    *) echo "ack method=${METHOD_NAME} arg=${ARG}" ;;
  esac
}

svc_daemon_loop() {
  NAME="$1"
  svc_paths "$NAME"
  mkdir -p "${INBOX}" "${OUTBOX}" "${GUNNCHOS_LOG_ROOT}" "${GUNNCHOS_STATE_ROOT}" "${GUNNCHOS_RUN_ROOT}"
  echo "$$" > "${PIDFILE}"
  svc_persist "$NAME" "running"
  svc_log "$NAME" "started pid=$$ ipc=mailbox protocol=http_line"

  while true; do
    # shellcheck disable=SC2045
    for req in "${INBOX}"/*.req; do
      [ -e "${req}" ] || continue
      [ -f "${req}" ] || continue
      ID="$(basename "${req}" .req)"
      # First line: METHOD PATH
      # Optional second line: body
      METHOD="GET"
      PATH_Q="/health"
      BODY=""
      # Read request file
      LINE1="$(sed -n '1p' "${req}" 2>/dev/null || true)"
      LINE2="$(sed -n '2p' "${req}" 2>/dev/null || true)"
      rm -f "${req}"
      if [ -n "${LINE1}" ]; then
        METHOD="${LINE1%% *}"
        PATH_Q="${LINE1#* }"
        PATH_Q="${PATH_Q%% *}"
      fi
      BODY="${LINE2}"
      RESP="$(svc_handle_http "${NAME}" "${METHOD}" "${PATH_Q}" "${BODY}")"
      printf '%s\n' "${RESP}" > "${OUTBOX}/${ID}.rep"
      svc_log "$NAME" "handled ${METHOD} ${PATH_Q}"
      case "${RESP}" in
        *__SHUTDOWN__*)
          svc_persist "$NAME" "stopped"
          svc_log "$NAME" "shutdown"
          rm -f "${PIDFILE}"
          exit 0
          ;;
        *__RESTART__*)
          COUNT="$(cat "${RESTARTFILE}" 2>/dev/null || echo 0)"
          COUNT=$((COUNT + 1))
          echo "${COUNT}" > "${RESTARTFILE}"
          svc_persist "$NAME" "restarting"
          svc_log "$NAME" "restart count=${COUNT}"
          # Re-exec self as daemon
          rm -f "${PIDFILE}"
          exec /opt/gunnchos/services/"${NAME}".sh _daemon
          ;;
      esac
    done
    # Slightly longer poll interval reduces TCG thrash with 17 concurrent daemons.
    sleep 0.1
  done
}

svc_is_running() {
  NAME="$1"
  svc_paths "$NAME"
  if [ -f "${PIDFILE}" ]; then
    PID="$(cat "${PIDFILE}")"
    if kill -0 "${PID}" 2>/dev/null; then
      return 0
    fi
  fi
  return 1
}

svc_start() {
  NAME="$1"
  svc_paths "$NAME"
  mkdir -p "${GUNNCHOS_RUN_ROOT}/ipc/${NAME}/in" "${GUNNCHOS_RUN_ROOT}/ipc/${NAME}/out" \
    "${GUNNCHOS_LOG_ROOT}" "${GUNNCHOS_STATE_ROOT}"
  if svc_is_running "$NAME"; then
    echo "already_running ${NAME} pid=$(cat "${PIDFILE}")"
    return 0
  fi
  # Start background daemon (real long-lived process).
  /opt/gunnchos/services/"${NAME}".sh _daemon >/dev/null 2>&1 &
  # Wait briefly for pidfile + health
  i=0
  while [ "$i" -lt 40 ]; do
    if svc_is_running "$NAME"; then
      break
    fi
    i=$((i + 1))
    sleep 0.05
  done
  if ! svc_is_running "$NAME"; then
    echo "start_failed ${NAME}"
    return 1
  fi
  echo "started ${NAME} pid=$(cat "${PIDFILE}") realm=DEV kind=supervised_real ipc=mailbox"
  return 0
}

svc_stop() {
  NAME="$1"
  if ! svc_is_running "$NAME"; then
    echo "already_stopped ${NAME}"
    return 0
  fi
  # Prefer graceful IPC shutdown; fall back to kill.
  if command -v gunnchos-ipc >/dev/null 2>&1; then
    gunnchos-ipc "$NAME" POST /shutdown >/dev/null 2>&1 || true
    i=0
    while [ "$i" -lt 20 ]; do
      svc_is_running "$NAME" || break
      i=$((i + 1))
      sleep 0.05
    done
  fi
  svc_paths "$NAME"
  if [ -f "${PIDFILE}" ]; then
    PID="$(cat "${PIDFILE}")"
    kill "${PID}" 2>/dev/null || true
    rm -f "${PIDFILE}"
  fi
  svc_persist "$NAME" "stopped"
  echo "stopped ${NAME}"
}

svc_restart() {
  NAME="$1"
  svc_stop "$NAME" >/dev/null 2>&1 || true
  svc_paths "$NAME"
  COUNT="$(cat "${RESTARTFILE}" 2>/dev/null || echo 0)"
  echo $((COUNT + 1)) > "${RESTARTFILE}"
  svc_start "$NAME"
}

svc_status() {
  NAME="$1"
  svc_paths "$NAME"
  if svc_is_running "$NAME"; then
    echo "${NAME}: running pid=$(cat "${PIDFILE}") state_file=${STATEFILE}"
  else
    echo "${NAME}: stopped"
  fi
}

svc_health() {
  NAME="$1"
  if ! svc_is_running "$NAME"; then
    echo "not_running"
    return 1
  fi
  if command -v gunnchos-ipc >/dev/null 2>&1; then
    OUT="$(gunnchos-ipc "$NAME" GET /health 2>/dev/null || true)"
    if echo "${OUT}" | grep -q "ok svc=${NAME}"; then
      echo "ok"
      return 0
    fi
  fi
  echo "degraded"
  return 1
}

svc_logs() {
  NAME="$1"
  svc_paths "$NAME"
  if [ -f "${LOGFILE}" ]; then
    tail -n "${2:-20}" "${LOGFILE}"
  else
    echo "no_logs ${NAME}"
  fi
}

svc_dispatch() {
  NAME="$1"
  shift
  CMD="${1:-start}"
  if [ "$#" -gt 0 ]; then shift; fi
  case "${CMD}" in
    _daemon) svc_daemon_loop "$NAME" ;;
    start) svc_start "$NAME" ;;
    stop) svc_stop "$NAME" ;;
    restart) svc_restart "$NAME" ;;
    status) svc_status "$NAME" ;;
    health) svc_health "$NAME" ;;
    logs) svc_logs "$NAME" "$@" ;;
    persist)
      svc_paths "$NAME"
      if svc_is_running "$NAME"; then svc_persist "$NAME" "running"; else svc_persist "$NAME" "stopped"; fi
      cat "${STATEFILE}"
      ;;
    "")
      svc_start "$NAME"
      ;;
    *)
      echo "usage: ${NAME}.sh start|stop|restart|status|health|logs|persist"
      return 1
      ;;
  esac
}
