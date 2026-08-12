const PACKS = [
  {
    id: "wireless_basics_101",
    title: "Wireless Basics 101",
    kind: "lesson",
    body:
      "Learn what a radio link is, how OFDM carries many subcarriers, and why offline packs matter when the lab network is unavailable.",
    worked_example:
      "Example: sketch a 3-subcarrier OFDM symbol, label cyclic prefix, then check the offline pack quiz item #1.",
  },
  {
    id: "waike_gary_upnow_intro",
    title: "Gary UpNow Intro",
    kind: "lab",
    body:
      "Kinesthetic lab intro: stand, move, and map motion cues to wireless concepts with a short offline checklist.",
    worked_example:
      "Example: complete the warm-up motion, mark the checklist, then export a portfolio note for your educator.",
  },
  {
    id: "python_starter_pack",
    title: "Python Starter Pack",
    kind: "offline_pack",
    body:
      "Offline Python starter for WAIKE labs — edit a tiny script, run it in the SDK runtime, and capture progress.",
    worked_example:
      "Example: change the greet() string, re-run via gunnchSDK, then bump progress after the lab check.",
  },
];
const state = { selected: PACKS[0].id, progress: {}, role: "learner" };
const lessons = document.getElementById("lessons");
const labs = document.getElementById("labs");
const progressEl = document.getElementById("progress");
const contentEl = document.getElementById("lesson-content");
const statusEl = document.getElementById("shell-status");

function selectedPack() {
  return PACKS.find((p) => p.id === state.selected) || PACKS[0];
}

function setStatus(kind, text) {
  statusEl.dataset.state = kind;
  statusEl.textContent = text;
}

function renderProgress() {
  const entries = Object.entries(state.progress);
  if (!entries.length) {
    progressEl.innerHTML = `<p class="empty">No progress yet — start a lesson to see learner-facing status (not raw JSON).</p>`;
    return;
  }
  progressEl.innerHTML = entries
    .map(([id, row]) => {
      const title = (PACKS.find((p) => p.id === id) || { title: id }).title;
      return `<article class="progress-card"><h3>${title}</h3><p>Status: <strong>${row.status}</strong></p><p>Role: ${row.role}</p><p>Started: ${row.started_at}</p></article>`;
    })
    .join("");
}

function render() {
  const pack = selectedPack();
  lessons.innerHTML = "";
  PACKS.forEach((p) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.textContent = `${p.title} (${p.kind})`;
    btn.onclick = () => { state.selected = p.id; render(); };
    if (p.id === state.selected) btn.style.outline = "2px solid var(--accent)";
    li.appendChild(btn); lessons.appendChild(li);
  });
  labs.textContent = `Selected pack: ${pack.title}`;
  contentEl.innerHTML =
    `<h3>${pack.title}</h3>` +
    `<p>${pack.body}</p>` +
    `<h4>Worked example</h4>` +
    `<p>${pack.worked_example}</p>` +
    `<p class="hint">Full curriculum quality is not claimed — this is a digital lesson body surface for PLATFORM UX honesty.</p>`;
  renderProgress();
  setStatus("ready", "Lesson body visible. Companion shell still preview-only vs gunnchSDK persistence.");
}

document.getElementById("start-lab").onclick = () => {
  setStatus("loading", "Starting lesson…");
  window.setTimeout(() => {
    state.progress[state.selected] = {
      started_at: new Date().toISOString(),
      role: state.role,
      status: "in_progress",
      a11y: document.getElementById("a11y-high-contrast").checked,
    };
    render();
    setStatus("ready", "Lesson marked in-progress in companion preview (SDK runtime owns durable progress).");
  }, 200);
};
document.getElementById("export-portfolio").onclick = () => {
  if (!Object.keys(state.progress).length) {
    setStatus("error", "Nothing to export yet — start a lesson first.");
    return;
  }
  const blob = new Blob(
    [JSON.stringify({ schema: "waike.portfolio.v1", progress: state.progress }, null, 2)],
    { type: "application/json" }
  );
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "waike-portfolio.json";
  a.click();
  setStatus("ready", "Portfolio JSON downloaded from companion preview.");
};
document.getElementById("role").onchange = (e) => { state.role = e.target.value; };
document.getElementById("a11y-high-contrast").onchange = (e) => {
  document.body.classList.toggle("high-contrast", e.target.checked);
};
render();
