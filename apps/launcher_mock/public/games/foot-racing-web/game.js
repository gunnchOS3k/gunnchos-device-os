const canvas = document.getElementById('track')
const ctx = canvas.getContext('2d')
const titleScreen = document.getElementById('screen-title')
const gameScreen = document.getElementById('screen-game')
const winScreen = document.getElementById('screen-win')
const timerEl = document.getElementById('timer')
const distanceEl = document.getElementById('distance')
const boostFill = document.getElementById('boost-fill')
const winTimeEl = document.getElementById('win-time')

const LANES = [160, 400, 640]
const TRACK_LENGTH = 6000
const RUNNER_NAME = 'Bolt'

const keysDown = new Set()
let running = false
let finished = false
let elapsed = 0
let distance = 0
let boost = 100
let lane = 1
let laneY = 0
let hitFlash = 0
let obstacles = []

function resetRace() {
  running = true
  finished = false
  elapsed = 0
  distance = 0
  boost = 100
  lane = 1
  laneY = 0
  hitFlash = 0
  obstacles = spawnObstacles()
}

function spawnObstacles() {
  const list = []
  for (let d = 800; d < TRACK_LENGTH - 400; d += 420 + Math.random() * 280) {
    const type = Math.random() < 0.55 ? 'barrier' : 'puddle'
    list.push({
      distance: d,
      lane: Math.floor(Math.random() * 3),
      type,
      width: type === 'barrier' ? 50 : 70,
      height: type === 'barrier' ? 40 : 24,
    })
  }
  return list
}

document.getElementById('btn-start').onclick = () => {
  titleScreen.classList.remove('active')
  gameScreen.classList.add('active')
  winScreen.classList.remove('active')
  resetRace()
  requestAnimationFrame(loop)
}

document.getElementById('btn-exit').onclick = () => {
  running = false
  gameScreen.classList.remove('active')
  titleScreen.classList.add('active')
}

document.getElementById('btn-replay').onclick = () => {
  winScreen.classList.remove('active')
  gameScreen.classList.add('active')
  resetRace()
  requestAnimationFrame(loop)
}

document.getElementById('btn-win-exit').onclick = () => {
  running = false
  winScreen.classList.remove('active')
  titleScreen.classList.add('active')
}

window.addEventListener('keydown', e => {
  keysDown.add(e.code)
  if (e.code === 'ArrowLeft' && lane > 0) lane--
  if (e.code === 'ArrowRight' && lane < 2) lane++
})
window.addEventListener('keyup', e => keysDown.delete(e.code))

function update(dt) {
  if (!running || finished) return

  elapsed += dt
  const sprinting = keysDown.has('Space') && boost > 0
  const accelerating = keysDown.has('ArrowUp')
  let speed = 180
  if (accelerating) speed += 80
  if (sprinting) {
    speed += 140
    boost = Math.max(0, boost - 55 * dt)
  } else {
    boost = Math.min(100, boost + 25 * dt)
  }
  if (hitFlash > 0) speed *= 0.45

  distance += speed * dt
  laneY += (LANES[lane] - laneY) * 0.18

  for (const obs of obstacles) {
    const obsDist = obs.distance
    if (Math.abs(distance - obsDist) < 35 && obs.lane === lane) {
      hitFlash = 0.6
      boost = Math.max(0, boost - 18)
      obs.lane = -1
    }
  }

  if (hitFlash > 0) hitFlash -= dt

  if (distance >= TRACK_LENGTH) {
    finished = true
    running = false
    gameScreen.classList.remove('active')
    winScreen.classList.add('active')
    winTimeEl.textContent = `Finish time: ${elapsed.toFixed(1)} seconds`
  }
}

function drawTrack(scroll) {
  ctx.fillStyle = '#243447'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  for (let i = 0; i < 3; i++) {
    const x = LANES[i]
    ctx.strokeStyle = '#3d5166'
    ctx.setLineDash([12, 16])
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, canvas.height)
    ctx.stroke()
    ctx.setLineDash([])
  }

  ctx.fillStyle = '#2d4a3e'
  ctx.fillRect(0, 0, canvas.width, 48)
  ctx.fillStyle = '#9aa0a6'
  ctx.font = '14px system-ui'
  ctx.fillText('START', 24, 30)

  const finishY = canvas.height - 80 - ((TRACK_LENGTH - scroll) % canvas.height)
  if (scroll > TRACK_LENGTH - canvas.height) {
    ctx.fillStyle = '#fff'
    ctx.fillRect(0, canvas.height - 72, canvas.width, 8)
    ctx.fillStyle = '#111'
    for (let x = 0; x < canvas.width; x += 40) {
      ctx.fillRect(x, canvas.height - 72, 20, 8)
    }
    ctx.fillStyle = '#ffd93d'
    ctx.font = 'bold 16px system-ui'
    ctx.fillText('FINISH', canvas.width / 2 - 32, canvas.height - 84)
  }

  for (const obs of obstacles) {
    const rel = obs.distance - scroll
    if (rel < -80 || rel > canvas.height + 80 || obs.lane < 0) continue
    const y = canvas.height - 120 - rel * 0.12
    const x = LANES[obs.lane] - obs.width / 2
    if (obs.type === 'barrier') {
      ctx.fillStyle = '#e85d4c'
      ctx.fillRect(x, y, obs.width, obs.height)
      ctx.fillStyle = '#fff'
      ctx.font = '10px monospace'
      ctx.fillText('!', x + obs.width / 2 - 3, y + 26)
    } else {
      ctx.fillStyle = '#4a90c2'
      ctx.beginPath()
      ctx.ellipse(x + obs.width / 2, y + 12, obs.width / 2, obs.height / 2, 0, 0, Math.PI * 2)
      ctx.fill()
    }
  }
}

function drawRunner() {
  const x = laneY - 22
  const y = canvas.height - 140
  const bob = Math.sin(elapsed * 12) * (keysDown.has('ArrowUp') || keysDown.has('Space') ? 4 : 2)

  if (hitFlash > 0) {
    ctx.fillStyle = 'rgba(255, 80, 80, 0.35)'
    ctx.fillRect(x - 10, y - 70, 64, 80)
  }

  ctx.fillStyle = '#4ecdc4'
  ctx.fillRect(x + 8, y - 48 + bob, 28, 36)
  ctx.fillStyle = '#ffd93d'
  ctx.fillRect(x + 14, y - 58 + bob, 16, 14)
  ctx.fillStyle = '#2a2f3a'
  ctx.fillRect(x, y - 12 + bob, 14, 28)
  ctx.fillRect(x + 30, y - 12 + bob, 14, 28)

  ctx.fillStyle = '#fff'
  ctx.font = '12px monospace'
  ctx.fillText(RUNNER_NAME, x, y - 62 + bob)
}

let lastTs = 0
function loop(ts) {
  if (!gameScreen.classList.contains('active')) return
  const dt = Math.min(0.05, (ts - lastTs) / 1000 || 0.016)
  lastTs = ts

  update(dt)
  drawTrack(distance)
  drawRunner()

  timerEl.textContent = `Time: ${elapsed.toFixed(1)}s`
  distanceEl.textContent = `Distance: ${Math.min(100, Math.floor((distance / TRACK_LENGTH) * 100))}%`
  boostFill.style.width = `${boost}%`

  requestAnimationFrame(loop)
}
