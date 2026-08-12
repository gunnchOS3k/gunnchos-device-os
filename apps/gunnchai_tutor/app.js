const memory = [];
const replyEl = document.getElementById("reply");
const memoryEl = document.getElementById("memory");
const safetyEl = document.getElementById("safety");
const statusEl = document.getElementById("shell-status");
const continuityEl = document.getElementById("continuity");

function setStatus(kind, text) {
  statusEl.dataset.state = kind;
  statusEl.textContent = text;
}

function renderMemory() {
  if (!memory.length) {
    memoryEl.innerHTML = `<p class="empty">No turns yet.</p>`;
    return;
  }
  memoryEl.innerHTML = memory
    .slice(-8)
    .map(
      (t) =>
        `<article class="turn-card"><p class="meta">${t.at} · ${t.profile} · ${t.topic}${t.lesson ? " · " + t.lesson : ""}</p><p><strong>You:</strong> ${t.prompt}</p><p><strong>Preview reply:</strong> ${t.preview}</p></article>`
    )
    .join("");
}

function setEmptyReply() {
  replyEl.dataset.state = "empty";
  replyEl.textContent = "Waiting for a question…";
  setStatus("empty", "Empty — ask a question to see a disconnected companion preview.");
}

continuityEl.textContent =
  "CONTINUITY: DISCONNECTED_PREVIEW — browser Ask does not share state with gunnchSDK Python runtime memory.";

document.getElementById("ask").onclick = () => {
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
  setStatus("loading", "Loading preview reply…");
  replyEl.dataset.state = "loading";
  replyEl.textContent = "Loading…";
  window.setTimeout(() => {
    const blocked = /ignore previous|exfiltrate|<tool>|system:/i.test(prompt);
    if (blocked) {
      replyEl.dataset.state = "error";
      replyEl.textContent =
        "Prompt blocked by local safety gate.\nRecovery: rephrase without injection/exfil patterns, then retry in the SDK runtime.";
      safetyEl.textContent = "Safety: prompt_injection_suspected";
      setStatus("error", "Blocked by companion preview safety gate.");
      return;
    }
    const text =
      `[DISCONNECTED PREVIEW — not SDK session memory]\n` +
      `Local template reply for ${topic}` +
      (lesson ? ` (WAIKE: ${lesson})` : "") +
      `.\n\nAI suggests; human verifies.\n\nPrompt: ${prompt}`;
    replyEl.dataset.state = "ready";
    replyEl.textContent = text;
    safetyEl.textContent = "Safety: safe_to_show (companion shell preview only)";
    memory.push({
      profile,
      topic,
      lesson,
      prompt,
      preview: text.split("\n")[1] || text,
      at: new Date().toISOString(),
    });
    renderMemory();
    setStatus(
      "ready",
      "Preview reply shown. S2 OPEN: browser Ask remains disconnected from SDK runtime."
    );
  }, 220);
};

setEmptyReply();
renderMemory();
