# GunnchOS Operating System Requirements v0.1

## 1. Product Vision

GunnchOS is an education-first, creator-first, gamer-first operating system for affordable handheld and portable devices. The target user is a learner, gamer, worker, visionary, creative, and builder who deserves access to serious tools without needing an expensive laptop.

The first narrowed user profile is a college student who may not have access to a high-end computer but still needs to code, write papers, attend class, use learning platforms, create media, build STEM projects, and play high-quality games.

GunnchOS must feel like a console when gaming, a Chromebook when studying, a Linux workstation when building, and an AI learning companion when the user is stuck.

## 2. Primary User

The first target user is:

A college student or advanced high school student who needs one affordable device for school, coding, research, productivity, creative work, STEM labs, communication, and recreation.

Secondary users include:

* First-generation college students
* Community college students
* STEM learners
* Digital equity program participants
* Young creators
* Gamers
* Student entrepreneurs
* Remote workers
* Students in under-resourced schools
* Non-STEM majors who still need modern digital tools

## 3. OS Design Principle

GunnchOS should not try to replace every expensive desktop app locally on day one. It should combine:

1. Local-first tools for offline work.
2. Web/PWA tools for Google Suite, Brightspace D2L, NotebookLM, ChatGPT, and browser-based apps.
3. Linux containers for coding, Python, STEM tools, and developer workflows.
4. Android compatibility for mobile-first education and creative apps.
5. Cloud/remote compute for heavy MATLAB, CAD, Adobe, rendering, AI, and simulation workloads.
6. Dedicated Game Mode for first-party games.

## 4. Required System Modes

### 4.1 Campus Mode

Campus Mode is the main desktop interface.

It must include:

* Browser
* File manager
* App launcher
* Google Drive integration
* Local downloads folder
* Offline documents folder
* Notes
* Calendar
* Email
* Audio recorder
* Camera app
* Screen recorder
* Video editor
* AI assistant panel
* Coding workspace
* STEM tools hub
* Creative tools hub
* Learning management system hub
* Cloud storage hub

### 4.2 Game Mode

Game Mode is the console interface.

It must include:

* Full-screen game launcher
* Controller-first navigation
* Touch navigation
* Suspend/resume
* Performance profiles
* Offline play
* Local save files
* Cloud save sync
* Per-game graphics settings
* FPS/performance overlay
* Parental/guardian controls for younger users
* Battery-saving mode
* Tournament/local multiplayer mode

Game Mode must prioritize the three first-party games:

1. Anime Aggressors
2. Foot Racing Game
3. Earth Species Artifact Adventure

## 5. Required Application Categories

See full specification in repository docs. Categories: Browser/Web, Coding, AI Learning, Productivity, Creative, STEM.

## 6. Application Compatibility Strategy

Four levels: Native GunnchOS Apps, Web/PWA Apps, Linux Apps, Android Apps.

## 7. Hardware Requirements

Minimum: ARM64 or x86_64, 8 GB RAM, 128 GB storage, Wi-Fi 6+, Bluetooth, USB-C, touchscreen, game controls, cameras, microphone, 6–10 hour battery.

## 8. First-Party Game Requirements

Three exclusive titles with original IP — platform fighter, foot racing, educational Earth exploration RPG.

## 9–12. Security, Accessibility, Roadmap, Success Metrics

See user-provided full specification. Phase 0 deliverables are implemented in `apps/launcher_mock/src/shell/` and documented in `docs/PHASE0.md`.

## Implementation status

### Phase 0 (merged — PR #30)

| Requirement | Status |
|-------------|--------|
| Campus Mode shell | Implemented (mock) |
| Game Mode shell | Implemented (mock) |
| Browser/PWA hub | Implemented (mock) |
| File manager | Implemented (mock) |
| Settings | Implemented (mock) |
| First boot / student profile | Implemented |
| Linux base image | Docker container prototype |

### Phase 1 (merged — PR #31)

| Requirement | Status |
|-------------|--------|
| Media Mode shell | Implemented (prototype) |
| YouTube/Netflix/Hulu routes | Browser route prototype |
| Python→React policy bridge | Export script + JSON contract |
| Media policy tests | pytest + Vitest |
| Official streaming certification | **Not claimed** |
| DRM circumvention | **Not supported** |

### Phase 2 (planning — operational gap audit)

| Deliverable | Status |
|-------------|--------|
| Full operational gap matrix | Documented |
| Mock retirement plan | Documented |
| Beta release gate definition | Documented |
| Implementation issues backlog | `docs/issues/` |
| Mock replacement implementation | **Not started** |

See `docs/PHASE1.md`, `docs/PHASE2_PLAN.md`, and `docs/FULL_OPERATIONAL_GAP_MATRIX.md`.
