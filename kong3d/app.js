import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { TransformControls } from 'three/addons/controls/TransformControls.js';
import { createApp, AudioSystem, Physics, makePrimitive, serializeObjects, applyObjectData, profileGeometry, applyWidthProfile } from './engine.js';

const vp = document.getElementById('viewport');
const app = createApp({ mount: vp, background: 0x12141a, fog: { near: 40, far: 90 } });
const { scene, camera, renderer } = app;
camera.position.set(6, 5, 8);

// default scene: grid + lights
scene.add(new THREE.GridHelper(24, 24, 0x3d4356, 0x232734));
app.defaultLights();

const orbit = new OrbitControls(camera, renderer.domElement);
orbit.mouseButtons = { LEFT: null, MIDDLE: THREE.MOUSE.PAN, RIGHT: THREE.MOUSE.ROTATE };
orbit.enableDamping = true;

const gizmo = new TransformControls(camera, renderer.domElement);
gizmo.addEventListener('dragging-changed', e => { orbit.enabled = !e.value; });
gizmo.addEventListener('objectChange', () => refreshProps());
scene.add(gizmo);

// ---------- object management ----------
const objects = [];
let selected = null;
let counter = { box: 0, cylinder: 0, sphere: 0, plane: 0 };
const PALETTE = [0x7c6cff, 0x4fd1c5, 0xffb454, 0xff6b81, 0x4fd18b, 0x6cb2ff];

function addObject(kind, data) {
  const color = data?.color ?? PALETTE[(objects.length) % PALETTE.length];
  let mesh;
  if (data?.profile) {
    const g = profileGeometry(data.profile);
    if (data.profile.widthProfile) applyWidthProfile(g, data.profile.widthProfile);
    mesh = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color, roughness: 0.45, metalness: 0.25 }));
    mesh.userData.profile = data.profile;
  } else {
    mesh = makePrimitive(kind, { color });
  }
  mesh.userData.kind = kind;
  mesh.name = data?.name ?? `${kind}_${++counter[kind]}`;
  if (data) {
    applyObjectData(mesh, data);
    const n = parseInt((data.name ?? '').split('_')[1]); if (n > counter[kind]) counter[kind] = n;
  } else {
    mesh.position.set((Math.random() - 0.5) * 4, kind === 'plane' ? 0.01 : 0.5, (Math.random() - 0.5) * 4);
    if (kind === 'plane') mesh.rotation.x = -Math.PI / 2;
  }
  scene.add(mesh); objects.push(mesh);
  select(mesh); refreshList();
  return mesh;
}
function removeObject(mesh) {
  if (selected === mesh) select(null);
  scene.remove(mesh); mesh.geometry.dispose(); mesh.material.dispose();
  objects.splice(objects.indexOf(mesh), 1);
  refreshList();
}
function select(mesh) {
  selected = mesh;
  if (mesh) gizmo.attach(mesh); else gizmo.detach();
  refreshList(); refreshProps();
}

// ---------- picking ----------
const ray = new THREE.Raycaster(), ptr = new THREE.Vector2();
let downAt = null;
renderer.domElement.addEventListener('pointerdown', e => { if (e.button === 0) downAt = [e.clientX, e.clientY]; });
renderer.domElement.addEventListener('pointerup', e => {
  if (e.button !== 0 || !downAt) return;
  const moved = Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]); downAt = null;
  if (moved > 4 || gizmo.dragging || curve.on) return;
  const r = renderer.domElement.getBoundingClientRect();
  ptr.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(ptr, camera);
  const hit = ray.intersectObjects(objects, false)[0];
  select(hit ? hit.object : null);
});

// ---------- UI: toolbar ----------
const $ = id => document.getElementById(id);
$('addBox').onclick = () => addObject('box');
$('addCyl').onclick = () => addObject('cylinder');
$('addSphere').onclick = () => addObject('sphere');
$('addPlane').onclick = () => addObject('plane');
// game-entity palette: placeable, role-tagged (GUI level-authoring)
const ENTITY_DEFS = {
  platform: { kind: 'box', color: 0xc9722e, scale: [4, 0.5, 2], y: 1.5 },
  ladder:   { kind: 'box', color: 0xffd94a, scale: [0.7, 2.4, 0.3], y: 1.45 },
  fruit:    { kind: 'sphere', color: 0xe63c2f, scale: [0.45, 0.45, 0.45], y: 1.2 },
  snake:    { kind: 'cylinder', color: 0x4fae3f, scale: [1.1, 0.35, 0.4], y: 0.45 },
  spawn:    { kind: 'cylinder', color: 0x4fd1c5, scale: [0.4, 1.2, 0.4], y: 0.85 },
};
function addEntity(role) {
  const d = ENTITY_DEFS[role];
  counter[role] = counter[role] ?? 0;
  const mesh = makePrimitive(d.kind, { color: d.color });
  mesh.userData.kind = d.kind; mesh.userData.role = role;
  mesh.name = `${role}_${++counter[role]}`;
  mesh.scale.fromArray(d.scale);
  mesh.position.set(0, d.y, 0);
  scene.add(mesh); objects.push(mesh);
  select(mesh); refreshList();
  return mesh;
}
$('entPlatform').onclick = () => addEntity('platform');
$('entLadder').onclick = () => addEntity('ladder');
$('entFruit').onclick = () => addEntity('fruit');
$('entSnake').onclick = () => addEntity('snake');
$('entSpawn').onclick = () => addEntity('spawn');
// ---------- curve tool: click control-points on the z=0 side plane → extrude/lathe ----------
const curve = { on: false, corner: false, pts: [], markers: [], line: null };
const curvePlane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
function curveClear() {
  for (const m of curve.markers) scene.remove(m);
  if (curve.line) scene.remove(curve.line);
  curve.pts = []; curve.markers = []; curve.line = null;
}
function curveRefresh() {
  if (curve.line) scene.remove(curve.line);
  if (curve.pts.length >= 2) {
    const sc = new THREE.SplineCurve(curve.pts.map(p => new THREE.Vector2(p[0], p[1])));
    const pts3 = sc.getPoints(96).map(p => new THREE.Vector3(p.x, p.y, 0.02));
    curve.line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts3),
      new THREE.LineBasicMaterial({ color: 0x4fd1c5 }));
    scene.add(curve.line);
  }
}
$('curveCorner').onclick = () => {
  curve.corner = !curve.corner;
  $('curveCorner').classList.toggle('active', curve.corner);
};
$('curveDraw').onclick = () => {
  curve.on = !curve.on;
  $('curveDraw').classList.toggle('active', curve.on);
  if (!curve.on) curveClear();
  else { select(null); toast('curve mode: click points in Side view, ✔ extrude / ◔ lathe'); }
};
renderer.domElement.addEventListener('pointerdown', e => {
  if (!curve.on || e.button !== 0) return;
  const r = renderer.domElement.getBoundingClientRect();
  ptr.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(ptr, camera);
  const hit = new THREE.Vector3();
  if (ray.ray.intersectPlane(curvePlane, hit)) {
    curve.pts.push([+hit.x.toFixed(3), +hit.y.toFixed(3), curve.corner ? 1 : 0]);
    const mk = new THREE.Mesh(new THREE.SphereGeometry(0.05, 8, 6),
      new THREE.MeshBasicMaterial({ color: curve.corner ? 0xff6b81 : 0xffb454 }));
    mk.position.set(hit.x, hit.y, 0.03); scene.add(mk); curve.markers.push(mk);
    curveRefresh();
  }
});
function finishCurve(lathe) {
  if (curve.pts.length < 3) return toast('need 3+ points');
  const profile = { points: curve.pts.slice(), lathe };
  const geo = profileGeometry(profile);
  const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({
    color: PALETTE[objects.length % PALETTE.length], roughness: 0.45, metalness: 0.25 }));
  counter.profile = counter.profile ?? 0;
  mesh.userData.kind = 'profile'; mesh.userData.profile = profile;
  mesh.name = `${lathe ? 'lathe' : 'profile'}_${++counter.profile}`;
  if (!lathe) mesh.scale.z = 1.9; // extrude slab: scale.z = width
  scene.add(mesh); objects.push(mesh);
  curve.on = false; $('curveDraw').classList.remove('active'); curveClear();
  select(mesh); refreshList();
}
$('curveDone').onclick = () => finishCurve(false);
$('curveLathe').onclick = () => finishCurve(true);
const modeBtns = { translate: $('modeMove'), rotate: $('modeRotate'), scale: $('modeScale') };
function setMode(m) {
  gizmo.setMode(m);
  for (const [k, b] of Object.entries(modeBtns)) b.classList.toggle('active', k === m);
}
$('modeMove').onclick = () => setMode('translate');
$('modeRotate').onclick = () => setMode('rotate');
$('modeScale').onclick = () => setMode('scale');

window.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT') return;
  const k = e.key.toLowerCase();
  if (k === 'g') setMode('translate');
  else if (k === 'r') setMode('rotate');
  else if (k === 's') setMode('scale');
  else if (k === '1') addObject('box');
  else if (k === '2') addObject('cylinder');
  else if (k === '3') addObject('sphere');
  else if (k === '4') addObject('plane');
  else if ((k === 'delete' || k === 'backspace') && selected) removeObject(selected);
  else if (k === 'escape') select(null);
});

// ---------- UI: object list ----------
function refreshList() {
  const ul = $('objlist'); ul.innerHTML = '';
  for (const o of objects) {
    const li = document.createElement('li');
    li.className = o === selected ? 'sel' : '';
    li.setAttribute('role', 'button'); li.tabIndex = 0;
    const dot = document.createElement('span'); dot.className = 'dot';
    dot.style.background = '#' + o.material.color.getHexString();
    const nm = document.createElement('span'); nm.className = 'nm'; nm.textContent = o.name;
    const del = document.createElement('button'); del.textContent = '✕';
    del.setAttribute('aria-label', o.name + ' 삭제');
    del.onclick = e => { e.stopPropagation(); removeObject(o); };
    li.append(dot, nm, del);
    li.onclick = () => select(o);
    li.onkeydown = e => { if (e.key === 'Enter') select(o); };
    ul.appendChild(li);
  }
}

// ---------- UI: properties ----------
function propRow(label, vec, step, onset) {
  const row = document.createElement('div'); row.className = 'prow';
  const lb = document.createElement('label'); lb.textContent = label; row.appendChild(lb);
  ['x', 'y', 'z'].forEach(ax => {
    const inp = document.createElement('input');
    inp.type = 'number'; inp.step = step; inp.value = (+vec[ax]).toFixed(2);
    inp.setAttribute('aria-label', `${label} ${ax}`);
    inp.onchange = () => { onset(ax, parseFloat(inp.value) || 0); };
    row.appendChild(inp);
  });
  return row;
}
function refreshProps() {
  const box = $('props');
  if (!selected) { box.innerHTML = '<div id="empty">no selection</div>'; return; }
  const active = document.activeElement;
  if (active && box.contains(active) && active.tagName === 'INPUT') {
    // don't rebuild while user edits a field; live-update values only on gizmo drag
    for (const inp of box.querySelectorAll('input[type=number]')) {
      if (inp !== active) {
        const [lab, ax] = inp.getAttribute('aria-label').split(' ');
        const src = lab === 'pos' ? selected.position : lab === 'rot' ? null : selected.scale;
        if (lab === 'rot') inp.value = THREE.MathUtils.radToDeg(selected.rotation[ax]).toFixed(1);
        else if (src) inp.value = src[ax].toFixed(2);
      }
    }
    return;
  }
  box.innerHTML = '';
  const title = document.createElement('div');
  title.style.cssText = 'font-weight:600;margin:8px 0 2px'; title.textContent = selected.name;
  box.appendChild(title);
  box.appendChild(propRow('pos', selected.position, '0.05', (ax, v) => selected.position[ax] = v));
  const rotVec = { x: THREE.MathUtils.radToDeg(selected.rotation.x), y: THREE.MathUtils.radToDeg(selected.rotation.y), z: THREE.MathUtils.radToDeg(selected.rotation.z) };
  box.appendChild(propRow('rot', rotVec, '5', (ax, v) => selected.rotation[ax] = THREE.MathUtils.degToRad(v)));
  box.appendChild(propRow('scale', selected.scale, '0.05', (ax, v) => selected.scale[ax] = v));
  const cr = document.createElement('div'); cr.className = 'prow color';
  const cl = document.createElement('label'); cl.textContent = 'color';
  const ci = document.createElement('input'); ci.type = 'color';
  ci.value = '#' + selected.material.color.getHexString();
  ci.setAttribute('aria-label', '객체 색상');
  ci.oninput = () => { selected.material.color.set(ci.value); refreshList(); };
  cr.append(cl, ci); box.appendChild(cr);
  // hex text entry (automatable color set)
  const hxR = document.createElement('div'); hxR.className = 'prow color';
  const hxL = document.createElement('label'); hxL.textContent = 'hex';
  const hx = document.createElement('input'); hx.type = 'text';
  hx.value = '#' + selected.material.color.getHexString();
  hx.setAttribute('aria-label', '색상 HEX');
  hx.style.cssText = 'background:var(--panel2);border:1px solid var(--line);color:var(--text);border-radius:6px;padding:5px 6px;font-size:12px';
  hx.onchange = () => { try { selected.material.color.set(hx.value.trim()); ci.value = '#' + selected.material.color.getHexString(); refreshList(); } catch (e) {} };
  hxR.append(hxL, hx); box.appendChild(hxR);
  // --- AI section (behavior/speed/range, per-entity, saved in scene JSON) ---
  const ai = selected.userData.ai ??= { behavior: 'static', speed: 1.1, range: 2 };
  const aiH = document.createElement('div');
  aiH.style.cssText = 'font-weight:600;margin:12px 0 2px;color:#7c6cff;font-size:12px;letter-spacing:1px';
  aiH.textContent = 'AI'; box.appendChild(aiH);
  const br = document.createElement('div'); br.className = 'prow color';
  const bl = document.createElement('label'); bl.textContent = 'behavior';
  const sel = document.createElement('select');
  sel.setAttribute('aria-label', 'AI 행동 유형');
  sel.style.cssText = 'background:var(--panel2);color:var(--text);border:1px solid var(--line);border-radius:6px;padding:4px';
  for (const b of ['static', 'patrol', 'chase']) {
    const op = document.createElement('option'); op.value = b; op.textContent = b;
    if (ai.behavior === b) op.selected = true; sel.appendChild(op);
  }
  sel.onchange = () => ai.behavior = sel.value;
  br.append(bl, sel); box.appendChild(br);
  const numRow = (label, key, obj, step, aria) => {
    const r = document.createElement('div'); r.className = 'prow color';
    const l = document.createElement('label'); l.textContent = label;
    const i = document.createElement('input'); i.type = 'number'; i.step = step; i.value = obj[key];
    i.setAttribute('aria-label', aria);
    i.onchange = () => obj[key] = parseFloat(i.value) || 0;
    r.append(l, i); box.appendChild(r);
  };
  numRow('speed', 'speed', ai, '0.1', 'AI 속도');
  numRow('range', 'range', ai, '0.5', 'AI 순찰 범위');
  // --- PHYSICS section (gravity/collider/bounce, saved in scene JSON) ---
  const phys = selected.userData.phys ??= { gravity: false, collider: true, bounce: 0 };
  const phH = document.createElement('div');
  phH.style.cssText = 'font-weight:600;margin:12px 0 2px;color:#4fd1c5;font-size:12px;letter-spacing:1px';
  phH.textContent = 'PHYSICS'; box.appendChild(phH);
  const chkRow = (label, key, aria) => {
    const r = document.createElement('div'); r.className = 'prow color';
    const l = document.createElement('label'); l.textContent = label;
    const i = document.createElement('input'); i.type = 'checkbox'; i.checked = !!phys[key];
    i.setAttribute('aria-label', aria);
    i.style.cssText = 'width:18px;height:18px;justify-self:start';
    i.onchange = () => phys[key] = i.checked;
    r.append(l, i); box.appendChild(r);
  };
  // width-profile (tumblehome) for profile objects — GUI-configurable, saved
  if (selected.userData.profile && !selected.userData.profile.lathe) {
    const wp = selected.userData.profile.widthProfile ??= { beltY: 0.9, roofFrac: 0.78, rockerFrac: 0.97 };
    const wpH = document.createElement('div');
    wpH.style.cssText = 'font-weight:600;margin:12px 0 2px;color:#ffb454;font-size:12px;letter-spacing:1px';
    wpH.textContent = 'WIDTH PROFILE'; box.appendChild(wpH);
    const rebuild = () => {
      const geo = profileGeometry(selected.userData.profile);
      applyWidthProfile(geo, wp);
      selected.geometry.dispose(); selected.geometry = geo;
    };
    const wRow = (label, key, step, aria) => {
      const r = document.createElement('div'); r.className = 'prow color';
      const l = document.createElement('label'); l.textContent = label;
      const i = document.createElement('input'); i.type = 'number'; i.step = step; i.value = wp[key];
      i.setAttribute('aria-label', aria);
      i.onchange = () => { wp[key] = parseFloat(i.value) || wp[key]; rebuild(); };
      r.append(l, i); box.appendChild(r);
    };
    wRow('beltY', 'beltY', '0.05', '벨트라인 높이');
    wRow('roofW', 'roofFrac', '0.02', '루프 폭 비율');
    wRow('rockW', 'rockerFrac', '0.01', '로커 폭 비율');
    if (wp.noseFrac === undefined) { wp.noseFrac = 1; wp.tailFrac = 1; wp.taperStart = 0.55; }
    wRow('noseW', 'noseFrac', '0.02', '노즈 폭 비율');
    wRow('tailW', 'tailFrac', '0.02', '테일 폭 비율');
    wRow('taperS', 'taperStart', '0.05', '테이퍼 시작');
  }
  // smooth-shading toggle (per-object, saved)
  const smR = document.createElement('div'); smR.className = 'prow color';
  const smL = document.createElement('label'); smL.textContent = 'smooth';
  const smI = document.createElement('input'); smI.type = 'checkbox';
  smI.checked = selected.userData.smooth !== false;
  smI.setAttribute('aria-label', '부드러운 셰이딩');
  smI.style.cssText = 'width:18px;height:18px;justify-self:start';
  smI.onchange = () => {
    selected.userData.smooth = smI.checked;
    selected.material.flatShading = !smI.checked;
    selected.material.needsUpdate = true;
    if (smI.checked) selected.geometry.computeVertexNormals();
  };
  smR.append(smL, smI); box.appendChild(smR);
  chkRow('gravity', 'gravity', '중력 적용');
  chkRow('collider', 'collider', '충돌체 적용');
  numRow('bounce', 'bounce', phys, '0.1', '탄성 계수');
  const tr = document.createElement('div'); tr.className = 'prow color';
  const tl = document.createElement('label'); tl.textContent = 'target';
  const ti = document.createElement('input'); ti.type = 'checkbox';
  ti.checked = !!selected.userData.target;
  ti.setAttribute('aria-label', '사격 타겟 지정');
  ti.style.cssText = 'width:18px;height:18px;justify-self:start';
  ti.onchange = () => {
    selected.userData.target = ti.checked;
    selected.material.emissive.set(ti.checked ? 0x5a1a1a : 0x000000);
  };
  tr.append(tl, ti); box.appendChild(tr);
}

// ---------- save / load ----------
function serialize() {
  return {
    v: 1,
    objects: serializeObjects(objects),
    spawn: spawn.toArray(),
    bgm: audio.bgmMeta,
  };
}
function clearScene() { while (objects.length) removeObject(objects[0]); }
function deserialize(data) {
  clearScene();
  counter = { box: 0, cylinder: 0, sphere: 0, plane: 0 };
  for (const d of data.objects) {
    const m = addObject(d.kind, d);
    if (d.target) { m.userData.target = true; m.material.emissive.set(0x5a1a1a); }
  }
  if (data.spawn) spawn.fromArray(data.spawn);
  if (data.bgm?.dataUrl) loadBgm(data.bgm.dataUrl, data.bgm.name);
  select(null);
}
function toast(msg) {
  const t = $('toast'); t.textContent = msg; t.classList.add('show');
  clearTimeout(toast._h); toast._h = setTimeout(() => t.classList.remove('show'), 1800);
}
$('btnSave').onclick = () => { localStorage.setItem('kong3d_scene', JSON.stringify(serialize())); toast(`saved ${objects.length} objects`); };
$('btnLoad').onclick = () => {
  const raw = localStorage.getItem('kong3d_scene');
  if (!raw) return toast('no saved scene');
  deserialize(JSON.parse(raw)); toast(`loaded ${objects.length} objects`);
};
$('btnExport').onclick = () => {
  const blob = new Blob([JSON.stringify(serialize(), null, 1)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = 'kong3d_scene.json'; a.click();
  URL.revokeObjectURL(a.href);
};
$('btnClear').onclick = () => { clearScene(); toast('cleared'); };

// ---------- resize + loop ----------
function resize() {
  const w = vp.clientWidth, h = vp.clientHeight;
  camera.aspect = w / h; camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}
new ResizeObserver(resize).observe(vp);
resize();
app.start(dt => { playTick(dt); if (!play.on) orbit.update(); renderer.render(scene, camera); });

// ---------- v0.3: audio system (engine core) ----------
const audio = new AudioSystem(camera);
const audioCtx = () => audio.context;
const sfx = k => audio.sfx(k);
const sfxAt = (k, o) => audio.sfxAt(k, o);
function loadBgm(dataUrl, name) {
  audio.loadBgm(dataUrl, name).then(() => toast(`BGM: ${name}`)).catch(() => toast('BGM decode failed'));
}
$('btnBgm').onclick = () => $('bgmFile').click();
$('bgmFile').onchange = e => {
  const f = e.target.files[0]; if (!f) return;
  if (f.size > 4 * 1024 * 1024) toast('warn: >4MB, may not persist in localStorage');
  const rd = new FileReader();
  rd.onload = () => loadBgm(rd.result, f.name);
  rd.readAsDataURL(f);
};

// reference image overlay (side blueprint, semi-transparent, behind origin)
let refPlane = null;
$('btnRef').onclick = () => {
  if (refPlane) { refPlane.visible = !refPlane.visible; return; }
  new THREE.TextureLoader().load('./refs/tesla_model_y_official_pure_side.jpg', tex => {
    const ar = tex.image.width / tex.image.height;
    const h = 4.751 / ar * 1.50; // image wider than car; scale so car-in-image ≈ real length
    refPlane = new THREE.Mesh(new THREE.PlaneGeometry(4.751 * 1.50, h),
      new THREE.MeshBasicMaterial({ map: tex, transparent: true, opacity: 0.45, depthWrite: false }));
    refPlane.position.set(0, h / 2 - h * 0.21, -1.4);
    scene.add(refPlane);
    toast('ref: side blueprint');
  });
};
// camera view presets (ortho-ish framing for 3-axis verification)
function setView(pos, look = [0, 0.8, 0]) {
  camera.position.set(...pos);
  orbit.target.set(...look);
  orbit.update();
}
$('viewSide').onclick = () => setView([0, 0.9, 9]);
$('viewFront').onclick = () => setView([-9, 0.9, 0]);
$('viewTop').onclick = () => setView([0, 10, 0.01]);
$('viewQuarter').onclick = () => setView([-5, 3.2, 6]);
// spawn point
const spawn = new THREE.Vector3(0, 1.7, 6);
$('btnSpawn').onclick = () => {
  spawn.copy(camera.position); spawn.y = Math.max(1.7, spawn.y);
  toast(`spawn @ ${spawn.x.toFixed(1)},${spawn.y.toFixed(1)},${spawn.z.toFixed(1)}`);
};

// ---------- v0.2: play mode (FPS controller) ----------
const play = {
  on: false, vel: new THREE.Vector3(), keys: {},
  yaw: 0, pitch: 0, pos: new THREE.Vector3(0, 1.7, 6),
  grounded: false, savedCam: null,
  EYE: 1.7, RADIUS: 0.35, SPEED: 5.0, JUMP: 5.2, GRAV: 14.0,
};
const playhud = document.getElementById('playhud');
const playinfo = document.getElementById('playinfo');

function enterPlay() {
  if (play.on) return;
  play.on = true;
  play.savedCam = { pos: camera.position.clone(), quat: camera.quaternion.clone() };
  document.activeElement?.blur();
  select(null); gizmo.detach(); orbit.enabled = false;
  play.pos.copy(spawn); play.vel.set(0, 0, 0); play.yaw = 0; play.pitch = 0;
  play.score = 0; updateScore();
  document.body.classList.add('playing'); playhud.hidden = false;
  renderer.domElement.requestPointerLock();
  audio.playBgm();
}
function updateScore() { document.getElementById('score').textContent = 'SCORE ' + (play.score ?? 0); }
function exitPlay() {
  if (!play.on) return;
  play.on = false;
  if (document.pointerLockElement) document.exitPointerLock();
  camera.position.copy(play.savedCam.pos); camera.quaternion.copy(play.savedCam.quat);
  orbit.enabled = true;
  document.body.classList.remove('playing'); playhud.hidden = true;
  audio.pauseBgm();
}
// shoot: click while pointer-locked = ray from camera center
renderer.domElement.addEventListener('mousedown', e => {
  if (!play.on || !document.pointerLockElement || e.button !== 0) return;
  sfx('zap');
  ray.setFromCamera(new THREE.Vector2(0, 0), camera);
  const hit = ray.intersectObjects(objects.filter(o => o.visible), false)[0];
  if (hit && hit.object.userData.target) {
    play.score = (play.score ?? 0) + 1; updateScore();
    sfxAt('ding', hit.object);
    // hit feedback: flash + shrink-pop, respawn after 1.2s
    const o = hit.object, s0 = o.scale.clone();
    o.material.emissive.set(0xff4040);
    let t0 = performance.now();
    (function pop() {
      const k = (performance.now() - t0) / 200;
      if (k < 1) { o.scale.copy(s0).multiplyScalar(1 - 0.8 * k); requestAnimationFrame(pop); }
      else { o.visible = false; setTimeout(() => { o.scale.copy(s0); o.visible = true; o.material.emissive.set(0x5a1a1a); }, 1200); }
    })();
  }
});
document.getElementById('btnPlay').onclick = () => play.on ? exitPlay() : enterPlay();
document.addEventListener('pointerlockchange', () => {
  if (!document.pointerLockElement && play.on) exitPlay();
});
document.addEventListener('mousemove', e => {
  if (!play.on || !document.pointerLockElement) return;
  play.yaw -= e.movementX * 0.0022;
  play.pitch = Math.max(-1.45, Math.min(1.45, play.pitch - e.movementY * 0.0022));
});
window.addEventListener('keydown', e => {
  if (play.on) {
    play.keys[e.code] = true;
    if (e.code === 'Escape') exitPlay();
    // tap-impulse: a single key event always yields a visible step/jump,
    // even when down+up lands within one frame (scripted/CGEvent input)
    const f = new THREE.Vector3(-Math.sin(play.yaw), 0, -Math.cos(play.yaw));
    const r = new THREE.Vector3(-f.z, 0, f.x);
    const STEP = 0.12;
    if (e.code === 'KeyW') play.pos.addScaledVector(f, STEP);
    else if (e.code === 'KeyS') play.pos.addScaledVector(f, -STEP);
    else if (e.code === 'KeyD') play.pos.addScaledVector(r, STEP);
    else if (e.code === 'KeyA') play.pos.addScaledVector(r, -STEP);
    else if (e.code === 'Space') play.jumpReq = performance.now();
  }
  else if (e.key.toLowerCase() === 'p' && e.target.tagName !== 'INPUT') enterPlay();
});
window.addEventListener('keyup', e => { play.keys[e.code] = false; });

// collision via engine physics (capsule-approx vs world AABBs)
function collide(pos) {
  play.grounded = Physics.pushOutAABB(pos, play.vel, objects,
    { eye: play.EYE, radius: play.RADIUS }) || play.grounded;
}
function playTick(dt) {
  if (!play.on) return;
  const f = new THREE.Vector3(-Math.sin(play.yaw), 0, -Math.cos(play.yaw));
  const r = new THREE.Vector3(-f.z, 0, f.x);
  const dir = new THREE.Vector3();
  if (play.keys.KeyW) dir.add(f);
  if (play.keys.KeyS) dir.sub(f);
  if (play.keys.KeyD) dir.add(r);
  if (play.keys.KeyA) dir.sub(r);
  if (dir.lengthSq()) dir.normalize().multiplyScalar(play.SPEED);
  play.vel.x = dir.x; play.vel.z = dir.z;
  play.vel.y -= play.GRAV * dt;
  const jumpAsked = play.keys.Space || (play.jumpReq && performance.now() - play.jumpReq < 300);
  if (jumpAsked && play.grounded) { play.vel.y = play.JUMP; play.grounded = false; play.jumpReq = 0; sfx('boing'); }
  play.grounded = false;
  play.pos.addScaledVector(play.vel, dt);
  collide(play.pos);
  camera.position.copy(play.pos);
  camera.quaternion.setFromEuler(new THREE.Euler(play.pitch, play.yaw, 0, 'YXZ'));
  playinfo.textContent = `pos ${play.pos.x.toFixed(1)},${play.pos.y.toFixed(1)},${play.pos.z.toFixed(1)}` +
    (play.grounded ? ' ·ground' : ' ·air') +
    ` ·♪${audioCtx().state}/${audio.lastSfx}` + (audio.bgm.isPlaying ? '·bgm' : '');
}

// verification hook (read-only state for E2E checks)
window.kong3d = {
  state: () => serialize(),
  count: () => objects.length,
  selectedName: () => selected?.name ?? null,
  mode: () => gizmo.mode,
  playing: () => play.on,
  playerPos: () => play.pos.toArray().map(v => +v.toFixed(2)),
};
