# Screen Reader Notes

## Tested environments

- [ ] VoiceOver (macOS) — not formally tested
- [ ] NVDA (Windows) — not formally tested
- [ ] Orca (Linux) — not formally tested

## Known gaps

- Mock status rows in Settings may announce as static text only
- Game canvas content (web slices) may not expose live regions
- Media player controls need labeled buttons audit

## Recommendations before certification

1. Add `main`, `nav`, `aside` landmarks across shell panels
2. Announce policy blocks via live region
3. Test onboarding flow with screen reader script

**Not a screen reader certification report.**
