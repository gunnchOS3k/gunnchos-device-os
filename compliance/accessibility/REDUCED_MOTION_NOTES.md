# Reduced Motion Notes

- `reducedMotion` setting persists in localStorage
- CSS transitions in Settings toggles may still animate unless gated
- Game web slices use canvas animation — not tied to reduced motion preference

## Action items

- [ ] Respect `prefers-reduced-motion` media query globally
- [ ] Disable non-essential animations when reduced motion enabled
- [ ] Document game slice exceptions
