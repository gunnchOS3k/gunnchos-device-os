/**
 * Fixture screenshot harness for VXP visual evidence.
 * evidence_class: VISUAL_FIXTURE_NOT_PROVIDER_PROOF
 * Does not claim Pixel/physical validation.
 */
import { createServer } from 'node:http'
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs'
import { dirname, join, extname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createHash } from 'node:crypto'
import { chromium } from 'playwright'

const __dirname = dirname(fileURLToPath(import.meta.url))
const shellRoot = join(__dirname, '..')
const repoRoot = join(shellRoot, '../..')
const outRoot = join(repoRoot, 'artifacts/vxp')
const afterDir = join(outRoot, 'after')
const beforeDir = join(outRoot, 'before')
const manifestPath = join(outRoot, 'manifests/VXP_SCREENSHOT_MANIFEST.json')

const VIEWPORTS = [
  { name: 'phone-360', width: 360, height: 800 },
  { name: 'phone-430', width: 430, height: 932 },
  { name: 'tablet-768x1024', width: 768, height: 1024 },
  { name: 'laptop-1366x768', width: 1366, height: 768 },
  { name: 'desktop-1440x900', width: 1440, height: 900 },
  { name: 'desktop-1920x1080', width: 1920, height: 1080 },
]

const SURFACES = ['home', 'vault', 'app_center', 'connect', 'assist', 'care']

function sha256(buf) {
  return createHash('sha256').update(buf).digest('hex')
}

function contentType(file) {
  switch (extname(file)) {
    case '.html':
      return 'text/html'
    case '.js':
      return 'text/javascript'
    case '.css':
      return 'text/css'
    case '.svg':
      return 'image/svg+xml'
    default:
      return 'application/octet-stream'
  }
}

async function main() {
  mkdirSync(afterDir, { recursive: true })
  mkdirSync(beforeDir, { recursive: true })
  mkdirSync(dirname(manifestPath), { recursive: true })

  // Prefer built assets; fall back to a minimal fixture HTML if dist missing.
  const distIndex = join(shellRoot, 'dist/index.html')
  const useDist = existsSync(distIndex)

  const fixtureHtml = `<!doctype html><html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>VXP fixture</title>
<link rel="stylesheet" href="/src/design/tokens.css"/>
<link rel="stylesheet" href="/src/cx2.css"/>
</head><body><div id="root"></div>
<script type="module">
import React from 'https://esm.sh/react@18.2.0'
import { createRoot } from 'https://esm.sh/react-dom@18.2.0/client'
// Network-dependent fallback is intentionally avoided in CI — use dist when present.
document.getElementById('root').innerHTML = '<div class="cx2-shell vxp-living" role="application" aria-label="gunnchOS Complete Experience"><header class="cx2-topbar vxp-topbar"><div class="cx2-brand" aria-label="gunnchOS brand"><span class="cx2-brand-mark">gunnchOS</span><span class="cx2-brand-sub">Living Workspace</span></div></header><main class="cx2-main"><section class="cx2-panel vxp-home"><h1>gunnchOS</h1><p class="lead">Fixture shell for visual capture.</p></section></main><nav class="vxp-dock" aria-label="Primary"><button class="vxp-dock-btn active">Home</button><button class="vxp-dock-btn">Vault</button><button class="vxp-dock-btn">App Center</button><button class="vxp-dock-btn">Connect</button><button class="vxp-dock-btn">More</button></nav></div>'
</script></body></html>`

  const server = createServer((req, res) => {
    try {
      const url = new URL(req.url || '/', 'http://127.0.0.1')
      if (!useDist && url.pathname === '/') {
        res.writeHead(200, { 'Content-Type': 'text/html' })
        res.end(fixtureHtml)
        return
      }
      const base = useDist ? join(shellRoot, 'dist') : shellRoot
      let filePath = join(base, url.pathname === '/' ? 'index.html' : url.pathname)
      if (!existsSync(filePath) && url.pathname.startsWith('/src/')) {
        filePath = join(shellRoot, url.pathname.slice(1))
      }
      if (!existsSync(filePath)) {
        res.writeHead(404)
        res.end('missing')
        return
      }
      const buf = readFileSync(filePath)
      res.writeHead(200, { 'Content-Type': contentType(filePath) })
      res.end(buf)
    } catch (e) {
      res.writeHead(500)
      res.end(String(e))
    }
  })

  await new Promise((r) => server.listen(0, '127.0.0.1', r))
  const { port } = server.address()
  const origin = `http://127.0.0.1:${port}`

  let browser
  const entries = []
  try {
    browser = await chromium.launch({ headless: true })
    for (const vp of VIEWPORTS) {
      const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } })
      await page.goto(origin + '/', { waitUntil: 'networkidle' })
      for (const surface of SURFACES) {
        // Best-effort: click nav labels when present
        const btn = page.getByRole('button', { name: new RegExp(surface === 'app_center' ? 'App Center' : surface, 'i') }).first()
        if (await btn.count()) {
          try {
            await btn.click({ timeout: 1000 })
          } catch {
            /* fixture may be static */
          }
        }
        const file = `after_${surface}_${vp.name}.png`
        const abs = join(afterDir, file)
        const buf = await page.screenshot({ fullPage: true })
        writeFileSync(abs, buf)
        entries.push({
          file: `artifacts/vxp/after/${file}`,
          surface,
          viewport: vp,
          host: 'browser_fixture',
          provider_state: 'not_applicable_fixture',
          timestamp: new Date().toISOString(),
          sha256: sha256(buf),
          evidence_class: 'VISUAL_FIXTURE_NOT_PROVIDER_PROOF',
        })
      }
      // variants
      for (const variant of ['high-contrast', 'reduce-motion']) {
        await page.evaluate((v) => {
          const el = document.querySelector('.cx2-shell')
          if (el) el.classList.add(v)
        }, variant)
        const file = `after_home_${vp.name}_${variant}.png`
        const abs = join(afterDir, file)
        const buf = await page.screenshot({ fullPage: true })
        writeFileSync(abs, buf)
        entries.push({
          file: `artifacts/vxp/after/${file}`,
          surface: 'home',
          variant,
          viewport: vp,
          host: 'browser_fixture',
          provider_state: 'not_applicable_fixture',
          timestamp: new Date().toISOString(),
          sha256: sha256(buf),
          evidence_class: 'VISUAL_FIXTURE_NOT_PROVIDER_PROOF',
        })
      }
      await page.close()
    }
  } catch (err) {
    // Playwright may be unavailable — write honest pending fixture note
    const note = join(afterDir, 'CAPTURE_PENDING.txt')
    writeFileSync(
      note,
      `Playwright capture failed or unavailable: ${err}\nDigital screenshots PENDING. Do not label as physical.\n`,
    )
    entries.push({
      file: 'artifacts/vxp/after/CAPTURE_PENDING.txt',
      surface: 'harness',
      host: 'browser_fixture',
      timestamp: new Date().toISOString(),
      evidence_class: 'VISUAL_FIXTURE_NOT_PROVIDER_PROOF',
      error: String(err),
    })
  } finally {
    if (browser) await browser.close()
    server.close()
  }

  const manifest = {
    program: 'VXP-0/VXP-1',
    evidence_class: 'VISUAL_FIXTURE_NOT_PROVIDER_PROOF',
    note: 'Browser/fixture captures only. VXP_PIXEL_VISUAL_CAPTURE_PASS remains false without authentic Pixel evidence.',
    base_sha: 'f460ac7b0e94c98060e7aeafc3ee82fb3c65237d',
    entries,
  }
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n')
  console.log(`Wrote ${entries.length} manifest entries → ${manifestPath}`)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
