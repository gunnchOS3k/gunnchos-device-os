# Dependency Remediation Plan — launcher_mock (RC1 → v1.0.0)

**Repo:** `gunnchOS3k/gunnchos-device-os`  
**Package root:** `apps/launcher_mock`  
**Accepted main pin:** `c6fd04aced44b0d3eec6f07c3b0b3fdbe50ad7a4`  
**Policy:** No `npm audit fix --force` without reviewed written reason. Prefer lockfile-safe fixes first.

## RC1 actions completed

1. Fresh `npm ci` on post-#161 main.
2. Full + production JSON audits captured (pre/post).
3. `npm explain` for every high/critical package (`vitest`, `vite`, `browserslist`, `nanoid`, `postcss`).
4. Safe `npm audit fix` (no `--force`) → cleared browserslist / nanoid / postcss / baseline-browser-mapping.
5. Regression: `npm test` → 77/77 pass.
6. Production audit remains **0** critical / **0** high.

## Deferred (post-RC1 / before final v1.0.0 preferred)

### Track A — Vite major upgrade (closes R2, R5)

| Item | Plan |
|---|---|
| Target | `vite@^6` or `^8` after compatibility check with `@vitejs/plugin-react` |
| Risk | Breaking config / CJS Node API / plugin peer ranges |
| Tests | `npm test`, `npm run build`, launcher shell smoke |
| Force reason if needed | Only if intermediate versions leave GHSA-fx2h-pf6j-xcff open; document in PR |

### Track B — Vitest major upgrade (closes R1, R3, R4)

| Item | Plan |
|---|---|
| Target | `vitest@^3` or `^5` aligned with chosen Vite |
| Risk | API changes in config, jsdom env, matchMedia polyfill tests |
| Tests | Full `apps/launcher_mock` vitest suite + CX2 shell tests |
| Note | Vitest UI server advisories: keep UI disabled in CI; no public bind |

### Track C — overrides (last resort)

Only if major bumps slip past RC1 window and a production-reachable issue appears:

```json
"overrides": { "postcss": ">=8.5.23", "nanoid": ">=3.3.18" }
```

Not required now — those were cleared by safe fix. Do **not** override `vite`/`vitest` to fake green without upgrading consumers.

## Explicit non-actions for RC1

| Action | Decision |
|---|---|
| `npm audit fix --force` | **Rejected** — installs vite@8.3.0 / vitest@5.0.1 breaking majors mid-freeze |
| Pixel physical re-demo | **Not required** — no production/runtime dependency change |
| Claiming production critical=0 via ignoring audit | **N/A** — production audit is actually empty |

## Owner sign-off checklist (final v1.0.0)

- [ ] Track A + B landed on Device OS main
- [ ] `npm audit --omit=dev` still 0
- [ ] Dev toolchain critical either 0 or re-accepted with fresh classification
- [ ] Capsule rebuild only if runtime deps change
