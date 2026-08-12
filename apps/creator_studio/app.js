const files = document.getElementById("files");
const editor = document.getElementById("editor");
const term = document.getElementById("term");
const git = document.getElementById("git");
const debug = document.getElementById("debug");
const statusEl = document.getElementById("shell-status");
let PROJECTS = {};
let current = "hello.py";
let busy = false;
let wired = false;

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
    err.status = res.status;
    throw err;
  }
  return payload;
}

function renderFiles() {
  files.innerHTML = "";
  const names = Object.keys(PROJECTS);
  if (!names.length) {
    files.innerHTML = "<li>(waiting for sandbox workspace)</li>";
    return;
  }
  if (!names.includes(current)) current = names[0];
  names.forEach((name) => {
    const li = document.createElement("li");
    const b = document.createElement("button");
    b.textContent = name;
    b.onclick = () => {
      current = name;
      editor.value = PROJECTS[name];
    };
    li.appendChild(b);
    files.appendChild(li);
  });
  editor.value = PROJECTS[current] || "";
}

function applyCreatorResult(result) {
  const workspaceFiles = result.files || [];
  if (workspaceFiles.length) {
    // Keep editor buffers; seed missing names from last run listing.
    workspaceFiles.forEach((name) => {
      if (!(name in PROJECTS)) PROJECTS[name] = "";
    });
  }
  if (result.run || result.build || result.gunnchai_assist) {
    const run = result.run || {};
    const build = result.build || {};
    const assist = result.gunnchai_assist || {};
    term.dataset.state = result.ok ? "ready" : "error";
    term.textContent =
      `> sdk run_creator_studio (sandbox)\n` +
      `run exit=${run.code} stdout=${run.stdout || ""}\n` +
      `build exit=${build.code} package_ok=${build.package_ok} artifact=${build.artifact || ""}\n` +
      `assist ok=${assist.ok} mode=${assist.mode || ""}\n` +
      (assist.suggestion ? `assist: ${assist.suggestion}\n` : "") +
      `persisted_run_count=${result.persisted_run_count}\n` +
      `workspace=${result.workspace || ""}\n`;
  }
  if (Array.isArray(result.git_status_preview)) {
    git.textContent = result.git_status_preview.join("\n") || "(clean)";
  }
  if (result.device_debug) {
    debug.textContent = JSON.stringify(
      { ...result.device_debug, shell: "sdk_bridge_wired", wired: true },
      null,
      2
    );
  }
  renderFiles();
}

async function connectAndHydrate() {
  setStatus("loading", "Connecting to gunnchSDK companion bridge…");
  try {
    const health = await sdkFetch("/api/health");
    if (!health.ok || !health.wired) throw new Error("bridge_not_wired");
    wired = true;
    const runPayload = await sdkFetch("/api/creator/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        layout: document.getElementById("layout-mode").value || "single",
      }),
    });
    applyCreatorResult(runPayload.result || {});
    // Load workspace file bodies from known seed names when empty.
    ["hello.py", "Makefile", "notes.md"].forEach((name) => {
      if (!(name in PROJECTS)) PROJECTS[name] = "";
    });
    renderFiles();
    setStatus(
      "ready",
      `Wired to sandbox I/O · runs=${(runPayload.result || {}).persisted_run_count || "?"}`
    );
  } catch (err) {
    wired = false;
    term.dataset.state = "error";
    term.textContent =
      "RUNTIME_UNAVAILABLE — companion bridge not reachable.\n" +
      "Start: python3 scripts/platform001_companion_bridge.py\n" +
      "Fail-closed: no mock terminal success.\n" +
      `detail: ${err.message || err}`;
    setStatus("error", "Degraded — SDK bridge unavailable (fail-closed).");
  }
}

async function invokeStudio(label) {
  if (busy) return;
  busy = true;
  setStatus("loading", `Invoking SDK ${label}…`);
  term.dataset.state = "loading";
  term.textContent = `> ${label}\n[loading sandbox…]`;
  try {
    if (!wired) {
      const health = await sdkFetch("/api/health");
      if (!health.ok) throw new Error("bridge_not_wired");
      wired = true;
    }
    const payload = await sdkFetch("/api/creator/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        layout: document.getElementById("layout-mode").value || "single",
      }),
    });
    applyCreatorResult(payload.result || {});
    setStatus(
      payload.ok ? "ready" : "error",
      payload.ok
        ? `SDK ${label} complete · sandbox wired`
        : `SDK ${label} failed (honest runtime result)`
    );
  } catch (err) {
    wired = false;
    term.dataset.state = "error";
    term.textContent =
      `> ${label}\n` +
      `RUNTIME_UNAVAILABLE — fail-closed (no mock stdout).\n` +
      `detail: ${err.message || err}\n`;
    setStatus("error", "Degraded — SDK bridge unavailable.");
  } finally {
    busy = false;
  }
}

editor.addEventListener("input", () => {
  PROJECTS[current] = editor.value;
});
document.getElementById("run").onclick = () => invokeStudio(`run ${current}`);
document.getElementById("build").onclick = () => invokeStudio("build / package");
document.getElementById("assist").onclick = () => invokeStudio("gunnchAI assist");
document.getElementById("git-refresh").onclick = async () => {
  try {
    const payload = await sdkFetch("/api/creator/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        layout: document.getElementById("layout-mode").value || "single",
      }),
    });
    applyCreatorResult(payload.result || {});
    setStatus("ready", "Git status from SDK sandbox run.");
  } catch (err) {
    git.textContent =
      "RUNTIME_UNAVAILABLE — cannot refresh git via SDK bridge.\n" +
      `detail: ${err.message || err}`;
    setStatus("error", "Degraded — git refresh failed closed.");
  }
};
document.getElementById("layout-mode").onchange = (e) => {
  document.body.classList.toggle("dsxl", e.target.value === "dsxl");
  debug.textContent = JSON.stringify(
    {
      layout: e.target.value,
      serial: "DEV-UART-0",
      ring: "paired-sim",
      shell: wired ? "sdk_bridge_wired" : "runtime_unavailable",
    },
    null,
    2
  );
};
document.getElementById("layout-mode").dispatchEvent(new Event("change"));
connectAndHydrate();
