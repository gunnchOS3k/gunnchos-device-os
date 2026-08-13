"""Per-course seed prose. Intentionally non-isomorphic so the auditor can catch templates."""

from __future__ import annotations

from typing import Any

from gunnchos_device_os.waike_curriculum.catalog import COURSE_IDS, course_by_id

# Forbidden owner-template fingerprints (must not appear in product seeds).
FORBIDDEN_PHRASES = (
    "like learning to cook",
    "week 1: intuition + vocabulary + safety/privacy",
    "lab a: guided tutorial with gunnchai3k",
    "see `00_program_index.md` and flagship courses",
    "apprenticeship track outline",
)


def _seed(course_id: str, **fields: Any) -> dict[str, Any]:
    spec = course_by_id(course_id)
    fields["course_id"] = course_id
    fields["title"] = spec.title
    return fields


SEEDS: dict[str, dict[str, Any]] = {
    "DIGITAL_CONFIDENCE": _seed(
        "DIGITAL_CONFIDENCE",
        lesson=(
            "Operator confidence is not 'being good with computers.' It is knowing which of "
            "three jobs you asked the machine to do: remember (files), calculate (apps), or "
            "talk (network). Beginners freeze when a window disappears because they cannot "
            "name the job that failed.\n\n"
            "Today you will build a folder tree by hand: Documents/waike/lab1 plus a Downloads "
            "inbox. You will copy a note into lab1, then recover it after a 'delete' drill. "
            "Mouse-only habits hide the path; keyboard and path names survive when the GUI "
            "theme changes on a shared lab PC in Gary.\n\n"
            "Safety: never store passwords in the note. If a USB stick appears, treat it as "
            "untrusted until an instructor says otherwise. Offline pack: this lesson runs with "
            "no internet — the tree lives on disk."
        ),
        assignment=(
            "1) Create the required tree and screenshot or list it (`ls` / File Explorer).\n"
            "2) Write a 4-line operator journal: remember / calculate / talk / what broke.\n"
            "3) Restore the deleted note without using Undo as your only method."
        ),
        student_packet=(
            "You are practicing computer-operator basics, not programming. Bring nothing "
            "except curiosity and a USB-free workspace. Complete the folder drill, then the "
            "lab check. If you get lost, say the path out loud before clicking."
        ),
        instructor_packet=(
            "Watch for students who only use the desktop. Require a path listing. Do not "
            "accept a cloud screenshot as offline evidence. Common failure: creating "
            "Documents/Waike with a capital W — the lab is case-sensitive."
        ),
        slides=(
            "Slide 1: Remember / calculate / talk.\n"
            "Slide 2: Path vs icon.\n"
            "Slide 3: Delete-and-recover drill.\n"
            "Slide 4: USB distrust.\n"
            "No pixel deck ships in this seed — outline only."
        ),
        group_project=(
            "Pairs: one student is the 'lost user,' the other is the operator. The user "
            "hides a file; the operator recovers it and writes the path on paper."
        ),
        assessment=[
            {"id": "dc1", "q": "Name the three operator jobs.", "a": "remember, calculate, talk"},
            {"id": "dc2", "q": "Why is a path listing better than a themed screenshot?", "a": "paths survive GUI changes"},
            {"id": "dc3", "kind": "lab", "q": "Lab reports missing Documents/waike/lab1", "a": "missing includes that path"},
        ],
        portfolio="operator_journal.md + folder listing + lab result JSON",
        tutor_prompt="Ask the learner to say the full path before they click anything.",
        tutor_reply=(
            "Say the path out loud: Documents/waike/lab1. If that folder is missing, create "
            "it before copying. The lab marks missing paths — extras on the Desktop are clutter, not success."
        ),
    ),
    "IT_SUPPORT_HARDWARE": _seed(
        "IT_SUPPORT_HARDWARE",
        lesson=(
            "A ticket is a promise to restore someone's work, not a chat thread. Hardware "
            "foundations start at power, then storage, then memory, then the OS. Swapping "
            "parts before naming the subsystem is how labs waste DIMMs.\n\n"
            "Symptoms map poorly to parts if you skip questions: did it slow at boot, crash "
            "one app, or scream from the fan? Low RAM plus app crash points at memory. "
            "Slow boot plus almost-full disk points at storage. High CPU plus fan noise "
            "points at cooling — still not a new motherboard.\n\n"
            "Collect logs before you unscrew anything. This seed uses a virtual ticket; no "
            "live chassis. Kinesthetic add-on (classroom): point at the RAM slots on a donor "
            "board while the lab classifies the ticket."
        ),
        assignment=(
            "Triage three tickets (boot / crash / fan). For each: subsystem, whether to swap "
            "now, and one log you would collect. No vendor names required."
        ),
        student_packet=(
            "You are a first-week IT apprentice. Do not claim CompTIA credit from this seed. "
            "Work the fixture ticket in the lab, then write your own ticket in plain English."
        ),
        instructor_packet=(
            "Fail any answer that jumps to 'reinstall Windows' without a subsystem. RAM vs "
            "disk confusion is the teachable moment. No live high-voltage work."
        ),
        slides="Power → storage → memory → OS. Ticket fields. Swap vs log. Safety: unplug first.",
        group_project="Trio: reporter, tech, verifier. Verifier may only ask two questions.",
        assessment=[
            {"id": "it1", "q": "App crash + 4 GB RAM: first subsystem?", "a": "memory"},
            {"id": "it2", "q": "Why collect logs before a swap?", "a": "evidence disappears after the change"},
        ],
        portfolio="ticket_writeup.md + lab next_action",
        tutor_prompt="What failed first: power, disk, RAM, or cooling?",
        tutor_reply="If apps crash on a 4 GB machine, add or reseat RAM before you blame the OS.",
    ),
    "SOFTWARE_BUILDER": _seed(
        "SOFTWARE_BUILDER",
        lesson=(
            "Shipping is smaller than 'becoming a developer.' A stranger must run what you "
            "wrote. That means a function with checks, a README with one command, and no "
            "secrets in the repo.\n\n"
            "This seed grades numeric scores into bands: H (≥90), M (≥75), L (≥50), R (retry). "
            "The bands are arbitrary on purpose — you will change thresholds later. What you "
            "must not skip: run the checks. A function that 'looks right' is not a lab pass.\n\n"
            "Kinesthetic: write the band table on paper, then type it. If paper and code "
            "disagree, the paper wins until you find the bug."
        ),
        assignment=(
            "Implement band() for the four thresholds. Add one extra failing score. Document "
            "the run command in README. Do not copy a cooking analogy."
        ),
        student_packet="Bring a text editor. You will run a checker. Retry (R) is a valid grade, not shame.",
        instructor_packet=(
            "Look for hard-coded expected lists instead of thresholds. Accept any language "
            "if they also pass the Python lab fixture."
        ),
        slides="Function → checks → README. Bands H/M/L/R. Secrets stay out.",
        group_project="Pair-program the README only; the function owner cannot type the README.",
        assessment=[
            {"id": "sw1", "q": "Score 49 maps to which band?", "a": "R"},
            {"id": "sw2", "q": "What makes a stranger able to run it?", "a": "README with one command + checks"},
        ],
        portfolio="band function + README + lab JSON",
        tutor_prompt="Did the checks run, or did you only read the code?",
        tutor_reply="49 is Retry. 50 is L. Off-by-one on the boundary is the usual bug.",
    ),
    "NETWORKING_INFRA": _seed(
        "NETWORKING_INFRA",
        lesson=(
            "An IPv4 address is 32 bits wearing dots. CIDR steals high bits for the network "
            "and leaves the rest for hosts. /26 means 6 host bits — 64 addresses, 62 usable "
            "if you still believe in network and broadcast addresses.\n\n"
            "Work 192.168.10.40/26 on paper: mask, network, usable count. Then let the lab "
            "confirm. If you only memorize '254 hosts on a /24' you will fail a /26 quiz in "
            "a SOC ticket tomorrow.\n\n"
            "This is not CCNA. It is one calculation you can redo offline when the wiki is down."
        ),
        assignment="Compute network and usable hosts for 192.168.10.40/26 and one /28 of your choice.",
        student_packet="Calculator allowed. Phone subnet apps are not — show the bit math.",
        instructor_packet="Watch for people subtracting 2 on /31. The lab treats /32 and /31 as special.",
        slides="32 bits. Prefix. Usable = 2^(32-p)-2 when p≤30. Worked /26.",
        group_project="Each pair designs a 4-subnet plan for a one-room lab without overlapping.",
        assessment=[
            {"id": "net1", "q": "Usable hosts in /26?", "a": "62"},
            {"id": "net2", "q": "Network of 192.168.10.40/26?", "a": "192.168.10.0"},
        ],
        portfolio="paper bit-math photo (no PII) + lab JSON",
        tutor_prompt="How many host bits remain after the prefix?",
        tutor_reply="/26 leaves 6 host bits. 2^6=64 addresses; usable is 62 when broadcast exists.",
    ),
    "CYBER_SOC": _seed(
        "CYBER_SOC",
        lesson=(
            "A SOC junior does not 'hack back.' They count, threshold, and write one honest "
            "sentence. AUTH_FAIL lines that pile onto one user are a burst. Bursts are not "
            "proof of an attacker — they are proof you should look.\n\n"
            "The lab counts AUTH_FAIL tokens and flags users at threshold 3. You will also "
            "practice not pasting passwords into the incident note. If the note needs a "
            "secret, the note is wrong.\n\n"
            "Privacy: these logs are synthetic. Never import real school logs into this pack."
        ),
        assignment="Write a 3-sentence incident note from the fixture. Name burst users. No secrets.",
        student_packet="You are on the watch floor for 20 minutes. Escalate with a sentence, not a vibe.",
        instructor_packet="Reject notes that include passwords or real emails. Burst ≠ attribution.",
        slides="Count → threshold → note. AUTH_FAIL. Secrets never in tickets.",
        group_project="One analyst, one incident commander. Commander may only accept a one-liner.",
        assessment=[
            {"id": "soc1", "q": "Who bursts in the fixture?", "a": "ada"},
            {"id": "soc2", "q": "May the incident note include a password?", "a": "no"},
        ],
        portfolio="incident_note.md + fail_counts",
        tutor_prompt="Is a burst attribution?",
        tutor_reply="No. ada crossed the threshold; your note should say 'burst,' not 'attacker.'",
    ),
    "DATA_DASHBOARDS": _seed(
        "DATA_DASHBOARDS",
        lesson=(
            "A dashboard that cannot be rebuilt from a CSV is decoration. Start with group-by "
            "and top-N. Gary logged 20 lab hours, Ghana 5, Geelong 9 — the wall chart should "
            "match the arithmetic, not a designer’s guess.\n\n"
            "The lab sums a metric by site and returns the top two. Ties break alphabetically. "
            "You will then sketch the same table on paper so a sponsor who hates charts can "
            "still read the ranking."
        ),
        assignment="Recompute top-2 site hours by hand. Change top_n to 3 and explain what appears.",
        student_packet="Spreadsheet optional. The Python lab is the source of truth for this seed.",
        instructor_packet="Catch students who average when the metric is already a sum of hours.",
        slides="CSV → group-by → top-N → wall table. Ties. No 3-D pie charts.",
        group_project="Each trio owns one site's story: what the hours mean, not just the number.",
        assessment=[
            {"id": "db1", "q": "Gary total hours in fixture?", "a": "20"},
            {"id": "db2", "q": "Top-2 labels?", "a": "Gary, Geelong"},
        ],
        portfolio="wall_table.md + lab top list",
        tutor_prompt="Are you summing or averaging hours?",
        tutor_reply="Sum hours first. Gary is 12+8=20 and should lead the top-N.",
    ),
    "AI_ML_EDGE": _seed(
        "AI_ML_EDGE",
        lesson=(
            "Edge AI in this seed is 1-nearest-neighbor in 2-D. No GPU, no cloud, no 'training "
            "pipeline.' You store a few labeled points and assign each query the label of the "
            "closest training point by squared Euclidean distance.\n\n"
            "That is enough to feel the difference between a local decision and an API call. "
            "It is not a claim of model quality. gunnchAI tutoring here is a Socratic hint, "
            "not an inference server.\n\n"
            "Try moving a query across a decision boundary on paper before you run the lab."
        ),
        assignment="Classify two queries by hand against the three training points, then run the lab.",
        student_packet="No internet required. If someone says 'just use ChatGPT,' redirect to 1-NN.",
        instructor_packet="Do not allow cloud APIs for the lab pass. Discuss overfitting only as a teaser.",
        slides="Points on a plane. Distance. Argmin label. Cloud_used must be false.",
        group_project="Invent two new training points that flip one query label; defend the change.",
        assessment=[
            {"id": "ml1", "q": "k in this seed?", "a": "1"},
            {"id": "ml2", "q": "May the lab call a cloud model?", "a": "no"},
        ],
        portfolio="paper decision sketch + labels JSON",
        tutor_prompt="Which training point is closest, not which label you hope for?",
        tutor_reply="(1.9,2.1) sits next to (2,2) signal. (0.1,0.2) sits next to noise at the origin.",
    ),
    "EMBEDDED_PROTOTYPING": _seed(
        "EMBEDDED_PROTOTYPING",
        lesson=(
            "A GPIO bitmask is a set of pins encoded as bits. Pin 3 set means OR with 1<<3. "
            "Pin 0 is not 'optional' — it is bit 0, value 1, and firmware people forget it "
            "because zero looks like off.\n\n"
            "You will encode pins 0, 3, and 7. Read the hex back. If your mask is 0x88 you "
            "dropped pin 0. This maps to header-pin pointing on a real board later; this seed "
            "does not toggle hardware."
        ),
        assignment="Compute the mask on paper. Explain pin 0 in one sentence. Run the lab.",
        student_packet="No soldering. If you have a donor header, point — do not wire 5V to GPIO.",
        instructor_packet="Fail masks that ignore pin 0. Range errors must raise, not wrap.",
        slides="1<<n. OR. Hex readback. Pin 0 trap. No live 5V.",
        group_project="Map a 4-pin 'LED bar' to bits and write the on/off table.",
        assessment=[
            {"id": "em1", "q": "Mask for pins 0,3,7?", "a": "0x00000089"},
            {"id": "em2", "q": "Why is pin 0 special in this lesson?", "a": "bit 0 looks like off if omitted"},
        ],
        portfolio="bit table + gpio_mask_hex",
        tutor_prompt="Did you OR 1<<0, or did zero disappear?",
        tutor_reply="Pins 0,3,7 → bits 1 + 8 + 128 = 137 = 0x89. If you see 0x88, pin 0 was dropped.",
    ),
    "WIRELESS_6G": _seed(
        "WIRELESS_6G",
        lesson=(
            "OFDM packs many narrow subcarriers into one symbol. A cyclic prefix copies the "
            "tail onto the front so delayed copies still look circular. That prefix is not "
            "free: samples spent on CP are samples not spent on new data.\n\n"
            "Work a 64-point FFT with 52 occupied bins and CP=16. Symbol length is 80 samples. "
            "Overhead is 16/80. Occupancy is 52/64. Null bins exist on purpose (guards).\n\n"
            "6G slogans do not replace this arithmetic. This seed does not claim a 6G air "
            "interface implementation — it claims you can compute overhead offline."
        ),
        assignment="Compute symbol_samples, cp_overhead, occupancy, and say it in one sentence.",
        student_packet="Paper first. The lab sentence is a check, not a quote to memorize.",
        instructor_packet="If they cite a vendor slide instead of 16/80, send them back to the FFT size.",
        slides="Subcarriers. CP copy. Overhead fraction. Occupied vs null. Honesty about 6G.",
        group_project="Change CP to 8 and 32; plot overhead vs robustness as a 3-point table.",
        assessment=[
            {"id": "rf1", "q": "Symbol samples for n_fft=64 cp=16?", "a": "80"},
            {"id": "rf2", "q": "Does this seed implement 6G?", "a": "no"},
        ],
        portfolio="one_sentence + overhead table",
        tutor_prompt="Where did the 80 come from?",
        tutor_reply="64 FFT samples plus 16 cyclic-prefix samples. Overhead 16/80, occupancy 52/64.",
    ),
    "PM_AGILE_LSS": _seed(
        "PM_AGILE_LSS",
        lesson=(
            "Critical path is the longest chain of dependent work, not the noisiest standup. "
            "Lean Six Sigma will wait; today you only add durations along predecessors.\n\n"
            "Tasks: A=2, B=3 after A, C=1 after A, D=4 after B and C. The long way is "
            "A-B-D = 9 days. C is shorter slack. Sticky notes on a table are the kinesthetic "
            "version; the lab must match the stickies."
        ),
        assignment="Draw the four-box graph. Mark the 9-day path. Name one task with slack.",
        student_packet="You are not sitting PMP. You are adding days without double-counting.",
        instructor_packet="Watch for people summing all tasks (2+3+1+4=10) instead of the path.",
        slides="Nodes, arrows, longest path, slack. Standup ≠ path.",
        group_project="Add a task E and defend whether the critical path moves.",
        assessment=[
            {"id": "pm1", "q": "Critical path days in fixture?", "a": "9"},
            {"id": "pm2", "q": "Why isn't the answer 10?", "a": "C is parallel with B, not added on top"},
        ],
        portfolio="sticky photo or sketch + critical_path_days",
        tutor_prompt="Are you summing every box or only the longest chain?",
        tutor_reply="A-B-D is 2+3+4=9. C finishes earlier, so it does not extend D beyond B.",
    ),
    "GAME_DEV_INTERACTIVE": _seed(
        "GAME_DEV_INTERACTIVE",
        lesson=(
            "Axis-aligned bounding boxes are rectangles that do not rotate. They overlap when "
            "they overlap on X and on Y. The minimum translation vector (MTV) is the smallest "
            "push that separates them — usually along the shallower axis.\n\n"
            "Place A at (0,0) 10×10 and B at (8,2) 10×10. They overlap. Push along X by -2 "
            "(or +2 the other way) if that axis is shallower than Y. Feel it: two paper "
            "index cards on a desk."
        ),
        assignment="Predict overlap and MTV, then run the lab. Move B until overlap is false.",
        student_packet="No engine install required. Cards on a desk count as the kinesthetic lab.",
        instructor_packet="Reject Unity screenshots as a substitute for the AABB numbers.",
        slides="AABB test. Shallow axis. MTV. Overlap false after the push.",
        group_project="Add a moving platform; keep using AABB, no rotation.",
        assessment=[
            {"id": "gd1", "q": "Do the fixture boxes overlap?", "a": "yes"},
            {"id": "gd2", "q": "MTV prefers which axis here?", "a": "x (shallower)"},
        ],
        portfolio="card photo or sketch + mtv JSON",
        tutor_prompt="Which overlap is shallower, X or Y?",
        tutor_reply="A ends at x=10, B starts at 8 → 2px on X. Y overlap is larger, so MTV is on X.",
    ),
    "SEVEN_GC_APPRENTICESHIP": _seed(
        "SEVEN_GC_APPRENTICESHIP",
        lesson=(
            "Shannon capacity C = B log2(1+SNR) is an upper bound under AWGN, not a 7GC field "
            "measurement. A 1 MHz slice at SNR=3 linear yields about 2 Mbit/s. Real RAN "
            "overhead, scheduling, and hardware make that number optimistic.\n\n"
            "Apprentices list assumptions before they quote C. This seed forces the list: "
            "AWGN, single user, no overhead, not a field measurement. If a poster drops the "
            "list, the poster is overclaiming."
        ),
        assignment="Compute C. Write four assumptions. State one reason a drive-test would differ.",
        student_packet="Research apprentice mode: numbers without assumptions are not passing.",
        instructor_packet="Kill any sentence that says 'we achieved Shannon capacity in the field.'",
        slides="C=B log2(1+SNR). Units. Assumption list. Overclaim firewall.",
        group_project="Compare two SNR values and explain diminishing returns in one paragraph.",
        assessment=[
            {"id": "ap1", "q": "Name one required assumption.", "a": "AWGN (or single_user / no_overhead / not field)"},
            {"id": "ap2", "q": "Is C a field KPI?", "a": "no"},
        ],
        portfolio="assumption_list.md + capacity_mbps",
        tutor_prompt="What did you assume before quoting megabits?",
        tutor_reply="1e6 * log2(1+3) ≈ 2.0 Mbps. That is a bound, not a campus measurement.",
    ),
    "CLOUD_DEVOPS": _seed(
        "CLOUD_DEVOPS",
        lesson=(
            "Clusters forgive nothing you forgot to reject at the gate. A class manifest needs "
            "an image with a tag, a positive replica count, a legal port, and no privileged "
            "flag. Privileged containers are forbidden in this classroom cluster even if a "
            "blog said they are 'easier for hardware.'\n\n"
            "Owner program file for this course is a four-line stub. The product seed is the "
            "validator. You still do not have a full DevOps course — you have one gate."
        ),
        assignment="Break the fixture four ways (tag, replicas, port, privileged) and record errors.",
        student_packet="No cloud account. Validation is local. Do not enable privileged to 'make it work.'",
        instructor_packet="The owner stub is not curriculum. Grade the validator, not YAML cosplay.",
        slides="Image:tag. Replicas≥1. Port range. Privileged forbidden.",
        group_project="Write a one-page 'why we reject privileged' for a fictional principal.",
        assessment=[
            {"id": "cd1", "q": "Is privileged allowed?", "a": "no"},
            {"id": "cd2", "q": "Must image include a tag?", "a": "yes"},
        ],
        portfolio="broken_manifests.md + validator errors",
        tutor_prompt="Which of the four gates failed?",
        tutor_reply="A passing fixture has image:tag, replicas≥1, port in 1–65535, privileged false.",
    ),
    "COMM_PD_ETHICS": _seed(
        "COMM_PD_ETHICS",
        lesson=(
            "Professional writing in WAIKE is specific and kind, and it does not leak PII. "
            "Emails and US-style phone numbers in a peer draft get replaced with [EMAIL] and "
            "[PHONE] so a screenshot can leave the room.\n\n"
            "Redaction is not paraphrasing into mush. The sentence must still tell someone to "
            "call Maya before class — just not at 219-555-0142. Owner file is a stub; this "
            "seed is the redaction drill plus a tone check: no shame language."
        ),
        assignment="Redact the fixture. Then redact a paragraph you invent that contains one email.",
        student_packet="Do not use real classmate contact info. Synthetic only.",
        instructor_packet="If a student pastes a real number, stop and delete. This is an ethics fail.",
        slides="PII tokens. Placeholders. Meaning preserved. No shame.",
        group_project="Swap drafts; partner must find any leftover PII in 60 seconds.",
        assessment=[
            {"id": "ce1", "q": "Fixture phone becomes what token?", "a": "[PHONE]"},
            {"id": "ce2", "q": "May you use a real classmate number?", "a": "no"},
        ],
        portfolio="redacted paragraph + counts",
        tutor_prompt="Does the sentence still make sense after placeholders?",
        tutor_reply="Keep 'Call Maya at [PHONE] or [EMAIL] before class.' Meaning stays; digits go.",
    ),
    "ROBOTICS_CONTROL": _seed(
        "ROBOTICS_CONTROL",
        lesson=(
            "A proportional controller does one thing: delta = Kp * error. Heading 10°, target "
            "30°, Kp=0.5 → you add 10° and land at 20°. You did not arrive yet. Large Kp "
            "overshoots; you can feel it by turning a chair too fast toward a tape mark.\n\n"
            "This is not PID, not a rover, not ROS. Owner file is a stub. The seed is one step "
            "and a warning about gain."
        ),
        assignment="Compute the next heading. Repeat with Kp=2 and describe overshoot risk.",
        student_packet="Chair-and-tape optional. Do not drive a robot you do not own.",
        instructor_packet="Keep Kp discussion qualitative after the one-step lab. No live motors required.",
        slides="error. Kp. next = heading + Kp*error. Overshoot if |Kp|>1 in this toy.",
        group_project="Tune Kp so two steps land within 2° without a |Kp|>1.",
        assessment=[
            {"id": "rb1", "q": "Next heading for fixture?", "a": "20"},
            {"id": "rb2", "q": "Why is Kp=2 risky here?", "a": "overshoot (|Kp|>1)"},
        ],
        portfolio="step table + next_heading",
        tutor_prompt="Did you add Kp*error to heading, or replace heading with the target?",
        tutor_reply="error=20, delta=10, next=20. You are halfway; the controller is not a teleport.",
    ),
    "GUNNCHOS_PRODUCT_LAB": _seed(
        "GUNNCHOS_PRODUCT_LAB",
        lesson=(
            "Product lab honesty: uptime is stop minus start, summed. If a slide claims 100% "
            "and the sessions say 90 seconds in a longer window, the slide is wrong. This "
            "course sits on gunnchOS device sessions — still not a claim that Device Lab "
            "visual tokens are earned here.\n\n"
            "Parse two sessions (100–160 and 200–230). Total 90 s. Mean 45 s. If claimed "
            "ratio > 1, mark honest_claim false. Owner file is a stub pointer."
        ),
        assignment="Compute total and mean uptime. Invent a dishonest claim and show the lab flags it.",
        student_packet="Use the fixture JSON. Do not paste production logs with usernames.",
        instructor_packet="Tie this to claim firewalls: Cursor never merges; humans never rubber-stamp 100%.",
        slides="start/stop. Sum. Mean. claimed>1 fails. No visual token from this seed.",
        group_project="Design a session schema with an explicit claim_boundary field.",
        assessment=[
            {"id": "pl1", "q": "Total uptime fixture?", "a": "90"},
            {"id": "pl2", "q": "claimed_uptime_ratio=1.2 honest?", "a": "no"},
        ],
        portfolio="session table + honest_claim",
        tutor_prompt="What arithmetic would make 100% true?",
        tutor_reply="Only if stop-start covers the whole window. The fixture totals 90 s, not 'always up.'",
    ),
    "HARDWARE_ENGINEERING": _seed(
        "HARDWARE_ENGINEERING",
        lesson=(
            "A voltage divider is two resistors in series. Vout = Vin * R2/(R1+R2) when you "
            "take the tap across R2. 5 V, 1 kΩ, 3 kΩ → 3.75 V. Current is Vin/(R1+R2).\n\n"
            "Owner program is a 54-byte stub. This seed is "
            "Ohm's-law arithmetic plus a warning: do not build it on a live 120 V circuit. "
            "Paper and the lab are enough for digital acceptance of the *seed*, not of a "
            "hardware engineering degree."
        ),
        assignment="Compute Vout and current. Swap R1/R2 and predict the new Vout.",
        student_packet="No mains wiring. Optional: 5 V USB power only under instructor watch.",
        instructor_packet="Kill any attempt to measure mains. Grade the ratio, not a breadboard photo.",
        slides="Series resistors. Ratio. Current. Safety: no mains.",
        group_project="Choose R values for ~2.5 V from 5 V with current < 1 mA.",
        assessment=[
            {"id": "hw1", "q": "Vout for 5V, 1k, 3k?", "a": "3.75"},
            {"id": "hw2", "q": "Is the owner stub a course?", "a": "no"},
        ],
        portfolio="divider sketch + vout",
        tutor_prompt="Which resistor is the tap across?",
        tutor_reply="Tap across R2: 5 * 3000/4000 = 3.75 V. Current 5/4000 = 1.25 mA.",
    ),
    "DATA_VIZ_BI": _seed(
        "DATA_VIZ_BI",
        lesson=(
            "A histogram is a count of values that fell into edges. Edges [0,3,6,10] make "
            "three bins: [0,3), [3,6), [6,10]. The last bin includes the right edge so 10 "
            "does not fall on the floor. Values 1,2,2,5,9 → counts 3,1,1.\n\n"
            "Sponsors understand bins better than kernel density. Owner file is a stub. This "
            "seed is binning plus a sentence you could say in a budget meeting."
        ),
        assignment="Bin the fixture by hand. Add a value of 10 and update the last bin.",
        student_packet="No BI suite login. Paper bars are accepted as the sketch.",
        instructor_packet="Catch off-by-one on the last edge. Do not accept a pie chart substitute.",
        slides="Edges. Half-open bins. Last edge inclusive. Say the counts in words.",
        group_project="Pick bin widths that hide vs reveal a gap; write which is honest.",
        assessment=[
            {"id": "vz1", "q": "Fixture counts?", "a": "3,1,1"},
            {"id": "vz2", "q": "Does 10 belong in the last bin?", "a": "yes"},
        ],
        portfolio="bar sketch + counts",
        tutor_prompt="Is the last edge included?",
        tutor_reply="Yes for this lab. 1,2,2 land in bin 0; 5 in bin 1; 9 in bin 2 → [3,1,1].",
    ),
}


def seed_for(course_id: str) -> dict[str, Any]:
    if course_id not in SEEDS:
        raise KeyError(course_id)
    return SEEDS[course_id]


def assert_all_seeds() -> None:
    missing = [c for c in COURSE_IDS if c not in SEEDS]
    extra = [c for c in SEEDS if c not in COURSE_IDS]
    if missing or extra:
        raise RuntimeError(f"seed/catalog mismatch missing={missing} extra={extra}")
    for cid, seed in SEEDS.items():
        blob = " ".join(str(seed[k]) for k in ("lesson", "assignment", "student_packet", "instructor_packet")).lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in blob:
                raise RuntimeError(f"{cid} contains owner-template phrase: {phrase}")
