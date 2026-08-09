const PACKS = [
  { id: "wireless_basics_101", title: "Wireless Basics 101", kind: "lesson" },
  { id: "waike_gary_upnow_intro", title: "Gary UpNow Intro", kind: "lab" },
  { id: "python_starter_pack", title: "Python Starter Pack", kind: "offline_pack" },
];
const state = { selected: PACKS[0].id, progress: {}, role: "learner" };
const lessons = document.getElementById("lessons");
const labs = document.getElementById("labs");
const progressEl = document.getElementById("progress");
function render() {
  lessons.innerHTML = "";
  PACKS.forEach((p) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.textContent = `${p.title} (${p.kind})`;
    btn.onclick = () => { state.selected = p.id; render(); };
    if (p.id === state.selected) btn.style.outline = "2px solid var(--accent)";
    li.appendChild(btn); lessons.appendChild(li);
  });
  labs.textContent = `Selected: ${state.selected}`;
  progressEl.textContent = JSON.stringify(state.progress, null, 2);
}
document.getElementById("start-lab").onclick = () => {
  state.progress[state.selected] = {
    started_at: new Date().toISOString(),
    role: state.role,
    status: "in_progress",
    a11y: document.getElementById("a11y-high-contrast").checked,
  };
  render();
};
document.getElementById("export-portfolio").onclick = () => {
  const blob = new Blob([JSON.stringify({ schema: "waike.portfolio.v1", progress: state.progress }, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "waike-portfolio.json";
  a.click();
};
document.getElementById("role").onchange = (e) => { state.role = e.target.value; };
document.getElementById("a11y-high-contrast").onchange = (e) => {
  document.body.classList.toggle("high-contrast", e.target.checked);
};
render();
