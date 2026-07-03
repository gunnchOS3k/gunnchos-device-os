const canvas = document.getElementById('map')
const ctx = canvas.getContext('2d')
const titleScreen = document.getElementById('screen-title')
const gameScreen = document.getElementById('screen-game')
const zoneLabel = document.getElementById('zone-label')
const collectCount = document.getElementById('collect-count')
const speciesCard = document.getElementById('species-card')
const cardName = document.getElementById('card-name')
const cardHabitat = document.getElementById('card-habitat')
const cardFact = document.getElementById('card-fact')
const cardCitation = document.getElementById('card-citation')
const collectionLog = document.getElementById('collection-log')
const logList = document.getElementById('log-list')

const MAP_W = 960
const MAP_H = 640
const EXPLORER_NAME = 'Nora'

const SPECIES = [
  {
    id: 'coral-finch',
    name: 'Coral Finch',
    habitat: 'Sunlit meadow edges',
    color: '#ff8a65',
    x: 180,
    y: 140,
    fact: 'Coral Finches weave nests from dried grass and sing at dawn to mark territory boundaries.',
    citation: '[Citation placeholder: Field Guide to Fictional Avifauna, Vol. 2, p. 44]',
  },
  {
    id: 'moss-turtle',
    name: 'Moss Turtle',
    habitat: 'Shaded pond banks',
    color: '#7cb342',
    x: 620,
    y: 380,
    fact: 'Moss Turtles carry symbiotic algae on their shells, which helps camouflage them among wetland plants.',
    citation: '[Citation placeholder: Wetland Ecology Review, 2024 — pending verification]',
  },
  {
    id: 'star-orchid',
    name: 'Star Orchid',
    habitat: 'Forest understory',
    color: '#ce93d8',
    x: 480,
    y: 520,
    fact: 'Star Orchids bloom only after two weeks of steady rain and attract night pollinators with a faint glow.',
    citation: '[Citation placeholder: Botanical Archives — original research draft]',
  },
  {
    id: 'ridge-fox',
    name: 'Ridge Fox',
    habitat: 'Rocky highland trail',
    color: '#d4a574',
    x: 780,
    y: 160,
    fact: 'Ridge Foxes travel in pairs and leave scent markers on stones to guide juveniles along safe paths.',
    citation: '[Citation placeholder: Highland Mammal Survey, 2023]',
  },
]

const ZONES = [
  { name: 'Meadow Trail', x: 0, y: 0, w: 360, h: 280, color: '#3d5c3a' },
  { name: 'Pond Bank', x: 520, y: 280, w: 360, h: 280, color: '#2a4a5c' },
  { name: 'Forest Floor', x: 320, y: 400, w: 320, h: 240, color: '#2d3d28' },
  { name: 'Highland Ridge', x: 680, y: 0, w: 280, h: 220, color: '#4a4a3a' },
]

const keysDown = new Set()
let player = { x: 80, y: 80, w: 24, h: 24, speed: 3.2 }
let collected = new Set()
let active = false
let showLog = false

function resetGame() {
  player.x = 80
  player.y = 80
  collected = new Set()
  showLog = false
  speciesCard.classList.add('hidden')
  collectionLog.classList.add('hidden')
  active = true
}

document.getElementById('btn-start').onclick = () => {
  titleScreen.classList.remove('active')
  gameScreen.classList.add('active')
  resetGame()
  requestAnimationFrame(loop)
}

document.getElementById('btn-exit').onclick = () => {
  active = false
  gameScreen.classList.remove('active')
  titleScreen.classList.add('active')
}

document.getElementById('btn-close-card').onclick = () => speciesCard.classList.add('hidden')
document.getElementById('btn-close-log').onclick = () => {
  collectionLog.classList.add('hidden')
  showLog = false
}

window.addEventListener('keydown', e => {
  keysDown.add(e.code)
  if (e.code === 'KeyI' && active) toggleLog()
})
window.addEventListener('keyup', e => keysDown.delete(e.code))

function toggleLog() {
  showLog = !showLog
  if (showLog) {
    renderLog()
    collectionLog.classList.remove('hidden')
    speciesCard.classList.add('hidden')
  } else {
    collectionLog.classList.add('hidden')
  }
}

function renderLog() {
  logList.innerHTML = ''
  if (collected.size === 0) {
    const li = document.createElement('li')
    li.textContent = 'No artifacts collected yet.'
    logList.appendChild(li)
    return
  }
  for (const sp of SPECIES) {
    if (!collected.has(sp.id)) continue
    const li = document.createElement('li')
    li.innerHTML = `<strong>${sp.name}</strong> — ${sp.habitat}`
    logList.appendChild(li)
  }
}

function currentZone() {
  for (const z of ZONES) {
    if (player.x >= z.x && player.x < z.x + z.w && player.y >= z.y && player.y < z.y + z.h) return z.name
  }
  return 'Wilderness'
}

function update() {
  if (!active) return
  let dx = 0
  let dy = 0
  if (keysDown.has('KeyW') || keysDown.has('ArrowUp')) dy -= player.speed
  if (keysDown.has('KeyS') || keysDown.has('ArrowDown')) dy += player.speed
  if (keysDown.has('KeyA') || keysDown.has('ArrowLeft')) dx -= player.speed
  if (keysDown.has('KeyD') || keysDown.has('ArrowRight')) dx += player.speed

  player.x = Math.max(12, Math.min(MAP_W - 12, player.x + dx))
  player.y = Math.max(12, Math.min(MAP_H - 12, player.y + dy))

  for (const sp of SPECIES) {
    if (collected.has(sp.id)) continue
    const dist = Math.hypot(player.x - sp.x, player.y - sp.y)
    if (dist < 36) collectSpecies(sp)
  }

  zoneLabel.textContent = currentZone()
  collectCount.textContent = `Artifacts: ${collected.size} / ${SPECIES.length}`
}

function collectSpecies(sp) {
  collected.add(sp.id)
  cardName.textContent = sp.name
  cardHabitat.textContent = sp.habitat
  cardFact.textContent = sp.fact
  cardCitation.textContent = sp.citation
  speciesCard.classList.remove('hidden')
  collectionLog.classList.add('hidden')
  showLog = false
}

function drawMap() {
  ctx.fillStyle = '#1a2618'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  const camX = Math.max(0, Math.min(MAP_W - canvas.width, player.x - canvas.width / 2))
  const camY = Math.max(0, Math.min(MAP_H - canvas.height, player.y - canvas.height / 2))

  ctx.save()
  ctx.translate(-camX, -camY)

  for (const z of ZONES) {
    ctx.fillStyle = z.color
    ctx.fillRect(z.x, z.y, z.w, z.h)
    ctx.fillStyle = 'rgba(255,255,255,0.15)'
    ctx.font = '13px system-ui'
    ctx.fillText(z.name, z.x + 12, z.y + 22)
  }

  for (const sp of SPECIES) {
    if (collected.has(sp.id)) continue
    const pulse = 0.7 + Math.sin(Date.now() / 300) * 0.3
    ctx.fillStyle = sp.color
    ctx.globalAlpha = pulse
    ctx.beginPath()
    ctx.arc(sp.x, sp.y, 14, 0, Math.PI * 2)
    ctx.fill()
    ctx.globalAlpha = 1
    ctx.fillStyle = '#fff'
    ctx.font = '10px monospace'
    ctx.fillText('?', sp.x - 3, sp.y + 4)
  }

  ctx.fillStyle = '#6bcb77'
  ctx.fillRect(player.x - player.w / 2, player.y - player.h / 2, player.w, player.h)
  ctx.fillStyle = '#fff'
  ctx.font = '11px monospace'
  ctx.fillText(EXPLORER_NAME, player.x - 14, player.y - 18)

  ctx.restore()
}

function loop() {
  if (!gameScreen.classList.contains('active')) return
  update()
  drawMap()
  requestAnimationFrame(loop)
}
