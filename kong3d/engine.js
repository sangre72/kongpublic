// Kong3D engine core — shared by the editor (app.js) and games built on it (game.js).
// Provides: app bootstrap (scene/camera/renderer/loop/resize), audio system
// (procedural SFX + positional + BGM), input (key state + tap impulses),
// physics helpers (platform landing, AABB push-out), and primitive/scene-JSON helpers.
import * as THREE from 'three';

// ---------- app bootstrap ----------
export function createApp({ mount, background = 0x12141a, fog = null, fov = 55 } = {}) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(background);
  if (fog) scene.fog = new THREE.Fog(fog.color ?? background, fog.near, fog.far);
  const camera = new THREE.PerspectiveCamera(fov, 1, 0.1, 200);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(devicePixelRatio);
  mount.appendChild(renderer.domElement);
  function resize() {
    const w = mount.clientWidth || innerWidth, h = mount.clientHeight || innerHeight;
    camera.aspect = w / h; camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }
  new ResizeObserver(resize).observe(mount);
  addEventListener('resize', resize); resize();
  const clock = new THREE.Clock();
  return {
    scene, camera, renderer, clock,
    start(loop) { renderer.setAnimationLoop(() => loop(Math.min(clock.getDelta(), 0.05))); },
    defaultLights({ hemi = 0.9, sunI = 1.6 } = {}) {
      scene.add(new THREE.HemisphereLight(0xdde4ff, 0x1a1c24, hemi));
      const sun = new THREE.DirectionalLight(0xffffff, sunI);
      sun.position.set(6, 10, 4); scene.add(sun);
      return sun;
    },
  };
}

// ---------- audio system ----------
const SFX_RECIPES = {
  zap:    (t, dur) => Math.sin(2 * Math.PI * (900 - 700 * t / dur) * t) * 0.8,
  boing:  (t) => Math.sin(2 * Math.PI * (220 + 180 * Math.sin(t * 30)) * t) * 0.6,
  ding:   (t) => (Math.sin(2 * Math.PI * 1318 * t) + 0.5 * Math.sin(2 * Math.PI * 1979 * t)) * 0.5,
  thud:   (t) => (Math.random() * 2 - 1) * Math.exp(-t * 30) * 0.7,
  pickup: (t) => Math.sin(2 * Math.PI * (880 + 660 * t) * t),
  jump:   (t) => Math.sin(2 * Math.PI * (200 + 300 * t) * t),
  hurt:   (t) => Math.sin(2 * Math.PI * (300 - 200 * t) * t) + (Math.random() - .5) * .5,
  clear:  (t) => Math.sin(2 * Math.PI * [523, 659, 784, 1047][Math.floor(t * 5) % 4] * t),
};
const SFX_DUR = { thud: 0.15, clear: 0.9 };
const SFX_DECAY = { zap: 18, pickup: 10, ding: 9, boing: 9, thud: 9, jump: 5, hurt: 5, clear: 5 };

export class AudioSystem {
  constructor(camera) {
    this.listener = new THREE.AudioListener();
    camera.add(this.listener);
    this.cache = {}; this.lastSfx = '-';
    this.bgm = new THREE.Audio(this.listener); this.bgmMeta = null;
  }
  get context() { return this.listener.context; }
  buffer(kind) {
    if (this.cache[kind]) return this.cache[kind];
    const ctx = this.context, sr = ctx.sampleRate, dur = SFX_DUR[kind] ?? 0.3;
    const buf = ctx.createBuffer(1, sr * dur, sr), d = buf.getChannelData(0);
    const fn = SFX_RECIPES[kind] ?? SFX_RECIPES.ding, k = SFX_DECAY[kind] ?? 8;
    for (let i = 0; i < d.length; i++) {
      const t = i / sr;
      d[i] = fn(t, dur) * Math.exp(-t * k) * 0.6;
    }
    return this.cache[kind] = buf;
  }
  sfx(kind, vol = 0.7) {
    this.lastSfx = kind;
    const a = new THREE.Audio(this.listener);
    a.setBuffer(this.buffer(kind)); a.setVolume(vol); a.play();
  }
  sfxAt(kind, obj, refDist = 3) {
    this.lastSfx = kind + '@3d';
    const a = new THREE.PositionalAudio(this.listener);
    a.setBuffer(this.buffer(kind)); a.setRefDistance(refDist); a.setVolume(1);
    obj.add(a); a.play();
    a.source.onended = () => obj.remove(a);
  }
  loadBgm(dataUrl, name, { loop = true, volume = 0.4 } = {}) {
    return fetch(dataUrl).then(r => r.arrayBuffer())
      .then(ab => this.context.decodeAudioData(ab))
      .then(buf => {
        if (this.bgm.isPlaying) this.bgm.stop();
        this.bgm.setBuffer(buf); this.bgm.setLoop(loop); this.bgm.setVolume(volume);
        this.bgmMeta = { name, dataUrl };
      });
  }
  playBgm() { if (this.bgm.buffer && !this.bgm.isPlaying) this.bgm.play(); }
  pauseBgm() { if (this.bgm.isPlaying) this.bgm.pause(); }
}

// ---------- input ----------
export class KeyInput {
  constructor() {
    this.keys = {};
    this.tapHandlers = [];
    addEventListener('keydown', e => {
      this.keys[e.code] = true;
      for (const h of this.tapHandlers) h(e.code, e);
    });
    addEventListener('keyup', e => { this.keys[e.code] = false; });
  }
  // tap-impulse: a single scripted key event (CGEvent tap) still yields a visible step
  onTap(fn) { this.tapHandlers.push(fn); }
}

// ---------- physics ----------
export const Physics = {
  // side-view: land a point-actor (feet = pos.y - eye) on platform tops when falling
  landOnPlatforms(P, platforms, { eye = 0.55, snap = 0.35, margin = 0.2, skip = null } = {}) {
    let grounded = false;
    for (const p of platforms) {
      if (skip && skip(p)) continue;
      const top = p.position.y + p.userData.h / 2, w = p.userData.w;
      if (P.vy <= 0 && Math.abs(P.x - p.position.x) < w / 2 + margin &&
          P.y - eye <= top && P.y - eye > top - snap) {
        P.y = top + eye; P.vy = 0; grounded = true;
      }
    }
    return grounded;
  },
  // FPS: push a capsule-approx point out of world AABBs; returns grounded
  pushOutAABB(pos, vel, objects, { eye = 1.7, radius = 0.35, stepTop = 0.45 } = {}) {
    let grounded = false;
    if (pos.y < eye) { pos.y = eye; vel.y = 0; grounded = true; }
    const tmp = new THREE.Box3();
    for (const o of objects) {
      tmp.setFromObject(o); tmp.expandByScalar(radius);
      const feet = pos.y - eye, head = pos.y;
      if (pos.x > tmp.min.x && pos.x < tmp.max.x &&
          pos.z > tmp.min.z && pos.z < tmp.max.z &&
          head > tmp.min.y && feet < tmp.max.y) {
        if (feet >= tmp.max.y - stepTop && vel.y <= 0) {
          pos.y = tmp.max.y + eye; vel.y = 0; grounded = true; continue;
        }
        const dxl = pos.x - tmp.min.x, dxr = tmp.max.x - pos.x;
        const dzl = pos.z - tmp.min.z, dzr = tmp.max.z - pos.z;
        const m = Math.min(dxl, dxr, dzl, dzr);
        if (m === dxl) pos.x = tmp.min.x; else if (m === dxr) pos.x = tmp.max.x;
        else if (m === dzl) pos.z = tmp.min.z; else pos.z = tmp.max.z;
      }
    }
    return grounded;
  },
};

// ---------- primitives + scene JSON ----------
export function makeGeo(kind) {
  switch (kind) {
    case 'box': return new THREE.BoxGeometry(1, 1, 1);
    case 'cylinder': return new THREE.CylinderGeometry(0.5, 0.5, 1, 32);
    case 'sphere': return new THREE.SphereGeometry(0.6, 32, 24);
    case 'plane': return new THREE.PlaneGeometry(2, 2);
  }
}
export function makePrimitive(kind, { color = 0x7c6cff, roughness = 0.55, metalness = 0.15 } = {}) {
  return new THREE.Mesh(makeGeo(kind),
    new THREE.MeshStandardMaterial({ color, roughness, metalness,
      side: kind === 'plane' ? THREE.DoubleSide : THREE.FrontSide }));
}
export function serializeObjects(objects) {
  return objects.map(o => ({
    kind: o.userData.kind, name: o.name,
    position: o.position.toArray(),
    rotation: o.rotation.toArray().slice(0, 3),
    scale: o.scale.toArray(),
    color: o.material.color.getHex(),
    target: !!o.userData.target,
    role: o.userData.role,
    ai: o.userData.ai,
    phys: o.userData.phys,
    profile: o.userData.profile,
    smooth: o.userData.smooth,
  }));
}
export function applyObjectData(mesh, d) {
  mesh.position.fromArray(d.position);
  mesh.rotation.fromArray(d.rotation);
  mesh.scale.fromArray(d.scale);
  if (d.name) mesh.name = d.name;
  if (d.target) mesh.userData.target = true;
  if (d.role) mesh.userData.role = d.role;
  if (d.ai) mesh.userData.ai = d.ai;
  if (d.phys) mesh.userData.phys = d.phys;
}
// map a role-tagged editor scene (GUI-authored) to platformer level data
export function levelFromScene(sceneJson) {
  const L = { name: 'GUI STAGE', spawn: [-9, 1.0], platforms: [], ladders: [], snakes: [], fruits: [] };
  let found = false;
  for (const o of sceneJson.objects ?? []) {
    const [x, y] = [o.position[0], o.position[1]];
    const [sx, sy] = [o.scale[0], o.scale[1]];
    switch (o.role) {
      case 'platform': L.platforms.push({ x, y, w: sx, phys: o.phys }); found = true; break;
      case 'ladder':   L.ladders.push({ x, y0: y - sy / 2, y1: y + sy / 2 }); found = true; break;
      case 'fruit':    L.fruits.push({ x, y, phys: o.phys }); found = true; break;
      case 'snake':    L.snakes.push({ x, y: y - 0.2, range: o.ai?.range ?? Math.max(1, sx), ai: o.ai, phys: o.phys }); found = true; break;
      case 'spawn':    L.spawn = [x, Math.max(0.8, y)]; found = true; break;
    }
  }
  return found ? L : null;
}
// profile-curve geometry: control points (x,y) → smooth Catmull-Rom outline →
// extruded slab (depth 1 on z, centered — use object scale.z as width) or lathe.
// points: [x, y, corner?] — corner=1 marks a hard angle break: the outline is split
// into smooth runs between corner points; each run is spline-sampled, corners stay sharp.
function sampleOutline(points, per = 24) {
  const runs = [];
  let run = [points[0]];
  for (let i = 1; i < points.length; i++) {
    run.push(points[i]);
    if (points[i][2]) { runs.push(run); run = [points[i]]; }
  }
  if (run.length > 1) runs.push(run);
  const out = [];
  for (const r of runs) {
    if (r.length === 2) {
      out.push(new THREE.Vector2(r[0][0], r[0][1]));
    } else {
      const c = new THREE.SplineCurve(r.map(p => new THREE.Vector2(p[0], p[1])));
      const pts = c.getPoints(per * (r.length - 1));
      out.push(...pts.slice(0, -1));
    }
  }
  out.push(new THREE.Vector2(points[points.length - 1][0], points[points.length - 1][1]));
  return out;
}
// widthProfile: variable extrusion width by height (tumblehome / plan taper).
// {beltY, roofFrac, rockerFrac}: z-scale = 1.0 at beltY, rockerFrac at min-y, roofFrac at max-y.
export function applyWidthProfile(geo, { beltY = 0.9, roofFrac = 0.78, rockerFrac = 0.97, noseFrac = 1, tailFrac = 1, taperStart = 0.55 } = {}) {
  geo.computeBoundingBox();
  const { min, max } = geo.boundingBox;
  const pos = geo.attributes.position;
  const xc = (min.x + max.x) / 2, halfL = (max.x - min.x) / 2;
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i);
    let f;
    if (y >= beltY) {
      const t = (y - beltY) / Math.max(0.001, max.y - beltY);
      f = 1 + (roofFrac - 1) * t * t;      // ease-in tuck above the beltline
    } else {
      const t = (beltY - y) / Math.max(0.001, beltY - min.y);
      f = 1 + (rockerFrac - 1) * t;
    }
    // plan-view taper: width eases toward nose/tail ends (rounded corners, no slab face)
    const x = pos.getX(i);
    const u = (x - xc) / halfL;            // -1 nose .. +1 tail
    const a = Math.abs(u);
    if (a > taperStart) {
      const k = (a - taperStart) / (1 - taperStart);
      const endFrac = u < 0 ? noseFrac : tailFrac;
      f *= 1 + (endFrac - 1) * k * k;      // ease-in toward the end
    }
    pos.setZ(i, pos.getZ(i) * f);
  }
  pos.needsUpdate = true;
  geo.computeVertexNormals();
  return geo;
}
export function profileGeometry({ points, lathe = false, width }) {
  if (lathe) {
    const pts = sampleOutline(points).map(p => new THREE.Vector2(Math.abs(p.x), p.y));
    return new THREE.LatheGeometry(pts, 48);
  }
  const pts = sampleOutline(points);
  const shape = new THREE.Shape(pts);
  const geo = new THREE.ExtrudeGeometry(shape, { depth: 1, bevelEnabled: true, bevelThickness: 0.06, bevelSize: 0.06, bevelSegments: 3, curveSegments: 48 });
  geo.translate(0, 0, -0.5);
  return geo;
}
// repeating pixel-style canvas texture (used for arcade-look levels)
export function canvasTexture(draw, w = 128, h = 128, rx = 1, ry = 1) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rx, ry);
  t.magFilter = THREE.NearestFilter;
  return t;
}
