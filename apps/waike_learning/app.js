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
const state = { selected: PACKS[0].id, progress: {}, role: "learner", wired: false };
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

async function sdkFetch(path, options) {
  const res = await fetch(path, options);
  let payload = null;
  try {
    payload = await res.json();
  } catch (_err) {
    payload = null;
  }
  if (!res.ok) {
    const err = new Error((payload && payload.error) || `http_${res.status}`);
    err.payload = payload;
    throw err;
  }
  return payload;
}

function renderProgress() {
  const entries = Object.entries(state.progress);
  if (!entries.length) {
    progressEl.innerHTML = `<p class="empty">No progress yet — start a lesson to persist via gunnchSDK sandbox.</p>`;
    return;
  }
  progressEl.innerHTML = entries
    .map(([id, row]) => {
      const title = (PACKS.find((p) => p.id === id) || { title: id }).title;
      return (
        `<article class="progress-card"><h3>${title}</h3>` +
        `<p>Status: <strong>${row.status}</strong></p>` +
        `<p>Role: ${row.role}</p>` +
        `<p>Progress: ${row.pct != null ? row.pct + "%" : "n/a"}</p>` +
        `<p>Source: ${row.source || "local"}</p>` +
        `<p>Started: ${row.started_at || ""}</p></article>`
      );
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
    btn.onclick = () => {
      state.selected = p.id;
      render();
    };
    if (p.id === state.selected) btn.style.outline = "2px solid var(--accent)";
    li.appendChild(btn);
    lessons.appendChild(li);
  });
  labs.textContent = `Selected pack: ${pack.title}`;
  contentEl.innerHTML =
    `<h3>${pack.title}</h3>` +
    `<p>${pack.body}</p>` +
    `<h4>Worked example</h4>` +
    `<p>${pack.worked_example}</p>` +
    `<p class="hint">Full curriculum quality is not claimed — lesson body + SDK durable progress only.</p>`;
  renderProgress();
}

async function hydrateFromSandbox() {
  setStatus("loading", "Connecting WAIKE shell to gunnchSDK sandbox…");
  try {
    const health = await sdkFetch("/api/health");
    if (!health.ok || !health.wired) throw new Error("bridge_not_wired");
    state.wired = true;
    const prog = await sdkFetch("/api/waike/progress");
    const appState = prog.app_state || {};
    const portfolio = prog.portfolio || {};
    if (appState.last_lesson) {
      state.progress[appState.last_lesson] = {
        status: "in_progress",
        role: appState.last_role || state.role,
        pct: portfolio.progress_pct,
        source: "sdk_sandbox",
        started_at: new Date((appState.updated_at || Date.now() / 1000) * 1000).toISOString(),
      };
    }
    render();
    setStatus(
      "ready",
      `Wired to SDK sandbox · sessions=${appState.sessions_completed || 0}`
    );
  } catch (err) {
    state.wired = false;
    render();
    setStatus(
      "error",
      "Degraded — SDK bridge unavailable (fail-closed; local UI only, no fake durable progress)."
    );
  }
}

document.getElementById("start-lab").onclick = async () => {
  setStatus("loading", "Starting lesson via gunnchSDK waike_app…");
  try {
    const payload = await sdkFetch("/api/waike/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lesson_id: state.selected, role: state.role }),
    });
    state.wired = true;
    const result = payload.result || {};
    state.progress[state.selected] = {
      started_at: new Date().toISOString(),
      role: state.role,
      status: result.ok ? "in_progress" : "error",
      pct: result.persisted_progress_pct,
      source: "sdk_sandbox",
      a11y: document.getElementById("a11y-high-contrast").checked,
    };
    render();
    setStatus(
      result.ok ? "ready" : "error",
      result.ok
        ? `Lesson persisted in SDK sandbox · progress=${result.persisted_progress_pct}%`
        : "SDK waike_app returned non-ok."
    );
  } catch (err) {
    state.wired = false;
    setStatus(
      "error",
      `RUNTIME_UNAVAILABLE — lesson not persisted (fail-closed). ${err.message || err}`
    );
  }
};

document.getElementById("export-portfolio").onclick = async () => {
  try {
    const prog = await sdkFetch("/api/waike/progress");
    const portfolio = prog.portfolio || {
      schema: "waike.portfolio.v1",
      progress: state.progress,
      note: "empty_sandbox_portfolio",
    };
    const blob = new Blob([JSON.stringify(portfolio, null, 2)], {
      type: "application/json",
    });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "waike-portfolio.json";
    a.click();
    setStatus("ready", "Portfolio exported from SDK sandbox state.");
  } catch (err) {
    setStatus(
      "error",
      `RUNTIME_UNAVAILABLE — cannot export sandbox portfolio. ${err.message || err}`
    );
  }
};

document.getElementById("role").onchange = (e) => {
  state.role = e.target.value;
};
document.getElementById("a11y-high-contrast").onchange = (e) => {
  document.body.classList.toggle("high-contrast", e.target.checked);
};
render();
hydrateFromSandbox();
