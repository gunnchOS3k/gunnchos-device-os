# gunnchOS Phase XII GUI session

## Selected stack
**Weston** (Wayland reference compositor) configured as gunnchOS session for CI and
reference images.

### Why Weston (vs Plasma/GNOME/XFCE)
- Strong headless CI story (`headless-backend`)
- ARM + x86 support
- Lower RAM than full Plasma/GNOME for Student/Handheld profiles
- License/maintainability fit for reproducible images
- Plasma/GNOME/XFCE remain documented optional SKUs for richer desktop product lines

## CI
See `.github/workflows/phase-xii-execution-reality.yml` — installs `weston`, `xvfb`,
runs session smoke + screenshot capture.

## Branding
Session name, launcher, and wallpaper/theme overlays identify the desktop as
**gunnchOS**, not an untouched stock distro desktop.
