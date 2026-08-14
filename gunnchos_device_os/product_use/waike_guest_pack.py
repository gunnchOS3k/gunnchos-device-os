"""Build self-contained in-guest WAIKE HTML packs from signed owner ingest.

Does not re-author curriculum — projects accepted #43+#44 six-course
learner/teacher ingest into static pages the Interactive Guest Chromium can
open. Catalog course_ids stay owner-exact.

Reads the on-disk waike_store (already signed at ingest time). Does not import
cryptography / re-verify signatures at pack-build time so journey runners can
run without the signing toolchain present.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STORE_REL = Path("artifacts/product_use/waike_store")
LEARNER_FORBIDDEN_KEYS = frozenset(
    {
        "answer_index",
        "answer_keys",
        "instructor_keys",
        "solution_key",
        "explanation",
        "correct",
        "instructor_notes",
        "rubrics",
    }
)


def _strip(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items() if k not in LEARNER_FORBIDDEN_KEYS}
    if isinstance(obj, list):
        return [_strip(x) for x in obj]
    return obj


def _load_active_ingest(repo_root: Path) -> tuple[str, dict[str, Any], dict[str, Any]]:
    store = Path(repo_root).resolve() / STORE_REL
    index = json.loads((store / "INDEX.json").read_text(encoding="utf-8"))
    version = index.get("active_version")
    if not version:
        raise RuntimeError("waike_store_no_active_version")
    dest = store / "versions" / version
    learner = json.loads((dest / "learner_ingest.json").read_text(encoding="utf-8"))
    teacher = json.loads((dest / "teacher_ingest.json").read_text(encoding="utf-8"))
    return version, learner, teacher


def build_course_slice(repo_root: Path, course_id: str = "GENERAL_IT") -> dict[str, Any]:
    version, learner_doc, teacher_doc = _load_active_ingest(repo_root)
    l_courses = {c["course_id"]: c for c in (learner_doc.get("courses") or [])}
    t_courses = {c["course_id"]: c for c in (teacher_doc.get("courses") or [])}
    if course_id not in l_courses or course_id not in t_courses:
        raise RuntimeError(f"course_missing:{course_id}")
    lc = _strip(l_courses[course_id])
    tc = t_courses[course_id]
    week = (lc.get("weeks") or [{}])[0]
    quiz = (lc.get("quizzes") or [{}])[0]
    t_keys = ((tc.get("answer_keys") or {}).get("quizzes") or {})
    quiz_id = quiz.get("quiz_id")
    answer_map = t_keys.get(quiz_id) or t_keys
    return {
        "package_version": version,
        "course_id": course_id,
        "title": lc.get("title"),
        "lesson_id": week.get("lesson_id") or f"{course_id}-w01",
        "lesson_title": week.get("title") or "Week 1",
        "lesson_body": week.get("body_md") or lc.get("lesson_excerpt") or "",
        "worked_example": week.get("worked_example") or lc.get("worked_example") or "",
        "assignment": (lc.get("assignments") or [{"prompt": lc.get("assignment")}])[0],
        "quiz": quiz,
        "teacher_answer_keys_for_quiz": answer_map,
    }


LEARNER_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<title>WAIKE Learner — __COURSE__</title>
<style>
body{font-family:system-ui,sans-serif;max-width:820px;margin:24px auto;padding:0 16px;background:#f7f4ef;color:#1a1a1a}
h1{font-size:1.6rem} .card{background:#fff;border:1px solid #ddd;padding:16px;margin:12px 0}
button{font-size:1.1rem;padding:10px 16px;margin:4px} .ok{color:#0a7} .bad{color:#a00}
#status{font-weight:600}
</style></head><body>
<h1>WAIKE Learner</h1>
<p id="meta"></p>
<div class="card"><h2 id="lesson-title"></h2><article id="lesson"></article></div>
<div class="card"><h3>Worked example</h3><div id="example"></div></div>
<div class="card"><h3>Assignment</h3><div id="assignment"></div>
<button id="save-assignment">Save assignment draft</button></div>
<div class="card"><h3>Quiz</h3><div id="quiz"></div>
<button id="submit-quiz">Submit quiz answer</button></div>
<p id="status">ready</p>
<script>
const DATA = __DATA__;
const STATE_URL = '/state';
document.getElementById('meta').textContent = DATA.course_id + ' · ' + DATA.package_version + ' · learner (no keys)';
document.getElementById('lesson-title').textContent = DATA.lesson_title;
document.getElementById('lesson').textContent = DATA.lesson_body.slice(0, 2500);
document.getElementById('example').textContent = DATA.worked_example.slice(0, 1200);
document.getElementById('assignment').textContent = (DATA.assignment.prompt || DATA.assignment || '').toString().slice(0, 800);
const quiz = DATA.quiz || {items:[]};
const item = (quiz.items || [])[0] || {stem:'(no item)', choices:['A']};
let chosen = 0;
const q = document.getElementById('quiz');
q.innerHTML = '<p>' + item.stem + '</p>' + (item.choices||[]).map((c,i)=>
  '<label><input type="radio" name="c" value="'+i+'"'+(i===0?' checked':'')+'> '+c+'</label><br/>'
).join('');
q.addEventListener('change', e => { if(e.target.name==='c') chosen = Number(e.target.value); });
async function post(kind, extra){
  const body = Object.assign({kind, course_id: DATA.course_id, lesson_id: DATA.lesson_id, ts: Date.now()}, extra||{});
  await fetch(STATE_URL, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  document.getElementById('status').textContent = kind + ' saved';
}
document.getElementById('save-assignment').onclick = () => post('assignment_draft', {text: 'draft-for-' + DATA.lesson_id});
document.getElementById('submit-quiz').onclick = () => post('quiz_submit', {quiz_id: quiz.quiz_id, item_id: item.id, choice_index: chosen});
</script></body></html>
"""

TEACHER_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<title>WAIKE Teacher — __COURSE__</title>
<style>
body{font-family:system-ui,sans-serif;max-width:820px;margin:24px auto;padding:0 16px;background:#eef2f7;color:#111}
.card{background:#fff;border:1px solid #ccd;padding:16px;margin:12px 0}
button{font-size:1.1rem;padding:10px 16px;margin:4px} #keys{font-family:monospace;white-space:pre-wrap;background:#111;color:#cfc;padding:8px}
</style></head><body>
<h1>WAIKE Teacher (instructor-only keys)</h1>
<p id="meta"></p>
<div class="card"><h3>Syllabus / lesson</h3><div id="lesson"></div></div>
<div class="card"><h3>Assign fixture cohort</h3>
<button id="assign">Assign quiz fixture to cohort-A</button></div>
<div class="card"><h3>Grade fixture</h3>
<button id="grade">Grade learner fixture submission</button>
<button id="load-keys">Load keys (teacher role)</button>
<pre id="keys">(keys not embedded — require X-WAIKE-Role: teacher via /teacher/keys)</pre></div>
<p id="status">ready</p>
<script>
const DATA = __DATA__;
const ROLE_HEADERS = {'X-WAIKE-Role':'teacher', 'Content-Type':'application/json'};
document.getElementById('meta').textContent = DATA.course_id + ' · teacher view (keys not in HTML)';
document.getElementById('lesson').textContent = (DATA.lesson_body||'').slice(0,1200);
let cachedKeys = null;
async function loadKeys(){
  const r = await fetch('/teacher/keys', {headers:{'X-WAIKE-Role':'teacher'}});
  if(!r.ok){ document.getElementById('keys').textContent = 'forbidden '+r.status; return null; }
  cachedKeys = await r.json();
  document.getElementById('keys').textContent = JSON.stringify(cachedKeys, null, 2);
  return cachedKeys;
}
async function post(kind, extra){
  const body = Object.assign({kind, role:'teacher', course_id: DATA.course_id, ts: Date.now()}, extra||{});
  await fetch('/teacher', {method:'POST', headers: ROLE_HEADERS, body: JSON.stringify(body)});
  document.getElementById('status').textContent = kind + ' ok';
}
document.getElementById('load-keys').onclick = () => loadKeys();
document.getElementById('assign').onclick = () => post('assign_fixture', {cohort:'cohort-A', quiz_id: (DATA.quiz||{}).quiz_id});
document.getElementById('grade').onclick = async () => {
  const keys = cachedKeys || await loadKeys() || {};
  post('grade_fixture', { learner_choice: 0, rubric: 'fixture-rubric-v1', keys_ref: 'teacher/keys' });
};
</script></body></html>
"""


def write_guest_pack(repo_root: Path, out_dir: Path, course_id: str = "GENERAL_IT") -> dict[str, Any]:
    slice_ = build_course_slice(repo_root, course_id=course_id)
    _version, learner_doc, _teacher_doc = _load_active_ingest(repo_root)
    catalog_ids = [c.get("course_id") for c in (learner_doc.get("courses") or [])]
    out_dir.mkdir(parents=True, exist_ok=True)
    learner_dir = out_dir / "learner"
    teacher_dir = out_dir / "teacher"
    learner_dir.mkdir(parents=True, exist_ok=True)
    teacher_dir.mkdir(parents=True, exist_ok=True)
    learner_data = {
        k: v
        for k, v in slice_.items()
        if k != "teacher_answer_keys_for_quiz"
    }
    teacher_data = dict(slice_)
    # Teacher HTML must NOT embed answer keys — keys served only via ACL'd /teacher/keys.
    teacher_page_data = {
        k: v for k, v in slice_.items() if k != "teacher_answer_keys_for_quiz"
    }
    blob = json.dumps(learner_data)
    for k in LEARNER_FORBIDDEN_KEYS:
        if k in blob:
            raise RuntimeError(f"learner_pack_key_leak:{k}")

    learner_html = (
        LEARNER_HTML.replace("__COURSE__", course_id).replace(
            "__DATA__", json.dumps(learner_data, ensure_ascii=False)
        )
    )
    teacher_html = (
        TEACHER_HTML.replace("__COURSE__", course_id).replace(
            "__DATA__", json.dumps(teacher_page_data, ensure_ascii=False)
        )
    )
    if "teacher_answer_keys_for_quiz" in teacher_html or '"answer_keys"' in teacher_html:
        raise RuntimeError("teacher_html_must_not_embed_answer_keys")
    (learner_dir / "learner.html").write_text(learner_html, encoding="utf-8")
    (learner_dir / "learner_data.json").write_text(
        json.dumps(learner_data, indent=2) + "\n", encoding="utf-8"
    )
    (learner_dir / "MANIFEST.json").write_text(
        json.dumps(
            {
                "schema": "gunnchos.product_use.waike_guest_pack.v1",
                "role": "learner",
                "course_id": course_id,
                "package_version": slice_["package_version"],
                "reauthored": False,
                "owner": "waike-research-ops#43+#44",
                "catalog_course_ids": catalog_ids,
                "learner_has_answer_keys": False,
                "keys_co_located": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (teacher_dir / "teacher.html").write_text(teacher_html, encoding="utf-8")
    (teacher_dir / "teacher_data.json").write_text(
        json.dumps(teacher_data, indent=2) + "\n", encoding="utf-8"
    )
    # Flat compatibility copies for deploy (deploy still separates on guest FS).
    (out_dir / "learner.html").write_text(learner_html, encoding="utf-8")
    (out_dir / "learner_data.json").write_text(
        json.dumps(learner_data, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "teacher.html").write_text(teacher_html, encoding="utf-8")
    (out_dir / "teacher_data.json").write_text(
        json.dumps(teacher_data, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "MANIFEST.json").write_text(
        json.dumps(
            {
                "schema": "gunnchos.product_use.waike_guest_pack.v1",
                "course_id": course_id,
                "package_version": slice_["package_version"],
                "reauthored": False,
                "owner": "waike-research-ops#43+#44",
                "catalog_course_ids": catalog_ids,
                "stale_three_course_pack": False,
                "learner_has_answer_keys": False,
                "host_layout": "learner/ + teacher/ separated; flat copies for deploy helper",
                "guest_layout": {
                    "learner": "/var/lib/gunnchos/waike",
                    "teacher": "/var/lib/gunnchos/waike-teacher (0700/0600)",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "ok": True,
        "out_dir": str(out_dir),
        "course_id": course_id,
        "package_version": slice_["package_version"],
        "catalog_course_ids": catalog_ids,
        "learner_has_answer_keys": False,
        "host_separated": True,
    }
