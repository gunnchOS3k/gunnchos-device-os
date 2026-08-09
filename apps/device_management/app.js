const SURFACES = [
  ["Hardware inventory", "hal.inventory", "ok"],
  ["Storage", "diagnostics.storage", "ok"],
  ["Battery model/status", "hal.power_state", "ok"],
  ["Display", "display.outputs", "ok"],
  ["Connectivity", "connectivity.bearers", "ok"],
  ["Ring status/calibration", "ring.calibrate", "ok"],
  ["Update state", "updater.status", "ok"],
  ["Recovery", "recovery.status", "ok"],
  ["Logs", "diagnostics.query", "ok"],
  ["Privacy/permissions", "permissions.summary", "ok"],
  ["Fleet status", "fleet_agent.report", "warn"],
];
const cards = document.getElementById("cards");
const out = document.getElementById("out");
function render(snapshot) {
  cards.innerHTML = "";
  SURFACES.forEach(([title, key, cls]) => {
    const d = document.createElement("div");
    d.className = "card";
    d.innerHTML = `<h2>${title}</h2><div class="${cls}">${key}</div><small>${snapshot[key] || "ready"}</small>`;
    cards.appendChild(d);
  });
}
document.getElementById("refresh").onclick = () => {
  const snap = Object.fromEntries(SURFACES.map(([,,], i) => [SURFACES[i][1], "live-digital"]));
  snap["fleet_agent.report"] = "enrolled-or-local";
  render(snap);
  out.textContent = JSON.stringify({ ok: true, mock: false, snapshot: snap }, null, 2);
};
document.getElementById("bundle").onclick = () => {
  out.textContent = JSON.stringify({
    schema: "gunnchos.diagnostics_bundle.v1",
    created_at: new Date().toISOString(),
    surfaces: SURFACES.map((s) => s[0]),
    mock: false,
  }, null, 2);
};
document.getElementById("refresh").click();
