const state = {
  courses: [],
  selected: null,
  progress: {},
  role: "learner",
  wired: false,
};
const courseList = document.getElementById("courses");
const labs = document.getElementById("labs");
const progressEl = document.getElementById("progress");
const contentEl = document.getElementById("lesson-content");
const assignmentEl = document.getElementById("assignment");
const titleEl = document.getElementById("lesson-title");
const statusEl = document.getElementById("shell-status");
const tutorEl = document.getElementById("tutor-note");

function selectedCourse() {
  return state.courses.find((c) => c.course_id === state.selected) || state.courses[0];
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
    progressEl.innerHTML = `<p class="empty">No progress yet — start a course seed to persist via gunnchSDK sandbox when the companion bridge is up.</p>`;
    return;
  }
  progressEl.innerHTML = entries
    .map(([id, row]) => {
      const title = (state.courses.find((c) => c.course_id === id) || { title: id }).title;
      return (
        `<article class="progress-card"><h3>${title}</h3>` +
        `<p>Status: <strong>${row.status}</strong></p>` +
        `<p>Role: ${row.role}</p>` +
        `<p>Progress: ${row.pct != null ? row.pct + "%" : "n/a"}</p>` +
        `<p>Lab: ${row.lab_ok == null ? "n/a" : row.lab_ok ? "ran" : "failed"}</p>` +
        `<p>Source: ${row.source || "local"}</p></article>`
      );
    })
    .join("");
}

function render() {
  const course = selectedCourse();
  if (!course) {
    contentEl.innerHTML = `<p class="empty">courses.json missing — not a pack-ID browser, and not a hidden complete curriculum.</p>`;
    return;
  }
  courseList.innerHTML = "";
  state.courses.forEach((c) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = c.title;
    btn.onclick = () => {
      state.selected = c.course_id;
      render();
    };
    if (c.course_id === state.selected) btn.style.outline = "2px solid var(--accent)";
    li.appendChild(btn);
    courseList.appendChild(li);
  });
  titleEl.textContent = course.title;
  contentEl.innerHTML =
    `<p>${course.lesson_excerpt}</p>` +
    `<h4>Worked example / tutor</h4>` +
    `<p>${course.worked_example}</p>` +
    `<p class="hint">Seed depth only. Eight-week authorship and student validation are not claimed.</p>`;
  assignmentEl.textContent = course.assignment;
  labs.innerHTML =
    `<p>${course.lab_hint}</p>` +
    `<p class="hint">Executable lab: <code>python3 scripts/run_waike_course_lab.py --course ${course.course_id}</code></p>`;
  tutorEl.textContent = course.worked_example;
  renderProgress();
}

async function loadCatalog() {
  try {
    const catalog = await sdkFetch("courses.json");
    state.courses = catalog.courses || [];
    state.selected = (state.courses[0] || {}).course_id;
    render();
    setStatus("ready", `${state.courses.length} courses loaded (seeds, not complete curriculum).`);
  } catch (err) {
    setStatus("error", `Cannot load courses.json (${err.message || err}).`);
  }
}

async function hydrateFromSandbox() {
  try {
    const health = await sdkFetch("/api/health");
    if (!health.ok || !health.wired) throw new Error("bridge_not_wired");
    state.wired = true;
    const prog = await sdkFetch("/api/waike/progress");
    const appState = prog.app_state || {};
    const portfolio = prog.portfolio || {};
    const cid = appState.last_course_id || appState.last_lesson;
    if (cid) {
      state.progress[cid] = {
        status: "in_progress",
        role: appState.last_role || state.role,
        pct: portfolio.progress_pct,
        lab_ok: portfolio.lab_ok,
        source: "sdk_sandbox",
      };
      if (state.courses.some((c) => c.course_id === cid)) state.selected = cid;
    }
    render();
    setStatus("ready", `Wired to SDK sandbox · sessions=${appState.sessions_completed || 0}`);
  } catch (_err) {
    state.wired = false;
    setStatus(
      "ready",
      "Catalog local. Companion bridge optional — /api/waike/start used when present (fail-closed, no fake durable progress)."
    );
  }
}

document.getElementById("start-lab").onclick = async () => {
  const course = selectedCourse();
  if (!course) return;
  setStatus("loading", "Starting course seed via gunnchSDK waike_app…");
  try {
    const payload = await sdkFetch("/api/waike/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lesson_id: course.course_id,
        course_id: course.course_id,
        role: state.role,
      }),
    });
    state.wired = true;
    const result = payload.result || {};
    state.progress[course.course_id] = {
      status: result.ok ? "in_progress" : "error",
      role: state.role,
      pct: result.persisted_progress_pct,
      lab_ok: !!(result.lab && result.lab.ok),
      source: "sdk_sandbox",
    };
    render();
    setStatus(
      result.ok ? "ready" : "error",
      result.ok
        ? `Seed persisted · progress=${result.persisted_progress_pct}% · lab=${result.lab && result.lab.ok}`
        : "SDK waike_app returned non-ok."
    );
  } catch (err) {
    state.wired = false;
    setStatus(
      "error",
      `RUNTIME_UNAVAILABLE — progress not persisted (fail-closed). Run the Python lab locally. ${err.message || err}`
    );
  }
};

document.getElementById("export-portfolio").onclick = async () => {
  try {
    const prog = await sdkFetch("/api/waike/progress");
    const portfolio = prog.portfolio || {
      schema: "waike.portfolio.v1",
      progress: state.progress,
      full_curriculum_complete: false,
    };
    const blob = new Blob([JSON.stringify(portfolio, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "waike-portfolio.json";
    a.click();
    setStatus("ready", "Portfolio exported from SDK sandbox state.");
  } catch (err) {
    const local = {
      schema: "waike.portfolio.v1",
      progress: state.progress,
      full_curriculum_complete: false,
      note: "local_ui_only_no_sandbox",
    };
    const blob = new Blob([JSON.stringify(local, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "waike-portfolio.json";
    a.click();
    setStatus("error", `Sandbox export unavailable; wrote local UI progress only. ${err.message || err}`);
  }
};

document.getElementById("role").onchange = (e) => {
  state.role = e.target.value;
};
document.getElementById("a11y-high-contrast").onchange = (e) => {
  document.body.classList.toggle("high-contrast", e.target.checked);
};

loadCatalog().then(hydrateFromSandbox);
