// KongPoko — Ponpoko-style platformer built ON the Kong3D engine.
// Engine provides: app bootstrap, audio, input, physics, textures (engine.js).
// This file is: level data (ponpoko_level1.json) + game-specific visuals/logic.
import * as THREE from 'three';
import { createApp, AudioSystem, KeyInput, Physics, canvasTexture, levelFromScene } from './engine.js';

// ---------- engine bootstrap ----------
const app = createApp({ mount: document.getElementById('game'), background: 0x000008, fov: 50 });
const { scene, camera } = app;
app.defaultLights({ hemi: 1.0, sunI: 1.4 });
const audio = new AudioSystem(camera);
const input = new KeyInput();

// ---------- game-specific visuals (faithful 1982 Ponpoko look) ----------
const plankTex = canvasTexture((g, w, h) => {
  g.fillStyle = '#1a0f08'; g.fillRect(0, 0, w, h);
  g.fillStyle = '#e8e4d8';
  for (let x = 4; x < w; x += 22) { g.fillRect(x, 14, 14, 9); g.fillRect(x, h - 23, 14, 9); }
  g.fillStyle = '#c9722e'; g.fillRect(0, h / 2 - 6, w, 12);
}, 128, 64, 6, 1);
const mats = {
  plat: new THREE.MeshStandardMaterial({ map: plankTex, roughness: .85 }),
  ladder: new THREE.MeshStandardMaterial({ color: 0xf5e9c8, roughness: .6 }),
  ladderRung: new THREE.MeshStandardMaterial({ color: 0xffd94a, roughness: .55 }),
};
const platforms = [], ladders = [], snakes = [], fruits = [];
function box(w, h, d, mat, x, y) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, 0); scene.add(m); return m;
}
function buildPlatform({ x, y, w, phys }) {
  const m = box(w, 0.5, 2, mats.plat, x, y); m.userData = { w, h: 0.5, phys }; platforms.push(m);
}
function buildLadder({ x, y0, y1 }) {
  const h = y1 - y0;
  box(0.09, h, 0.3, mats.ladder, x - 0.32, y0 + h / 2);
  box(0.09, h, 0.3, mats.ladder, x + 0.32, y0 + h / 2);
  for (let ry = 0.18; ry < h; ry += 0.4) box(0.72, 0.09, 0.32, mats.ladderRung, x, y0 + ry);
  ladders.push({ x, y0, y1 });
}
function buildSnake({ x, y, range, ai }) {
  const g = new THREE.Group();
  const red = new THREE.MeshStandardMaterial({ color: 0xe63c2f, roughness: .5 });
  const yel = new THREE.MeshStandardMaterial({ color: 0xffd94a, roughness: .5 });
  for (let i = 0; i < 5; i++) {
    const seg = new THREE.Mesh(new THREE.SphereGeometry(0.16 - i * 0.014, 10, 8), i % 2 ? yel : red);
    seg.position.x = -0.22 * i; g.add(seg);
  }
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.2, 12, 10), red);
  head.position.set(0.16, 0.05, 0); g.add(head);
  for (const s of [-1, 1]) {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.07, 8, 6),
      new THREE.MeshStandardMaterial({ color: 0xffffff }));
    eye.position.set(0.26, 0.14, 0.08 * s); g.add(eye);
    const pup = new THREE.Mesh(new THREE.SphereGeometry(0.035, 6, 5),
      new THREE.MeshStandardMaterial({ color: 0x111111 }));
    pup.position.set(0.32, 0.14, 0.08 * s); g.add(pup);
  }
  g.position.set(x, y + 0.2, 0); scene.add(g);
  snakes.push({ x, y: y + 0.2, r: 0.45, grp: g, x0: x, range, dir: 1, beh: ai?.behavior ?? 'patrol', speed: ai?.speed ?? 1.1 });
}
const FRUIT_COLORS = [0xe63c2f, 0xff9a2e, 0xffe14a, 0x7ad14f, 0xff5fa2, 0xc9722e];
function buildFruit({ x, y, phys }) {
  const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.SphereGeometry(0.26, 16, 12),
    new THREE.MeshStandardMaterial({ color: FRUIT_COLORS[fruits.length % 6], roughness: .35, emissive: 0x1a0a02 }));
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.16, 6),
    new THREE.MeshStandardMaterial({ color: 0x5d4037 }));
  stem.position.y = 0.32;
  const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.09, 8, 6),
    new THREE.MeshStandardMaterial({ color: 0x4fae3f }));
  leaf.scale.set(1.4, 0.5, 0.8); leaf.position.set(0.1, 0.36, 0);
  g.add(body, stem, leaf);
  g.position.set(x, y, 0); g.userData.phys = phys; g.userData.vy = 0; scene.add(g); fruits.push(g);
}

// ---------- player: tanuki (red-brown fur, yellow belly, ringed tail — cover-art faithful) ----------
const player = new THREE.Group();
{
  const fur = new THREE.MeshStandardMaterial({ color: 0xc0392b, roughness: .6 });
  const belly = new THREE.MeshStandardMaterial({ color: 0xffd94a, roughness: .5 });
  const white = new THREE.MeshStandardMaterial({ color: 0xf6f2e8, roughness: .5 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x241611, roughness: .5 });
  const body = new THREE.Mesh(new THREE.SphereGeometry(0.34, 16, 12), fur);
  body.scale.set(1, 1.15, 0.9);
  const bellyM = new THREE.Mesh(new THREE.SphereGeometry(0.26, 14, 10), belly);
  bellyM.scale.set(1, 1.1, 0.62); bellyM.position.set(0.1, -0.06, 0.02);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.24, 14, 10), fur);
  head.position.set(0.06, 0.46, 0);
  const muzzle = new THREE.Mesh(new THREE.SphereGeometry(0.13, 10, 8), white);
  muzzle.scale.set(1.2, 0.9, 0.9); muzzle.position.set(0.2, 0.42, 0);
  const nose = new THREE.Mesh(new THREE.SphereGeometry(0.045, 8, 6), dark);
  nose.position.set(0.33, 0.45, 0);
  const cheekM = new THREE.MeshStandardMaterial({ color: 0xff5f5f, roughness: .5 });
  for (const s of [-1, 1]) {
    const ear = new THREE.Mesh(new THREE.ConeGeometry(0.09, 0.16, 8), fur);
    ear.position.set(0.02, 0.68, 0.13 * s); player.add(ear);
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.045, 8, 6), dark);
    eye.position.set(0.24, 0.54, 0.09 * s); player.add(eye);
    const cheek = new THREE.Mesh(new THREE.SphereGeometry(0.05, 8, 6), cheekM);
    cheek.position.set(0.22, 0.42, 0.16 * s); player.add(cheek);
    const foot = new THREE.Mesh(new THREE.SphereGeometry(0.1, 8, 6), dark);
    foot.scale.set(1.4, 0.6, 0.9); foot.position.set(0.05, -0.42, 0.14 * s); player.add(foot);
    const arm = new THREE.Mesh(new THREE.SphereGeometry(0.09, 8, 6), fur);
    arm.scale.set(1.5, 0.8, 0.8); arm.position.set(0.14, 0.12, 0.26 * s); player.add(arm);
  }
  for (let i = 0; i < 4; i++) {
    const ring = new THREE.Mesh(new THREE.SphereGeometry(0.11 - i * 0.012, 8, 6), i % 2 ? dark : fur);
    ring.position.set(-0.34 - i * 0.14, -0.1 + i * 0.1, 0);
    player.add(ring);
  }
  player.add(body, bellyM, head, muzzle, nose);
}
scene.add(player);

// ---------- game state / input ----------
const P = { x: -9, y: 1.0, vx: 0, vy: 0, grounded: false, onLadder: false, lives: 3, fruits: 0, dead: false, won: false };
let SPAWN = [-9, 1.0];
const SPEED = 4.2, JUMP = 7.2, GRAV = 16, STEP = 0.14;
const keys = input.keys;
function spawnP() { P.x = SPAWN[0]; P.y = SPAWN[1]; P.vx = 0; P.vy = 0; }
function nearLadder() { return ladders.some(l => Math.abs(P.x - l.x) < 0.6 && P.y > l.y0 - 0.6 && P.y < l.y1 + 1.2); }

input.onTap(code => {
  if (P.won || P.dead) return;
  if (code === 'KeyD') P.x += STEP;
  else if (code === 'KeyA') P.x -= STEP;
  else if (code === 'Space') P.jumpReq = performance.now();
  else if (code === 'KeyW' && nearLadder()) { P.y += STEP; P.onLadder = true; P.vy = 0; }
  else if (code === 'KeyS' && nearLadder()) { P.y -= STEP; P.onLadder = true; P.vy = 0; P.dropT = performance.now() + 300; }
});

// ---------- HUD ----------
const hudFruit = document.querySelector('#hud .fruit');
const hudLives = document.querySelector('#hud .lives');
const hudStage = document.querySelector('#hud .stage');
const banner = document.getElementById('banner'), bannerText = document.getElementById('bannerText');
function updHud() {
  hudFruit.textContent = `🍎 ${P.fruits}/${fruits.length}`;
  hudLives.textContent = '♥'.repeat(P.lives) + '·'.repeat(Math.max(0, 3 - P.lives));
}

// ---------- level load ----------
// priority 1: GUI-authored scene from the editor (role-tagged objects, saved via editor Save)
// priority 2: bundled JSON level file
function loadLevel() {
  try {
    const raw = localStorage.getItem('kong3d_scene');
    if (raw) {
      const L = levelFromScene(JSON.parse(raw));
      if (L) { L.name = 'GUI STAGE'; return Promise.resolve(L); }
    }
  } catch (e) { /* fall through to bundled level */ }
  return fetch('./ponpoko_level1.json').then(r => r.json());
}
loadLevel().then(L => {
  SPAWN = L.spawn; hudStage.textContent = L.name;
  L.platforms.forEach(buildPlatform);
  L.ladders.forEach(buildLadder);
  L.snakes.forEach(buildSnake);
  L.fruits.forEach(buildFruit);
  spawnP(); updHud();
  app.start(tick);
});

// ---------- game logic ----------
function hurt() {
  if (P.dead || P.won || performance.now() < (P.inv || 0)) return;
  P.inv = performance.now() + 1500;
  P.lives--; audio.sfx('hurt'); updHud();
  if (P.lives <= 0) {
    P.dead = true; bannerText.textContent = 'GAME OVER'; bannerText.style.color = '#ff6b81';
    banner.style.display = 'grid';
  } else spawnP();
}
function win() {
  P.won = true; audio.sfx('clear');
  bannerText.textContent = 'STAGE CLEAR!'; banner.style.display = 'grid';
}
function tick(dt) {
  if (!P.won && !P.dead) {
    const L = nearLadder();
    if (!L) P.onLadder = false;
    if (keys.KeyD) P.vx = SPEED; else if (keys.KeyA) P.vx = -SPEED; else P.vx = 0;
    if (P.onLadder && L) {
      if (keys.KeyW) P.vy = 2.6; else if (keys.KeyS) P.vy = -2.6; else P.vy = 0;
    } else {
      P.vy -= GRAV * dt;
    }
    const jumpAsked = keys.Space || (P.jumpReq && performance.now() - P.jumpReq < 300);
    if (jumpAsked && (P.grounded || P.onLadder)) {
      P.vy = JUMP; P.grounded = false; P.onLadder = false; P.jumpReq = 0; audio.sfx('jump');
    }
    P.x += P.vx * dt; P.y += P.vy * dt;
    P.x = Math.max(-10.5, Math.min(10.5, P.x));
    // platform landing via engine physics; skip while descending a ladder
    const dropping = P.onLadder && (keys.KeyS || P.vy < -0.1 || performance.now() < (P.dropT || 0));
    P.grounded = !dropping && Physics.landOnPlatforms(P, platforms, { eye: 0.55, snap: 0.35, skip: p => p.userData.phys?.collider === false });
    if (P.y < -3) hurt();
    for (const s of snakes) {
      if (s.beh === 'chase') { s.dir = P.x > s.x ? 1 : -1; s.x += s.dir * s.speed * dt; }
      else if (s.beh === 'patrol') {
        s.x += s.dir * s.speed * dt;
        if (s.x > s.x0 + s.range) s.dir = -1; else if (s.x < s.x0 - s.range) s.dir = 1;
      }
      s.grp.position.x = s.x;
      s.grp.rotation.y = s.dir > 0 ? 0 : Math.PI;
      s.grp.position.y = s.y + Math.sin(performance.now() / 120 + s.x0) * 0.03;
      if (Math.hypot(P.x - s.x, P.y - 0.4 - s.y) < s.r) { hurt(); break; }
    }
    for (const f of fruits) {
      if (f.visible && Math.hypot(P.x - f.position.x, P.y - f.position.y) < 0.62) {
        f.visible = false; P.fruits++; audio.sfx('pickup'); updHud();
        if (P.fruits === fruits.length) win();
      }
      if (f.visible) f.rotation.y += dt * 2;
      // per-object physics (gravity + bounce), configured in the editor
      const ph = f.userData.phys;
      if (f.visible && ph?.gravity) {
        f.userData.vy -= GRAV * 0.5 * dt;
        f.position.y += f.userData.vy * dt;
        for (const p of platforms) {
          const top = p.position.y + 0.25;
          if (f.userData.vy < 0 && Math.abs(f.position.x - p.position.x) < p.userData.w / 2 &&
              f.position.y - 0.26 <= top && f.position.y - 0.26 > top - 0.3) {
            f.position.y = top + 0.26;
            f.userData.vy = (ph.bounce ?? 0) > 0.05 ? -f.userData.vy * ph.bounce : 0;
          }
        }
        if (f.position.y < -3) { f.position.y = 6; f.userData.vy = 0; }
      }
    }
    player.position.set(P.x, P.y, 0);
    player.rotation.y = P.vx >= 0 ? 0.3 : Math.PI - 0.3;
  }
  camera.position.lerp(new THREE.Vector3(P.x * 0.6, Math.max(3.2, P.y + 1.2), 13), 0.08);
  camera.lookAt(P.x * 0.6, Math.max(2.4, P.y), 0);
  app.renderer.render(scene, camera);
}

// verification hook + dbg line
window.kongpoko = {
  pos: () => [P.x.toFixed(2), P.y.toFixed(2)],
  fruits: () => `${P.fruits}/${fruits.length}`,
  lives: () => P.lives, won: () => P.won, lastSfx: () => audio.lastSfx,
};
const dbg = document.createElement('div');
dbg.style.cssText = 'position:fixed;top:10px;left:12px;font:12px ui-monospace,monospace;color:#4fd1c5;background:rgba(16,19,34,.7);padding:5px 9px;border-radius:8px';
document.body.appendChild(dbg);
setInterval(() => {
  dbg.textContent = `p ${P.x.toFixed(1)},${P.y.toFixed(1)} ${P.grounded ? 'g' : P.onLadder ? 'L' : 'a'} ♪${audio.lastSfx}`;
}, 100);
