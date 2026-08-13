const memoryEl = document.getElementById("memory");
const replyEl = document.getElementById("reply");
const safetyEl = document.getElementById("safety");
const statusEl = document.getElementById("shell-status");
const continuityEl = document.getElementById("continuity");
let wired = false;
let memoryTurns = [];

function setStatus(kind, text) {
  statusEl.dataset.state = kind;
  statusEl.textContent = text;
}

function setContinuity(text) {
  continuityEl.textContent = text;
}

async function sdkFetch(path, options) {
  const res = await fetch(path, options);
  let payload = null;
  try {
    payload = await res.json();
  } catch (_err) {
    payload = null;
  }
  if (!res.ok) {
    const err = new Error((payload && (payload.error || payload.result && payload.result.error)) || `http_${res.status}`);
    err.payload = payload;
    err.status = res.status;
    throw err;
  }
  return payload;
}

function renderMemory() {
  if (!memoryTurns.length) {
    memoryEl.innerHTML = `<p class="empty">No turns yet in SDK sandbox memory.</p>`;
    return;
  }
  memoryEl.innerHTML = memoryTurns
    .slice(-8)
    .map((t) => {
      const at = t.at ? new Date(typeof t.at === "number" ? t.at * 1000 : t.at).toISOString() : "";
      return (
        `<article class="turn-card">` +
        `<p class="meta">${at} · ${t.profile || ""} · ${t.topic || ""}${t.waike_lesson ? " · " + t.waike_lesson : ""}</p>` +
        `<p><strong>You:</strong> ${t.prompt || ""}</p>` +
        `<p><strong>SDK reply:</strong> ${(t.reply || "").toString().slice(0, 280)}</p>` +
        `</article>`
      );
    })
    .join("");
}

function setEmptyReply() {
  replyEl.dataset.state = "empty";
  replyEl.textContent = "Waiting for a question…";
  setStatus("empty", "Empty — Ask uses gunnchSDK tutor runtime when bridge is up.");
}

async function hydrateMemory() {
  const mem = await sdkFetch("/api/gunnchai/memory");
  memoryTurns = ((mem.memory || {}).turns) || [];
  renderMemory();
}

async function connectBridge() {
  setStatus("loading", "Connecting Ask to gunnchSDK tutor runtime…");
  try {
    const health = await sdkFetch("/api/health");
    if (!health.ok || !health.wired) throw new Error("bridge_not_wired");
    wired = true;
    setContinuity(
      "CONTINUITY: SDK_SANDBOX_MEMORY — browser Ask shares tutor_memory.json with first_party gunnchSDK runtime."
    );
    await hydrateMemory();
    setStatus("ready", "Ask wired to local SDK/tutor sandbox runtime.");
  } catch (err) {
    wired = false;
    setContinuity(
      "CONTINUITY: RUNTIME_UNAVAILABLE — fail-closed (no DISCONNECTED_PREVIEW replies)."
    );
    replyEl.dataset.state = "error";
    replyEl.textContent =
      "RUNTIME_UNAVAILABLE — companion bridge not reachable.\n" +
      "Start: python3 scripts/platform001_companion_bridge.py\n" +
      "Fail-closed: Ask will not invent disconnected preview replies.";
    setStatus("error", "Degraded — SDK tutor runtime unavailable.");
  }
}

document.getElementById("ask").onclick = async () => {
  const profile = document.getElementById("profile").value;
  const topic = document.getElementById("topic").value.trim() || "general";
  const lesson = document.getElementById("lesson").value;
  const prompt = document.getElementById("prompt").value.trim();
  if (!prompt) {
    replyEl.dataset.state = "error";
    replyEl.textContent = "Enter a question first.";
    setStatus("error", "Empty prompt.");
    return;
  }
  setStatus("loading", "Asking gunnchSDK tutor runtime…");
  replyEl.dataset.state = "loading";
  replyEl.textContent = "Loading…";
  try {
    const payload = await sdkFetch("/api/gunnchai/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile, topic, lesson, prompt }),
    });
    wired = true;
    setContinuity(
      "CONTINUITY: SDK_SANDBOX_MEMORY — reply + turn persisted via first_party_apps.gunnchai_tutor."
    );
    const result = payload.result || {};
    if (result.error === "prompt_blocked" || payload.error === "prompt_blocked") {
      replyEl.dataset.state = "error";
      replyEl.textContent =
        "Prompt blocked by SDK safety gate.\nRecovery: rephrase without injection/exfil patterns.";
      safetyEl.textContent = `Safety: ${(result.guard && result.guard.reason) || "prompt_injection_suspected"}`;
      setStatus("error", "Blocked by SDK tutor safety gate.");
      return;
    }
    const text = (result.reply && result.reply.text) || "(empty SDK reply)";
    replyEl.dataset.state = result.ok ? "ready" : "error";
    replyEl.textContent = text;
    const safety = result.safety || {};
    safetyEl.textContent = `Safety: ${safety.safe_to_show ? "safe_to_show" : "blocked"} (SDK runtime)`;
    await hydrateMemory();
    setStatus(
      result.ok ? "ready" : "error",
      result.ok
        ? `SDK reply shown · sessions=${result.persisted_session_count || "?"}`
        : "SDK tutor returned non-ok (honest fail)."
    );
  } catch (err) {
    const blocked = err.status === 403 || (err.payload && err.payload.result && err.payload.result.error === "prompt_blocked");
    if (blocked) {
      replyEl.dataset.state = "error";
      replyEl.textContent =
        "Prompt blocked by SDK safety gate.\nRecovery: rephrase without injection/exfil patterns.";
      safetyEl.textContent = "Safety: prompt_injection_suspected";
      setStatus("error", "Blocked by SDK tutor safety gate.");
      return;
    }
    wired = false;
    setContinuity(
      "CONTINUITY: RUNTIME_UNAVAILABLE — fail-closed (no DISCONNECTED_PREVIEW replies)."
    );
    replyEl.dataset.state = "error";
    replyEl.textContent =
      "RUNTIME_UNAVAILABLE — Ask did not reach gunnchSDK tutor runtime.\n" +
      "Fail-closed: no disconnected preview reply invented.\n" +
      `detail: ${err.message || err}`;
    safetyEl.textContent = "Safety: unavailable (runtime down)";
    setStatus("error", "Degraded — Ask failed closed without fake preview.");
  }
};

setEmptyReply();
renderMemory();
connectBridge();
