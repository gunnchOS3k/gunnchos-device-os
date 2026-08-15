## Summary
- Ingest accepted WAIKE **twelve-course** catalog post-#46 (tip includes #47 mastery) via versioned COW store (`owner-e4dd4df67f95`); rollback to prior nine-course retained.
- Consume gunnchAI accepted tip **#37** honesty matrix (#35) + mastery sidecar; **refuse unmerged #36/#38**. Product UI must not claim COMPLETE for PARTIAL/OPEN.
- Pin accepted-main SHAs including field-kit **#79**, WAIKE tip, gunnchAI #37; four-game pins unchanged (Anime #76, Pedestrian #17, Archive #30, Beat Link #21).
- Host free-space gate ≥25 GiB / preferred ≥40 GiB; sealed base + COW only (no second QEMU, no reprovision).
- Guest depth: **G14 CLOSED** (edit→py_compile→artifact sha256→run); **FOUR_GAME CLOSED** including Beat Link (scoped `@socket.io/component-emitter` + `/root/release/ACHIEVEMENTS.json`); Ring still OPEN at `guest_dispatch_to_app_receipt` (latency waterfall recorded; not a raw timeout).
- Cursor never merges. Tokens stay honest; BUILDER+CREATIVE true only where earned; STUDENT/OFFICE/TEACHER false while S1>0.

## Test plan
- [x] Sealed base preserved; COW persona overlay only
- [x] WAIKE store active lists 12 course_ids; rollback tested
- [x] GUNNCHAI_HONESTY_CONSUMED.json at #37; refused #36/#38
- [x] G14 git_build_test artifact_sha256 + RUN_OUT=5 + DSXL PASS
- [x] FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS (4/4) on accepted mains
- [ ] RING_TO_REAL_APP_STATE_MUTATION_PASS (browser memo boundary)
- [ ] S0=0 and S1=0 before any persona Product-Use PASS claim / independent verifier
- [ ] Prefer FAIL over invented guest PASS
