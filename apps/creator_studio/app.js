const PROJECTS = {
  "hello.py": "print('hello from Creator Studio')\n",
  "Makefile": "all:\n\t@echo build-ok\n",
  "notes.md": "# Studio notes\n",
};
const files = document.getElementById("files");
const editor = document.getElementById("editor");
const term = document.getElementById("term");
const git = document.getElementById("git");
const debug = document.getElementById("debug");
const statusEl = document.getElementById("shell-status");
let current = "hello.py";
let busy = false;

function setStatus(kind, text) {
  statusEl.dataset.state = kind;
  statusEl.textContent = text;
}

function setEmptyTerminal() {
  term.textContent = "";
  term.dataset.state = "empty";
  setStatus("empty", "Terminal empty — companion shell is not wired to gunnchSDK sandbox I/O.");
}

function renderFiles() {
  files.innerHTML = "";
  Object.keys(PROJECTS).forEach((name) => {
    const li = document.createElement("li");
    const b = document.createElement("button");
    b.textContent = name;
    b.onclick = () => { current = name; editor.value = PROJECTS[name]; };
    li.appendChild(b); files.appendChild(li);
  });
  editor.value = PROJECTS[current];
}

function previewAction(label) {
  if (busy) return;
  busy = true;
  setStatus("loading", `Loading ${label}…`);
  term.dataset.state = "loading";
  term.textContent = `> ${label}\n[loading]`;
  window.setTimeout(() => {
    busy = false;
    // Honest preview: do NOT invent success stdout that looks like a real SDK run.
    term.dataset.state = "error";
    term.textContent =
      `> ${label}\n` +
      `[preview-only] Companion HTML cannot execute sandbox run/build.\n` +
      `Use sdk/apps/creator_studio via gunnchSDK package→install→run for real artifacts.\n` +
      `S2 OPEN: shell not wired to sandbox runtime I/O.\n`;
    setStatus("error", "Preview-only — real run/build lives in the Python/SDK runtime.");
  }, 250);
}

editor.addEventListener("input", () => { PROJECTS[current] = editor.value; });
document.getElementById("run").onclick = () => previewAction(`run ${current}`);
document.getElementById("build").onclick = () => previewAction("build / package");
document.getElementById("assist").onclick = () => previewAction("gunnchAI assist");
document.getElementById("git-refresh").onclick = () => {
  git.textContent =
    "(preview) Git status is not live in this shell.\n" +
    `Current buffer: ${current}\n` +
    "Host git status comes from first_party_apps.creator_studio on SDK run.";
};
document.getElementById("layout-mode").onchange = (e) => {
  document.body.classList.toggle("dsxl", e.target.value === "dsxl");
  debug.textContent = JSON.stringify(
    { layout: e.target.value, serial: "DEV-UART-0", ring: "paired-sim", shell: "companion_preview" },
    null,
    2
  );
};
renderFiles();
setEmptyTerminal();
document.getElementById("git-refresh").click();
document.getElementById("layout-mode").dispatchEvent(new Event("change"));
