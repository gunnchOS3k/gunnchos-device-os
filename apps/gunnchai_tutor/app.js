const memory = [];
const replyEl = document.getElementById("reply");
const memoryEl = document.getElementById("memory");
const safetyEl = document.getElementById("safety");

document.getElementById("ask").onclick = () => {
  const profile = document.getElementById("profile").value;
  const topic = document.getElementById("topic").value.trim() || "general";
  const lesson = document.getElementById("lesson").value;
  const prompt = document.getElementById("prompt").value.trim();
  if (!prompt) {
    replyEl.textContent = "Enter a question first.";
    return;
  }
  const blocked = /ignore previous|exfiltrate|<tool>|system:/i.test(prompt);
  if (blocked) {
    replyEl.textContent = "Prompt blocked by local safety gate.";
    safetyEl.textContent = "Safety: prompt_injection_suspected";
    return;
  }
  const text =
    `Local template reply for ${topic}` +
    (lesson ? ` (WAIKE: ${lesson})` : "") +
    `.\n\nAI suggests; human verifies.\n\nPrompt: ${prompt}`;
  replyEl.textContent = text;
  safetyEl.textContent = "Safety: safe_to_show (companion shell preview)";
  memory.push({ profile, topic, lesson, prompt, at: new Date().toISOString() });
  memoryEl.textContent = JSON.stringify(memory.slice(-8), null, 2);
};
