const canvas = document.getElementById('arena')
const ctx = canvas.getContext('2d')
const titleScreen = document.getElementById('screen-title')
const gameScreen = document.getElementById('screen-game')
const p1HealthEl = document.getElementById('p1-health')
const p2HealthEl = document.getElementById('p2-health')

const GROUND = 380
const GRAVITY = 0.6

function makeFighter(name, x, color, keys) {
  return {
    name, x, y: GROUND, vx: 0, vy: 0, w: 40, h: 64, color,
    health: 100, onGround: true, attacking: false, attackTimer: 0, keys,
  }
}

let p1 = makeFighter('Rook', 120, '#ff6b6b', { left: 'KeyA', right: 'KeyD', jump: 'KeyW', attack: 'KeyJ' })
let p2 = makeFighter('Sage', 640, '#6bcb77', { left: 'ArrowLeft', right: 'ArrowRight', jump: 'ArrowUp', attack: 'KeyK' })
const keysDown = new Set()

document.getElementById('btn-start').onclick = () => {
  titleScreen.classList.remove('active')
  gameScreen.classList.add('active')
  resetFight()
  requestAnimationFrame(loop)
}

document.getElementById('btn-exit').onclick = () => {
  gameScreen.classList.remove('active')
  titleScreen.classList.add('active')
}

window.addEventListener('keydown', e => keysDown.add(e.code))
window.addEventListener('keyup', e => keysDown.delete(e.code))

if (navigator.getGamepads) {
  document.getElementById('controller-hint').textContent =
    'Controller detection placeholder — plug a gamepad (not wired in this slice)'
}

function resetFight() {
  p1 = makeFighter('Rook', 120, '#ff6b6b', p1.keys)
  p2 = makeFighter('Sage', 640, '#6bcb77', p2.keys)
}

function updateFighter(f, other) {
  const speed = 4
  if (keysDown.has(f.keys.left)) f.vx = -speed
  else if (keysDown.has(f.keys.right)) f.vx = speed
  else f.vx = 0

  if (keysDown.has(f.keys.jump) && f.onGround) {
    f.vy = -12
    f.onGround = false
  }

  if (keysDown.has(f.keys.attack) && f.attackTimer === 0) {
    f.attacking = true
    f.attackTimer = 18
    if (Math.abs(f.x - other.x) < 70 && Math.abs(f.y - other.y) < 50) {
      other.health = Math.max(0, other.health - 8)
    }
  }

  if (f.attackTimer > 0) {
    f.attackTimer--
    if (f.attackTimer === 0) f.attacking = false
  }

  f.vy += GRAVITY
  f.x += f.vx
  f.y += f.vy

  if (f.y >= GROUND) {
    f.y = GROUND
    f.vy = 0
    f.onGround = true
  }

  f.x = Math.max(20, Math.min(canvas.width - f.w - 20, f.x))

  if (f.x < -40 || f.x > canvas.width + 40) {
    other.health = Math.min(100, other.health + 5)
    f.health = Math.max(0, f.health - 15)
    f.x = canvas.width / 2
    f.y = GROUND
  }
}

function drawFighter(f) {
  ctx.fillStyle = f.color
  ctx.fillRect(f.x, f.y - f.h, f.w, f.h)
  ctx.fillStyle = '#fff'
  ctx.font = '12px monospace'
  ctx.fillText(f.name, f.x, f.y - f.h - 6)
  if (f.attacking) {
    ctx.fillStyle = '#ffd93d'
    ctx.fillRect(f.x + (f.vx >= 0 ? f.w : -20), f.y - 40, 20, 12)
  }
}

function loop() {
  if (!gameScreen.classList.contains('active')) return

  updateFighter(p1, p2)
  updateFighter(p2, p1)

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.fillStyle = '#2a2f3a'
  ctx.fillRect(0, GROUND + 64, canvas.width, 20)

  drawFighter(p1)
  drawFighter(p2)

  p1HealthEl.textContent = `Rook: ${p1.health}`
  p2HealthEl.textContent = `Sage: ${p2.health}`

  if (p1.health <= 0 || p2.health <= 0) {
    ctx.fillStyle = 'rgba(0,0,0,0.6)'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.fillStyle = '#fff'
    ctx.font = '24px system-ui'
    ctx.fillText(p1.health <= 0 ? 'Sage wins!' : 'Rook wins!', canvas.width / 2 - 60, canvas.height / 2)
    setTimeout(resetFight, 1500)
  }

  requestAnimationFrame(loop)
}
