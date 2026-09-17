(function () {
  const lib = window.VC_LIBRARY || { tasks: [], packs: [], edmund: { actions: [] }, consent_text: "" };
  const STORAGE_KEY = "gunnchos.validation_center.v1";

  const state = loadState() || {
    mode: "home",
    sessions: [],
    currentSessionId: null,
    taskIndex: 0,
    a11y: { textSize: "100", spacing: "normal", reducedMotion: false, highContrast: false, simpleLanguage: false, readAloud: false },
    autosaveStatus: "idle",
  };

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  function loadState() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    } catch {
      return null;
    }
  }

  function setAutosave(msg) {
    state.autosaveStatus = msg;
    const el = $("#autosave-status");
    if (el) {
      el.textContent = "Autosave: " + msg;
      el.setAttribute("data-status-text", msg);
    }
  }

  function saveState() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    setAutosave("saved " + new Date().toLocaleTimeString());
  }

  function currentSession() {
    return state.sessions.find((s) => s.session_id === state.currentSessionId) || null;
  }

  function taskById(id) {
    return lib.tasks.find((t) => t.task_id === id);
  }

  function applyA11y() {
    const root = document.documentElement;
    root.style.setProperty("--text-scale", String(Number(state.a11y.textSize) / 100));
    root.classList.toggle("reduced-motion", !!state.a11y.reducedMotion);
    root.classList.toggle("high-contrast", !!state.a11y.highContrast);
    root.classList.remove("spacing-relaxed", "spacing-wide");
    if (state.a11y.spacing === "relaxed") root.classList.add("spacing-relaxed");
    if (state.a11y.spacing === "wide") root.classList.add("spacing-wide");
  }

  function setMode(mode) {
    state.mode = mode;
    $$(".mode-btn").forEach((btn) => btn.setAttribute("aria-pressed", String(btn.dataset.mode === mode)));
    ["home", "entry", "moderator", "participant", "reviewer"].forEach((m) => {
      const view = $("#view-" + m);
      if (view) view.hidden = m !== mode;
    });
    saveState();
    render();
  }

  function fillPackSelectors() {
    const packSelect = $("#pack-select");
    const taskSelect = $("#task-select");
    if (!packSelect || !taskSelect) return;
    packSelect.innerHTML = "";
    lib.packs.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.pack_id;
      opt.textContent = p.pack_id + " (" + p.task_count + " tasks" + (p.status === "pending_external" ? ", pending external" : "") + ")";
      if (p.pack_id === "validation_center_smoke") opt.selected = true;
      packSelect.appendChild(opt);
    });
    function refreshTasks() {
      const selected = Array.from(packSelect.selectedOptions).map((o) => o.value);
      taskSelect.innerHTML = "";
      lib.tasks
        .filter((t) => selected.includes(t.pack_id))
        .forEach((t) => {
          const opt = document.createElement("option");
          opt.value = t.task_id;
          opt.textContent = (t.active_by_default ? "★ " : "") + t.title;
          opt.selected = !!t.active_by_default;
          taskSelect.appendChild(opt);
        });
    }
    packSelect.addEventListener("change", refreshTasks);
    refreshTasks();
  }

  function renderHome() {
    const sessions = state.sessions;
    const ready = lib.packs.filter((p) => p.status === "available");
    const external = lib.packs.filter((p) => p.status === "pending_external");
    const fill = (id, items, labelFn) => {
      const ul = $(id);
      if (!ul) return;
      ul.innerHTML = "";
      if (!items.length) {
        const li = document.createElement("li");
        li.textContent = "None";
        ul.appendChild(li);
        return;
      }
      items.forEach((item) => {
        const li = document.createElement("li");
        li.textContent = labelFn(item);
        ul.appendChild(li);
      });
    };
    fill("#ready-list", ready, (p) => p.pack_id);
    fill("#progress-list", sessions.filter((s) => ["in_progress", "paused", "consent_pending"].includes(s.session_status)), (s) => s.session_code + " · " + s.participant_alias);
    fill("#submitted-list", sessions.filter((s) => s.session_status === "submitted"), (s) => s.session_code + " · awaiting review");
    fill("#needs-list", sessions.filter((s) => ["needs_clarification", "pending_submission"].includes(s.session_status)), (s) => s.session_code);
    fill("#reviewed-list", sessions.filter((s) => s.session_status === "reviewed"), (s) => s.session_code);
    fill("#external-list", external, (p) => p.pack_id);

    const ed = $("#edmund-list");
    if (ed) {
      ed.innerHTML = "";
      (lib.edmund.actions || []).forEach((a) => {
        const article = document.createElement("article");
        article.innerHTML =
          "<h4>" +
          escapeHtml(a.edmund_action_id + ". " + a.title) +
          "</h4><p><strong>Prerequisite:</strong> " +
          escapeHtml(a.prerequisite || "") +
          "</p><p><strong>Estimate:</strong> " +
          escapeHtml(a.estimated_time || "") +
          "</p><p><strong>Evidence:</strong> " +
          escapeHtml(a.exact_evidence || "") +
          "</p><p><strong>Unlocks:</strong> " +
          escapeHtml(a.gate_unlocked || "") +
          "</p><p><strong>Tasks:</strong> " +
          escapeHtml((a.task_ids || []).join(", ") || "(pending external / dependency)") +
          "</p>";
        ed.appendChild(article);
      });
    }
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function createSession(evt) {
    evt.preventDefault();
    const pack_ids = Array.from($("#pack-select").selectedOptions).map((o) => o.value);
    let task_ids = Array.from($("#task-select").selectedOptions).map((o) => o.value);
    if (!task_ids.length) {
      task_ids = lib.tasks.filter((t) => pack_ids.includes(t.pack_id) && t.active_by_default).map((t) => t.task_id);
    }
    const session = {
      session_id: "sess_" + Math.random().toString(16).slice(2, 10),
      session_code: Math.random().toString(36).slice(2, 8).toUpperCase(),
      access_token: crypto.getRandomValues(new Uint8Array(32)).reduce((a, b) => a + b.toString(16).padStart(2, "0"), ""),
      access_revoked: false,
      pack_ids,
      task_ids,
      participant_alias: $("#participant-alias").value.trim(),
      moderator: $("#moderator-name").value.trim(),
      device_sku: $("#sku-select").value,
      build_version: $("#build-version").value.trim(),
      lan_bind_opt_in: $("#lan-opt-in") ? $("#lan-opt-in").checked : false,
      evidence_eligibility: "PILOT_NON_GATING",
      is_rehearsal: false,
      session_title: pack_ids.join(" + "),
      expected_duration_minutes: task_ids.reduce((n, tid) => n + (taskById(tid)?.estimated_minutes || 0), 0),
      privacy_summary: "Your responses stay on this local Validation Center unless an operator exports them. You can stop at any time.",
      started_at: null,
      submitted_at: null,
      session_status: "consent_pending",
      consent_state: { accepted: false, declined: false, media_photo: false, media_audio: false, media_video: false, minors_mode: false },
      privacy_state: { store_local_only: true, cloud_upload_enabled: false, export_excludes_private: true },
      task_results: task_ids.map((tid) => ({
        task_id: tid,
        state: "not_started",
        step_completions: (taskById(tid)?.participant_steps || []).map(() => false),
        participant_rating: {},
        evidence_refs: [],
        issue_refs: [],
        reviewer_signoff: false,
        reviewer_state: "not_reviewed",
        reviewer_notes: "",
        moderator_observation: "",
      })),
      issues: [],
      evidence: [],
      final_comments: "",
      created_at: new Date().toISOString(),
    };
    state.sessions.push(session);
    state.currentSessionId = session.session_id;
    state.taskIndex = 0;
    saveState();
    $("#moderator-session").hidden = false;
    renderModerator();
    setMode("participant");
  }

  function renderModerator() {
    const s = currentSession();
    if (!s) return;
    $("#moderator-session").hidden = false;
    $("#mod-session-meta").textContent =
      "Code " + s.session_code + " · " + s.participant_alias + " · eligibility " + (s.evidence_eligibility || "PILOT_NON_GATING") + " · status " + s.session_status + (s.access_revoked ? " · LINK REVOKED" : "");
    const ul = $("#mod-task-list");
    ul.innerHTML = "";
    s.task_results.forEach((tr) => {
      const t = taskById(tr.task_id);
      const li = document.createElement("li");
      li.textContent = (t?.title || tr.task_id) + " — " + tr.state + (tr.skip_reason ? " (skip: " + tr.skip_reason + ")" : "");
      ul.appendChild(li);
    });
    const evHuman = s.evidence.filter((e) => e.source === "HUMAN_OBSERVED").length;
    const evSys = s.evidence.filter((e) => e.source === "SYSTEM_CAPTURED").length;
    $("#mod-evidence-status").textContent =
      "Evidence completeness: " + s.evidence.length + " items (HUMAN_OBSERVED " + evHuman + ", SYSTEM_CAPTURED " + evSys + ")";
  }

  function renderParticipant() {
    const s = currentSession();
    $("#consent-text").textContent = lib.consent_text;
    if (!s) {
      $("#consent-screen").hidden = false;
      $("#task-screen").hidden = true;
      $("#final-review").hidden = true;
      $("#consent-error").textContent = "No session yet. Create one in Moderator mode (same device works).";
      return;
    }
    const consented = !!s.consent_state.accepted;
    $("#consent-screen").hidden = consented;
    $("#task-screen").hidden = !consented || s.session_status === "submitted";
    $("#final-review").hidden = !(consented && state.taskIndex >= s.task_ids.length);
    if (!consented) return;
    if (state.taskIndex >= s.task_ids.length) {
      renderFinal(s);
      return;
    }
    const tid = s.task_ids[state.taskIndex];
    const t = taskById(tid);
    const tr = s.task_results.find((x) => x.task_id === tid);
    $("#task-progress").textContent = "Task " + (state.taskIndex + 1) + " of " + s.task_ids.length + " — " + (tr?.state || "not_started");
    $("#task-heading").textContent = t.title;
    $("#task-why").textContent = state.a11y.simpleLanguage ? t.short_description : "Why this matters: " + t.purpose;
    $("#task-prereq").textContent = "Prerequisites: " + (t.prerequisite_ids.join(", ") || "None");
    $("#task-estimate").textContent = "Estimated time: about " + t.estimated_minutes + " minutes";
    $("#task-safety").textContent = t.safety_notes.length ? "Safety: " + t.safety_notes.join(" · ") : "";
    $("#task-expected").textContent = t.expected_result;
    const ol = $("#task-steps");
    ol.innerHTML = "";
    t.participant_steps.forEach((step, idx) => {
      const li = document.createElement("li");
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.id = "step-" + idx;
      cb.checked = !!(tr.step_completions || [])[idx];
      cb.addEventListener("change", () => {
        tr.step_completions[idx] = cb.checked;
        saveState();
      });
      const label = document.createElement("label");
      label.htmlFor = cb.id;
      label.textContent = " " + step;
      li.appendChild(cb);
      li.appendChild(label);
      ol.appendChild(li);
    });
    $("#task-technical").textContent = JSON.stringify(
      { task_id: t.task_id, pack_id: t.pack_id, pass_rule: t.pass_rule, gate_unlocked: t.gate_unlocked, version: t.version },
      null,
      2
    );
    if (state.a11y.readAloud && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(t.title + ". " + t.short_description);
      window.speechSynthesis.speak(u);
    }
  }

  function renderFinal(s) {
    $("#task-screen").hidden = true;
    $("#final-review").hidden = false;
    const box = $("#final-summary");
    box.innerHTML = s.task_results
      .map((tr) => {
        const t = taskById(tr.task_id);
        const r = tr.participant_rating || {};
        return (
          "<p><strong>" +
          escapeHtml(t?.title || tr.task_id) +
          "</strong> — " +
          escapeHtml(tr.state) +
          "; completion " +
          escapeHtml(r.completion || tr.participant_completion || "") +
          "; evidence " +
          (tr.evidence_refs || []).length +
          "</p>"
        );
      })
      .join("");
  }

  function renderReviewer() {
    const awaiting = $("#awaiting-review-list");
    if (awaiting) {
      awaiting.innerHTML = "";
      state.sessions
        .filter((s) => ["submitted", "needs_clarification"].includes(s.session_status))
        .forEach((s) => {
          const li = document.createElement("li");
          const blocking = (s.issues || []).filter((i) => Number(i.severity) >= 3).length;
          li.textContent =
            (s.participant_alias || "?") +
            " · packs " +
            (s.pack_ids || []).join(",") +
            " · build " +
            (s.build_version || "?") +
            " · gating eligibility " +
            (s.evidence_eligibility || "PILOT_NON_GATING") +
            " · completion " +
            s.session_status +
            " · blocking issues " +
            blocking +
            " · evidence " +
            (s.evidence || []).length;
          awaiting.appendChild(li);
        });
      if (!awaiting.children.length) {
        const li = document.createElement("li");
        li.textContent = "None awaiting review";
        awaiting.appendChild(li);
      }
    }
    const body = $("#review-body");
    body.innerHTML = "";
    const completionFilter = ($("#rev-filter-completion").value || "").toLowerCase();
    const sevFilter = $("#rev-filter-severity").value;
    state.sessions
      .filter((s) => ["submitted", "reviewed", "needs_clarification"].includes(s.session_status))
      .forEach((s) => {
        s.task_results.forEach((tr) => {
          const r = tr.participant_rating || {};
          const completion = (r.completion || tr.participant_completion || "").toLowerCase();
          if (completionFilter && !completion.includes(completionFilter)) return;
          const issues = s.issues.filter((i) => i.task_id === tr.task_id);
          const maxSev = issues.reduce((m, i) => Math.max(m, Number(i.severity) || 0), 0);
          if (sevFilter && String(maxSev) !== String(sevFilter)) return;
          const trEl = document.createElement("tr");
          trEl.innerHTML =
            "<td>" +
            escapeHtml(s.session_code) +
            "</td><td>" +
            escapeHtml(s.participant_alias) +
            "</td><td>" +
            escapeHtml(s.device_sku) +
            "</td><td>" +
            escapeHtml(tr.task_id) +
            "</td><td>" +
            escapeHtml(r.completion || "") +
            "</td><td>" +
            escapeHtml(String(r.ease || "")) +
            "</td><td>" +
            escapeHtml(String(r.confidence || "")) +
            "</td><td>" +
            escapeHtml(String(r.satisfaction || "")) +
            "</td><td>" +
            escapeHtml(r.accessibility_impact || "") +
            "</td><td>" +
            escapeHtml(String(maxSev || "")) +
            "</td><td>" +
            escapeHtml(String((tr.evidence_refs || []).length)) +
            "</td><td class='status-text' data-status-text='" +
            escapeHtml(tr.reviewer_state || "not_reviewed") +
            "'>" +
            escapeHtml(tr.reviewer_state || "not_reviewed") +
            (tr.reviewer_signoff ? " · signed off" : "") +
            "</td><td></td>";
          const actions = trEl.lastChild;
          const sign = document.createElement("button");
          sign.type = "button";
          sign.textContent = "Sign off";
          sign.addEventListener("click", () => {
            tr.reviewer_signoff = true;
            tr.reviewer_state = "signed_off";
            tr.reviewer_notes = (tr.reviewer_notes || "") + " signed";
            if (s.task_results.every((x) => x.reviewer_signoff)) s.session_status = "reviewed";
            saveState();
            renderReviewer();
          });
          const clarify = document.createElement("button");
          clarify.type = "button";
          clarify.textContent = "Request clarification";
          clarify.addEventListener("click", () => {
            tr.reviewer_signoff = false;
            tr.reviewer_state = "clarification_requested";
            s.session_status = "needs_clarification";
            saveState();
            renderReviewer();
          });
          actions.appendChild(sign);
          actions.appendChild(clarify);
          body.appendChild(trEl);
        });
      });
  }

  function render() {
    applyA11y();
    renderHome();
    renderModerator();
    renderParticipant();
    renderReviewer();
  }

  // Events
  $$(".mode-btn").forEach((btn) => btn.addEventListener("click", () => setMode(btn.dataset.mode)));
  $("#open-a11y-options").addEventListener("click", () => {
    $("#a11y-options").hidden = false;
    $("#opt-text-size").focus();
  });
  $("#close-a11y-options").addEventListener("click", () => {
    $("#a11y-options").hidden = true;
    $("#open-a11y-options").focus();
  });
  ["opt-text-size", "opt-spacing", "opt-reduced-motion", "opt-high-contrast", "opt-simple-language", "opt-read-aloud"].forEach((id) => {
    $("#" + id).addEventListener("change", () => {
      state.a11y.textSize = $("#opt-text-size").value;
      state.a11y.spacing = $("#opt-spacing").value;
      state.a11y.reducedMotion = $("#opt-reduced-motion").checked;
      state.a11y.highContrast = $("#opt-high-contrast").checked;
      state.a11y.simpleLanguage = $("#opt-simple-language").checked;
      state.a11y.readAloud = $("#opt-read-aloud").checked;
      saveState();
      applyA11y();
      renderParticipant();
    });
  });

  if ($("#create-session-form")) $("#create-session-form").addEventListener("submit", createSession);

  $("#consent-accept").addEventListener("click", () => {
    const s = currentSession();
    if (!s) return;
    if (!$("#consent-purpose").checked) {
      $("#consent-error").textContent = "Please confirm you understand the purpose.";
      return;
    }
    s.consent_state = {
      accepted: true,
      declined: false,
      purpose_acknowledged: true,
      media_photo: $("#consent-photo").checked,
      media_audio: $("#consent-audio").checked,
      media_video: $("#consent-video").checked,
      minors_mode: false,
      plain_language_shown: true,
      recorded_at: new Date().toISOString(),
    };
    s.session_status = "in_progress";
    s.started_at = s.started_at || new Date().toISOString();
    saveState();
    renderParticipant();
  });

  $("#consent-decline").addEventListener("click", () => {
    const s = currentSession();
    if (!s) return;
    s.consent_state = { accepted: false, declined: true, media_photo: false, media_audio: false, media_video: false, minors_mode: false };
    s.session_status = "revoked";
    saveState();
    $("#consent-error").textContent = "Consent declined. Session will not collect evidence.";
    renderParticipant();
  });

  $("#task-start").addEventListener("click", () => {
    const s = currentSession();
    if (!s) return;
    const tr = s.task_results[state.taskIndex];
    tr.state = "in_progress";
    tr.started_at = tr.started_at || new Date().toISOString();
    saveState();
    renderParticipant();
  });
  $("#task-pause").addEventListener("click", () => {
    const s = currentSession();
    if (!s) return;
    s.task_results[state.taskIndex].state = "paused";
    s.session_status = "paused";
    saveState();
    renderParticipant();
  });
  $("#task-add-note").addEventListener("click", () => {
    const s = currentSession();
    if (!s) return;
    const note = window.prompt("Add a text note");
    if (!note) return;
    const tr = s.task_results[state.taskIndex];
    const ev = {
      evidence_id: "ev_" + Math.random().toString(16).slice(2, 8),
      file_name: "note.txt",
      mime: "text/plain",
      sha256: "pending-client-hash",
      timestamp: new Date().toISOString(),
      source: "HUMAN_OBSERVED",
      task_id: tr.task_id,
      privacy_classification: "internal",
      attribution: "participant",
      text: note,
    };
    // SHA-256 when SubtleCrypto available
    if (window.crypto?.subtle) {
      const enc = new TextEncoder().encode(note);
      crypto.subtle.digest("SHA-256", enc).then((buf) => {
        ev.sha256 = Array.from(new Uint8Array(buf))
          .map((b) => b.toString(16).padStart(2, "0"))
          .join("");
        s.evidence.push(ev);
        tr.evidence_refs.push(ev.evidence_id);
        saveState();
        renderModerator();
      });
    } else {
      s.evidence.push(ev);
      tr.evidence_refs.push(ev.evidence_id);
      saveState();
    }
  });
  $("#task-add-evidence").addEventListener("click", () => {
    const s = currentSession();
    if (!s) return;
    const input = document.createElement("input");
    input.type = "file";
    input.addEventListener("change", async () => {
      const file = input.files?.[0];
      if (!file) return;
      const consent = s.consent_state || {};
      if (file.type.startsWith("image/") && !consent.media_photo) {
        alert("Photo consent required.");
        return;
      }
      if (file.type.startsWith("audio/") && !consent.media_audio) {
        alert("Audio consent required.");
        return;
      }
      if (file.type.startsWith("video/") && !consent.media_video) {
        alert("Video consent required.");
        return;
      }
      const buf = await file.arrayBuffer();
      const hashBuf = await crypto.subtle.digest("SHA-256", buf);
      const sha = Array.from(new Uint8Array(hashBuf))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");
      const tr = s.task_results[state.taskIndex];
      const ev = {
        evidence_id: "ev_" + Math.random().toString(16).slice(2, 8),
        file_name: file.name,
        mime: file.type || "application/octet-stream",
        sha256: sha,
        timestamp: new Date().toISOString(),
        source: "HUMAN_OBSERVED",
        task_id: tr.task_id,
        privacy_classification: "internal",
        attribution: "participant",
      };
      s.evidence.push(ev);
      tr.evidence_refs.push(ev.evidence_id);
      saveState();
      alert("Evidence attached with SHA256 " + sha.slice(0, 12) + "…");
    });
    input.click();
  });
  $("#task-report-issue").addEventListener("click", () => {
    const s = currentSession();
    if (!s) return;
    const description = window.prompt("Describe the issue");
    if (!description) return;
    const severity = Number(window.prompt("Severity 1-4", "2") || "2");
    const tr = s.task_results[state.taskIndex];
    const issue = {
      issue_id: "iss_" + Math.random().toString(16).slice(2, 8),
      task_id: tr.task_id,
      severity,
      category: "other",
      description,
      status: "open",
    };
    s.issues.push(issue);
    tr.issue_refs.push(issue.issue_id);
    saveState();
  });
  $("#task-complete").addEventListener("click", () => {
    const s = currentSession();
    if (!s) return;
    s.task_results[state.taskIndex].state = "completed";
    s.task_results[state.taskIndex].completed_at = new Date().toISOString();
    saveState();
    renderParticipant();
  });

  function readRating() {
    const completion = (document.querySelector('input[name="completion"]:checked') || {}).value || "";
    const prefer = !!( $("#prefer-not-to-answer") && $("#prefer-not-to-answer").checked );
    return {
      completion,
      ease: prefer ? null : Number($("#rating-ease").value),
      confidence: prefer ? null : Number($("#rating-confidence").value),
      satisfaction: prefer ? null : Number($("#rating-satisfaction").value),
      accessibility_impact: $("#rating-a11y").value,
      physical_comfort: $("#rating-comfort").value || null,
      prefer_not_to_answer: prefer,
      comment: document.querySelector('textarea[name="comment"]').value,
      what_was_confusing: document.querySelector('textarea[name="what_was_confusing"]').value,
      what_would_make_easier: document.querySelector('textarea[name="what_would_make_easier"]').value,
    };
  }

  $("#submit-task").addEventListener("click", () => {
    const s = currentSession();
    if (!s) return;
    const rating = readRating();
    if (!rating.completion) {
      alert("Select a completion rating.");
      return;
    }
    const tr = s.task_results[state.taskIndex];
    tr.participant_rating = rating;
    tr.participant_completion = rating.completion;
    tr.state = tr.state === "skipped" ? "skipped" : "completed";
    tr.completed_at = new Date().toISOString();
    saveState();
    alert("Task submitted (local). Ratings are evidence, not automatic PASS.");
  });

  $("#next-task").addEventListener("click", () => {
    state.taskIndex += 1;
    saveState();
    renderParticipant();
  });

  $("#submit-session").addEventListener("click", () => {
    const s = currentSession();
    if (!s) return;
    if (s._submit_lock) {
      $("#submit-status").textContent = "Duplicate submit prevented.";
      return;
    }
    const incomplete = s.task_results.filter((tr) => !["completed", "skipped"].includes(tr.state));
    if (incomplete.length) {
      $("#submit-status").textContent = "Incomplete tasks: " + incomplete.map((t) => t.task_id).join(", ");
      s.session_status = "pending_submission";
      saveState();
      return;
    }
    s._submit_lock = true;
    s.final_comments = $("#final-comments").value;
    s.submitted_at = new Date().toISOString();
    s.session_status = "submitted";
    s.submission_version = (s.submission_version || 0) + 1;
    s.latest_submission_hash = "local-" + s.session_id + "-v" + s.submission_version;
    saveState();
    $("#submit-status").textContent = "Session submitted (immutable local snapshot v" + s.submission_version + "). Awaiting reviewer signoff.";
    render();
  });

  $("#mod-pause").addEventListener("click", () => {
    const s = currentSession();
    if (!s) return;
    s.session_status = "paused";
    saveState();
    renderModerator();
  });
  $("#mod-resume").addEventListener("click", () => {
    const s = currentSession();
    if (!s) return;
    s.session_status = "in_progress";
    saveState();
    renderModerator();
  });
  $("#mod-skip").addEventListener("click", () => {
    const s = currentSession();
    if (!s) return;
    const reason = window.prompt("Skip reason");
    if (!reason) return;
    const tr = s.task_results[state.taskIndex] || s.task_results[0];
    if (!tr) return;
    tr.state = "skipped";
    tr.skip_reason = reason;
    tr.participant_completion = "not_attempted_skipped";
    saveState();
    renderModerator();
  });
  $("#mod-revoke").addEventListener("click", () => {
    const s = currentSession();
    if (!s) return;
    s.access_revoked = true;
    s.access_token = crypto.getRandomValues(new Uint8Array(32)).reduce((a, b) => a + b.toString(16).padStart(2, "0"), "");
    saveState();
    renderModerator();
  });

  $("#rev-filter-completion").addEventListener("input", () => renderReviewer());
  $("#rev-filter-severity").addEventListener("input", () => renderReviewer());


  // --- CX4.2 pilot readiness UI ---
  let wizardStep = 1;
  function showWizardStep(n) {
    wizardStep = n;
    const label = $("#wizard-step-label");
    if (label) label.textContent = "Wizard step " + n + " of 6";
    $$(".wizard-pane").forEach((pane) => {
      pane.hidden = Number(pane.dataset.step) !== n;
    });
    if (n === 5) {
      const tids = Array.from(($("#task-select") || { selectedOptions: [] }).selectedOptions).map((o) => o.value);
      const mins = tids.reduce((sum, tid) => sum + (taskById(tid)?.estimated_minutes || 0), 0);
      const dur = $("#wizard-duration");
      if (dur) dur.textContent = "Expected duration: about " + mins + " minutes";
    }
  }
  if ($("#wizard-next")) {
    $("#wizard-next").addEventListener("click", () => showWizardStep(Math.min(6, wizardStep + 1)));
    $("#wizard-back").addEventListener("click", () => showWizardStep(Math.max(1, wizardStep - 1)));
    showWizardStep(1);
  }
  if ($("#wizard-launch")) {
    $("#wizard-launch").addEventListener("click", (evt) => {
      createSession(evt);
      const s = currentSession();
      if (!s) return;
      $("#launch-result").hidden = false;
      $("#launch-code").textContent = s.session_code;
      $("#launch-url").textContent = location.origin + location.pathname + "#entry?code=" + encodeURIComponent(s.session_code);
      $("#moderator-session").hidden = false;
      setMode("moderator");
    });
  }
  if ($("#participant-entry")) {
    $("#participant-entry").addEventListener("submit", (evt) => {
      evt.preventDefault();
      const code = ($("#session-code-entry").value || "").trim().toUpperCase();
      const token = ($("#session-token-entry").value || "").trim();
      const err = $("#entry-error");
      const match = state.sessions.find((s) => (s.session_code || "").toUpperCase() === code);
      if (!match || match.access_revoked) {
        err.textContent = "Could not join session. Check the code with your moderator.";
        return;
      }
      if (token && match.access_token && token !== match.access_token) {
        err.textContent = "Could not join session. Check the code with your moderator.";
        return;
      }
      // Do not expose internal branch / gate tokens
      $("#entry-session-meta").hidden = false;
      $("#entry-session-title").textContent = match.session_title || "Validation session";
      $("#entry-duration").textContent = "Expected duration: about " + (match.expected_duration_minutes || "—") + " minutes";
      $("#entry-privacy").textContent = match.privacy_summary || "privacy summary";
      if (!$("#entry-consent-ack").checked) {
        err.textContent = "Please confirm the privacy summary before starting.";
        return;
      }
      if ($("#entry-a11y-large")?.checked) { state.a11y.textSize = "150"; $("#opt-text-size").value = "150"; }
      if ($("#entry-a11y-contrast")?.checked) { state.a11y.highContrast = true; $("#opt-high-contrast").checked = true; }
      if ($("#entry-a11y-simple")?.checked) { state.a11y.simpleLanguage = true; $("#opt-simple-language").checked = true; }
      if ($("#entry-a11y-motion")?.checked) { state.a11y.reducedMotion = true; $("#opt-reduced-motion").checked = true; }
      applyA11y();
      state.currentSessionId = match.session_id;
      saveState();
      setMode("participant");
    });
  }
  if ($("#scan-qr-btn")) {
    $("#scan-qr-btn").addEventListener("click", () => {
      const st = $("#qr-status");
      if (!window.isSecureContext || !navigator.mediaDevices) {
        st.textContent = "Camera QR scan is not available here. Enter the session code instead.";
        return;
      }
      st.textContent = "QR camera support detected; enter code manually if scan UI is unavailable in this build.";
    });
  }

  function attachEvidence(kind) {
    const s = currentSession();
    if (!s) return;
    const consent = s.consent_state || {};
    const consentEl = $("#evidence-consent-state");
    if (consentEl) {
      consentEl.textContent =
        "Consent — photos: " + !!consent.media_photo + ", audio: " + !!consent.media_audio + ", video: " + !!consent.media_video;
    }
    const tr = s.task_results[state.taskIndex];
    if (!tr) return;
    const needsMedia = ["screenshot", "photo", "video", "audio"].includes(kind);
    if (needsMedia) {
      const ok =
        (kind === "screenshot" || kind === "photo") ? consent.media_photo :
        kind === "audio" ? consent.media_audio :
        kind === "video" ? consent.media_video : true;
      if (!ok) {
        alert("Media consent is required before attaching this evidence. You can still add a note or file if allowed.");
        return;
      }
    }
    const input = $("#ev-file-input");
    const finish = (name, note) => {
      const item = {
        evidence_id: "ev_" + Math.random().toString(16).slice(2, 10),
        file_name: name,
        mime: kind === "note" ? "text/plain" : "application/octet-stream",
        sha256: "pending-local-" + Date.now().toString(16),
        timestamp: new Date().toISOString(),
        source: "HUMAN_OBSERVED",
        task_id: tr.task_id,
        privacy_classification: "internal",
        attribution: "participant",
        notes: note || kind,
        preview: name,
      };
      s.evidence.push(item);
      tr.evidence_refs.push(item.evidence_id);
      const list = $("#ev-preview-list");
      if (list) {
        const li = document.createElement("li");
        li.textContent = name + " (" + kind + ") — remove before submission if needed";
        const rm = document.createElement("button");
        rm.type = "button";
        rm.textContent = "Remove";
        rm.addEventListener("click", () => {
          s.evidence = s.evidence.filter((e) => e.evidence_id !== item.evidence_id);
          tr.evidence_refs = tr.evidence_refs.filter((id) => id !== item.evidence_id);
          li.remove();
          saveState();
        });
        li.appendChild(rm);
        list.appendChild(li);
      }
      saveState();
    };
    if (kind === "note") {
      const note = window.prompt("Add note");
      if (note) finish("note.txt", note);
      return;
    }
    if (input) {
      input.onchange = () => {
        const f = input.files && input.files[0];
        if (f) finish(f.name, "uploaded-" + kind);
        input.value = "";
      };
      input.click();
    } else {
      finish(kind + ".bin", "fallback-upload");
    }
  }
  [
    ["ev-screenshot", "screenshot"],
    ["ev-photo", "photo"],
    ["ev-video", "video"],
    ["ev-audio", "audio"],
    ["ev-file", "file"],
    ["ev-note", "note"],
  ].forEach(([id, kind]) => {
    const el = $("#" + id);
    if (el) el.addEventListener("click", () => attachEvidence(kind));
  });
  if ($("#task-need-help")) {
    $("#task-need-help").addEventListener("click", () => alert("Help requested. A moderator can assist. You may pause or stop at any time."));
  }
  if ($("#task-stop-session")) {
    $("#task-stop-session").addEventListener("click", () => {
      const s = currentSession();
      if (!s) return;
      if (!window.confirm("Stop this session? Your progress is autosaved.")) return;
      s.session_status = "paused";
      saveState();
      alert("Session stopped/paused. You can resume later with your moderator.");
    });
  }


  // hydrate a11y controls
  $("#opt-text-size").value = state.a11y.textSize || "100";
  $("#opt-spacing").value = state.a11y.spacing || "normal";
  $("#opt-reduced-motion").checked = !!state.a11y.reducedMotion;
  $("#opt-high-contrast").checked = !!state.a11y.highContrast;
  $("#opt-simple-language").checked = !!state.a11y.simpleLanguage;
  $("#opt-read-aloud").checked = !!state.a11y.readAloud;

  fillPackSelectors();
  setMode(state.mode || "home");
  setAutosave(state.autosaveStatus || "recovered");
})();
