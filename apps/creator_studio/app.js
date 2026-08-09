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
let current = "hello.py";
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
editor.addEventListener("input", () => { PROJECTS[current] = editor.value; });
document.getElementById("run").onclick = () => {
  term.textContent += `> run ${current}\n` + (current.endsWith(".py") ? "hello from Creator Studio\n" : `executed ${current}\n`);
};
document.getElementById("build").onclick = () => {
  term.textContent += "> build / package\nbuild-ok\nartifact=dist/app-package.dev.json\n";
};
document.getElementById("assist").onclick = () => {
  term.textContent += "> gunnchAI assist (local/DEV)\nsuggestion: add type hints and a pytest smoke test\n";
};
document.getElementById("git-refresh").onclick = () => {
  git.textContent = "On branch local-studio\nChanges not staged:\n  modified: " + current + "\n(use host git via first_party_apps.creator_studio backend for real status)";
};
document.getElementById("layout-mode").onchange = (e) => {
  document.body.classList.toggle("dsxl", e.target.value === "dsxl");
  debug.textContent = JSON.stringify({ layout: e.target.value, serial: "DEV-UART-0", ring: "paired-sim" }, null, 2);
};
renderFiles();
document.getElementById("git-refresh").click();
document.getElementById("layout-mode").dispatchEvent(new Event("change"));
