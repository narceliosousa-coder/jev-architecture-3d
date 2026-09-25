/* Visualizador Three.js da arquitetura do Jev. Consome window.SCENE (gerado pelo Python). */
(function () {
  'use strict';
  var D = window.SCENE;
  var container = document.querySelector('.plot');
  var detailBody = document.getElementById('detail-body');
  var tip = document.getElementById('tip');
  var hb = document.getElementById('hoverbtn');
  var DFAC = 1.45;                      // fator global de distancia das cameras
  var GOP = 0.96;                       // opacidade dos fantasmas na animacao
  var PH = { A: 700, B: 2300, C: 700 }; // ms: aproximar · subir/abrir · materializar
  var q = new URLSearchParams(location.search);
  var STILL = q.has('still');           // modo de captura: 1 quadro, sem sombras (verificacao headless)

  // ---------- utilitarios ----------
  function clamp01(t) { return Math.max(0, Math.min(1, t)); }
  function ease(t) { t = clamp01(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
  function easeOut(t) { t = clamp01(t); return 1 - Math.pow(1 - t, 3); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function h2r(h) { h = h.replace('#', ''); return [parseInt(h.substr(0, 2), 16), parseInt(h.substr(2, 2), 16), parseInt(h.substr(4, 2), 16)]; }
  function r2h(r) { return '#' + r.map(function (v) { v = Math.round(Math.max(0, Math.min(255, v))); return (v < 16 ? '0' : '') + v.toString(16); }).join(''); }
  function lerpHex(a, b, t) { var A = h2r(a), B = h2r(b); return r2h([lerp(A[0], B[0], t), lerp(A[1], B[1], t), lerp(A[2], B[2], t)]); }
  var colCache = {};
  function col(hex) { if (!colCache[hex]) colCache[hex] = new THREE.Color(hex).convertSRGBToLinear(); return colCache[hex]; }
  function v3(a) { return new THREE.Vector3(a[0], a[1], a[2]); }

  // ---------- renderer / cena / camera ----------
  var renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(STILL ? 1 : Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.shadowMap.enabled = !STILL;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.setClearColor(0xf7f8fa, 1);
  renderer.domElement.style.display = 'block';
  container.insertBefore(renderer.domElement, container.firstChild);

  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(42, 1, 0.5, 4000);
  camera.up.set(0, 0, 1);
  var controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.dampingFactor = 0.1; controls.screenSpacePanning = true;
  controls.minDistance = 1.5; controls.maxDistance = 500;
  controls.mouseButtons = { LEFT: THREE.MOUSE.ROTATE, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN };

  var B = D.bounds;
  var cx = (B.xmin + B.xmax) / 2, cy = (B.ymin + B.ymax) / 2;
  scene.add(new THREE.HemisphereLight(0xffffff, 0xcfd6e0, 0.62));
  var sun = new THREE.DirectionalLight(0xffffff, 0.62);
  sun.position.set(cx - 45, cy - 95, 130);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;
  sun.target.position.set(cx, cy, 8);
  var R = Math.max(B.xmax - B.xmin, B.ymax - B.ymin, B.zmax - B.zmin) * 0.75;
  sun.shadow.camera.left = -R; sun.shadow.camera.right = R; sun.shadow.camera.top = R; sun.shadow.camera.bottom = -R;
  sun.shadow.camera.near = 5; sun.shadow.camera.far = 600;
  scene.add(sun); scene.add(sun.target);
  var fill = new THREE.DirectionalLight(0xffffff, 0.18); fill.position.set(cx + 80, cy + 60, 60); scene.add(fill);

  var ground = new THREE.Mesh(new THREE.PlaneGeometry(600, 600), new THREE.MeshStandardMaterial({ color: col('#eef1f5'), roughness: 1, metalness: 0 }));
  ground.position.set(cx, cy, B.zmin - 0.06); ground.receiveShadow = true; scene.add(ground);

  var layers = { main: new THREE.Group(), exp: new THREE.Group() };
  scene.add(layers.main); scene.add(layers.exp);
  layers.exp.visible = false;

  var pick = [];        // objetos com hover
  var sprites = [];     // rotulos (escala em pixels)
  var byGroup = {};     // legenda -> objetos
  var expMats = [];     // materiais da regiao expandida (fade)
  function reg(g, obj) { if (!g) return; (byGroup[g] = byGroup[g] || []).push(obj); obj.userData.g = g; }

  // ---------- materiais ----------
  var matCache = {};
  function mat(hex, o, layer) {
    var k = layer + '|' + hex + '|' + o;
    if (!matCache[k]) {
      var m = new THREE.MeshStandardMaterial({ color: col(hex), roughness: 0.88, metalness: 0.0, transparent: o < 1, opacity: o });
      m.userData.baseOpacity = o;
      if (layer === 'exp') expMats.push(m);
      matCache[k] = m;
    }
    return matCache[k];
  }

  // ---------- primitivas ----------
  var unitBox = new THREE.BoxGeometry(1, 1, 1);
  var cylGeo = new THREE.CylinderGeometry(1, 1, 1, 10, 1);
  var coneGeo = new THREE.ConeGeometry(1, 1, 16);
  var sphereGeo = new THREE.SphereGeometry(1, 18, 12);
  var diamondGeo = new THREE.OctahedronGeometry(1, 0);
  var UP = new THREE.Vector3(0, 1, 0);

  function addBox(p) {
    var b = p.b;
    var m = new THREE.Mesh(unitBox, mat(p.c, p.o, p.L));
    m.position.set((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2);
    m.scale.set(Math.max(b[1] - b[0], 0.02), Math.max(b[3] - b[2], 0.02), Math.max(b[5] - b[4], 0.02));
    m.castShadow = p.o >= 0.5 && (b[5] - b[4]) > 0.1;
    m.receiveShadow = true;
    m.userData.h = p.h; m.userData.n = p.n;
    layers[p.L].add(m);
    if (p.h) pick.push(m);
    reg(p.g, m);
  }

  function addCubes(p) {
    var n = p.cells.length; if (!n) return;
    var material = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.9, metalness: 0, transparent: p.o < 1, opacity: p.o });
    material.userData.baseOpacity = p.o;
    if (p.L === 'exp') expMats.push(material);
    var im = new THREE.InstancedMesh(unitBox, material, n);
    var M = new THREE.Matrix4(), q = new THREE.Quaternion(), pos = new THREE.Vector3(), scl = new THREE.Vector3();
    var colors = [];
    for (var i = 0; i < n; i++) {
      var c = p.cells[i];
      pos.set((c[0] + c[1]) / 2, (c[2] + c[3]) / 2, (c[4] + c[5]) / 2);
      scl.set(c[1] - c[0], c[3] - c[2], c[5] - c[4]);
      M.compose(pos, q, scl); im.setMatrixAt(i, M);
      var cc = col(c[6]); im.setColorAt(i, cc); colors.push(cc);
    }
    im.instanceMatrix.needsUpdate = true;
    if (im.instanceColor) im.instanceColor.needsUpdate = true;
    im.castShadow = true; im.receiveShadow = true;
    im.userData.cells = p.cells; im.userData.colors = colors;
    layers[p.L].add(im); pick.push(im); reg(p.g, im);
  }

  function makeText(text, sz, color, bold) {
    var dpr = 2, pad = 6;
    var font = (bold ? '700 ' : '500 ') + (sz * dpr) + 'px "Segoe UI", "Helvetica Neue", Arial, sans-serif';
    var c = document.createElement('canvas'); var ctx = c.getContext('2d');
    ctx.font = font;
    var w = Math.ceil(ctx.measureText(text).width) + pad * 2 * dpr, h = Math.ceil(sz * dpr * 1.4);
    c.width = w; c.height = h;
    ctx.font = font; ctx.textBaseline = 'middle'; ctx.fillStyle = color;
    ctx.fillText(text, pad * dpr, h / 2 + sz * dpr * 0.04);
    var tex = new THREE.CanvasTexture(c);
    tex.encoding = THREE.sRGBEncoding; tex.minFilter = THREE.LinearFilter; tex.generateMipmaps = false;
    return { tex: tex, pxW: w / dpr, pxH: h / dpr };
  }
  function addLabel(p) {
    var t = makeText(p.s, p.sz, p.c, p.b);
    var sm = new THREE.SpriteMaterial({ map: t.tex, transparent: true, depthTest: true, depthWrite: false, sizeAttenuation: false });
    sm.userData.baseOpacity = 1;
    var sp = new THREE.Sprite(sm);
    sp.position.set(p.p[0], p.p[1], p.p[2]);
    sp.userData.pxW = t.pxW; sp.userData.pxH = t.pxH; sp.userData.sz = p.sz;
    sp.renderOrder = 10;
    sprites.push(sp); layers[p.L].add(sp);
    if (p.L === 'exp') expMats.push(sm);
  }
  function updateSpriteScales() {
    var H = renderer.domElement.clientHeight || 1;
    var k = 2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) / H;
    for (var i = 0; i < sprites.length; i++) { var sp = sprites[i]; sp.scale.set(sp.userData.pxW * k, sp.userData.pxH * k, 1); }
  }
  var lastLod = -1;
  function updateLabelLod() { // rotulos pequenos somem quando a camera esta longe
    var d = camera.position.distanceTo(controls.target);
    var lod = d > 95 ? 2 : (d > 55 ? 1 : 0);
    if (lod === lastLod) return; lastLod = lod;
    for (var i = 0; i < sprites.length; i++) { var sz = sprites[i].userData.sz || 11; sprites[i].visible = lod === 0 || (lod === 1 && sz > 8) || (lod === 2 && sz > 9.5); }
  }

  function addSegment(a, b, r, material, layer, hover) {
    var A = v3(a), Bv = v3(b), d = new THREE.Vector3().subVectors(Bv, A), len = d.length();
    if (len < 1e-6) return null;
    var m = new THREE.Mesh(cylGeo, material);
    m.position.copy(A).addScaledVector(d, 0.5);
    m.scale.set(r, len, r);
    m.quaternion.setFromUnitVectors(UP, d.clone().normalize());
    layers[layer].add(m);
    if (hover) { m.userData.h = hover; pick.push(m); }
    return m;
  }
  function addLine(p) {
    var r = 0.026 * p.w + 0.02, material = mat(p.c, 1, p.L);
    for (var i = 0; i < p.pts.length - 1; i++) {
      if (p.d) {
        var A = v3(p.pts[i]), Bv = v3(p.pts[i + 1]), L = A.distanceTo(Bv), dash = 0.3, gap = 0.18, s = 0;
        while (s < L) { var e = Math.min(L, s + dash); addSegment(A.clone().lerp(Bv, s / L).toArray(), A.clone().lerp(Bv, e / L).toArray(), r, material, p.L, p.h); s = e + gap; }
      } else addSegment(p.pts[i], p.pts[i + 1], r, material, p.L, p.h);
    }
  }
  function addArrow(p) {
    var r = 0.026 * p.w + 0.02, material = mat(p.c, 1, p.L);
    var A = v3(p.p0), Bv = v3(p.p1), d = new THREE.Vector3().subVectors(Bv, A), len = d.length();
    if (len < 1e-6) return;
    var dir = d.clone().normalize();
    var hl = Math.min(len * 0.6, 0.3 + p.hd * 0.7), hr = Math.max(r * 2.2, 0.08 + p.hd * 0.32);
    addSegment(A.toArray(), Bv.clone().addScaledVector(dir, -hl).toArray(), r, material, p.L, p.h);
    var cone = new THREE.Mesh(coneGeo, material);
    cone.position.copy(Bv).addScaledVector(dir, -hl / 2);
    cone.scale.set(hr, hl, hr);
    cone.quaternion.setFromUnitVectors(UP, dir);
    layers[p.L].add(cone);
    if (p.h) { cone.userData.h = p.h; pick.push(cone); }
  }
  function heatColor(v) {
    if (v <= 0.001) return '#f3f5f8';
    if (v < 0.35) return lerpHex('#f3f5f8', '#9fb3c8', v / 0.35);
    return lerpHex('#9fb3c8', '#14365d', (v - 0.35) / 0.65);
  }
  function addHeat(p) {
    var w = p.w, ny = w.length, nx = w[0].length, S = 28;
    var c = document.createElement('canvas'); c.width = nx * S; c.height = ny * S;
    var ctx = c.getContext('2d');
    for (var r = 0; r < ny; r++) for (var q = 0; q < nx; q++) {
      ctx.fillStyle = heatColor(w[r][q]);
      ctx.fillRect(q * S, (ny - 1 - r) * S, S, S);
    }
    ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2;
    for (var i = 0; i <= nx; i++) { ctx.beginPath(); ctx.moveTo(i * S, 0); ctx.lineTo(i * S, ny * S); ctx.stroke(); }
    for (var j = 0; j <= ny; j++) { ctx.beginPath(); ctx.moveTo(0, j * S); ctx.lineTo(nx * S, j * S); ctx.stroke(); }
    var tex = new THREE.CanvasTexture(c); tex.encoding = THREE.sRGBEncoding; tex.anisotropy = 4;
    var m = new THREE.Mesh(new THREE.PlaneGeometry(p.x1 - p.x0, p.y1 - p.y0),
      new THREE.MeshStandardMaterial({ map: tex, roughness: 0.9, metalness: 0, side: THREE.DoubleSide }));
    m.position.set((p.x0 + p.x1) / 2, (p.y0 + p.y1) / 2, p.z);
    m.receiveShadow = true; m.userData.h = p.h;
    layers[p.L].add(m); pick.push(m);
  }
  function addPoints(p) {
    var material = mat(p.c, 1, p.L), r = 0.03 * p.sz + 0.06;
    p.pts.forEach(function (pt) {
      var m = new THREE.Mesh(p.sym === 'diamond' ? diamondGeo : sphereGeo, material);
      m.position.set(pt[0], pt[1], pt[2]);
      if (p.sym === 'diamond') m.scale.set(r * 0.85, r * 0.85, r * 1.35); else m.scale.setScalar(r);
      m.castShadow = true;
      if (p.h) { m.userData.h = p.h; pick.push(m); }
      layers[p.L].add(m);
    });
  }

  D.prims.forEach(function (p) {
    switch (p.t) {
      case 'box': addBox(p); break;
      case 'cubes': addCubes(p); break;
      case 'label': addLabel(p); break;
      case 'line': addLine(p); break;
      case 'arrow': addArrow(p); break;
      case 'heat': addHeat(p); break;
      case 'points': addPoints(p); break;
    }
  });

  // ---------- camera: vistas e voos ----------
  function camFromView(v) {
    var az = THREE.MathUtils.degToRad(v.az), el = THREE.MathUtils.degToRad(v.el), d = v.d * DFAC;
    return { pos: new THREE.Vector3(v.tg[0] + d * Math.cos(el) * Math.cos(az), v.tg[1] + d * Math.cos(el) * Math.sin(az), v.tg[2] + d * Math.sin(el)), tg: v3(v.tg) };
  }
  function setCam(c) { camera.position.copy(c.pos); controls.target.copy(c.tg); camera.lookAt(c.tg); }
  var fly = null;
  function flyTo(v, ms, done) {
    var to = camFromView(v);
    fly = { p0: camera.position.clone(), t0: controls.target.clone(), p1: to.pos, t1: to.tg, start: null, ms: ms || 1000, done: done };
  }
  function stepFly(now) {
    if (!fly) return;
    if (fly.start === null) fly.start = now;
    var u = clamp01((now - fly.start) / fly.ms), e = ease(u);
    camera.position.lerpVectors(fly.p0, fly.p1, e);
    controls.target.lerpVectors(fly.t0, fly.t1, e);
    camera.lookAt(controls.target);
    if (u >= 1) { var d = fly.done; fly = null; if (d) d(); }
  }

  // ---------- hover / tooltip ----------
  var ray = new THREE.Raycaster(); var ndc = new THREE.Vector2(); var mouse = { x: 0, y: 0, inside: false };
  var needPick = false, hovered = null, hoveredId = -1, savedMat = null;
  renderer.domElement.addEventListener('pointermove', function (e) {
    var r = renderer.domElement.getBoundingClientRect();
    mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top; mouse.inside = true;
    ndc.set((mouse.x / r.width) * 2 - 1, -(mouse.y / r.height) * 2 + 1);
    needPick = true;
  });
  renderer.domElement.addEventListener('pointerleave', function () { mouse.inside = false; clearHover(); });
  function visibleUp(o) { while (o) { if (!o.visible) return false; o = o.parent; } return true; }
  function clearHover() {
    if (hovered) {
      if (hovered.isInstancedMesh) { if (hoveredId >= 0) { hovered.setColorAt(hoveredId, hovered.userData.colors[hoveredId]); hovered.instanceColor.needsUpdate = true; } }
      else if (savedMat) { hovered.material = savedMat; }
    }
    hovered = null; hoveredId = -1; savedMat = null;
    tip.style.display = 'none';
  }
  var hiCache = {};
  function hiMaterial(m) {
    var k = m.uuid;
    if (!hiCache[k]) { var c = m.clone(); c.emissive = new THREE.Color(0xffffff); c.emissiveIntensity = 0.18; hiCache[k] = c; }
    return hiCache[k];
  }
  var CARDMAP = (D.cardmap || []).map(function (e) { return [new RegExp(e[0]), e[1]]; });
  function cardIdFor(txt) { if (!txt) return null; var t = String(txt); for (var i = 0; i < CARDMAP.length; i++) if (CARDMAP[i][0].test(t)) return CARDMAP[i][1]; return null; }
  function openCard(cid) {
    var el = document.getElementById('card-' + cid); if (!el) return false;
    var all = document.querySelectorAll('.item'); for (var i = 0; i < all.length; i++) all[i].classList.remove('active');
    el.classList.add('active'); el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash');
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return true;
  }
  function hoverTextOf(obj, id) {
    if (obj.isInstancedMesh) { var c = obj.userData.cells[id]; return c ? c[7] : null; }
    return obj.userData.h || null;
  }
  function doPick() {
    needPick = false;
    if (anim) return;
    ray.setFromCamera(ndc, camera);
    var cand = [];
    for (var i = 0; i < pick.length; i++) if (visibleUp(pick[i])) cand.push(pick[i]);
    var hits = ray.intersectObjects(cand, false);
    if (!hits.length) { clearHover(); scheduleHideBtn(900); return; }
    var h = hits[0], obj = h.object, id = (h.instanceId !== undefined) ? h.instanceId : -1;
    if (obj !== hovered || id !== hoveredId) {
      clearHover();
      hovered = obj; hoveredId = id;
      if (obj.isInstancedMesh && id >= 0) { var base = obj.userData.colors[id]; obj.setColorAt(id, base.clone().lerp(new THREE.Color(1, 1, 1), 0.45)); obj.instanceColor.needsUpdate = true; }
      else { savedMat = obj.material; obj.material = hiMaterial(obj.material); }
    }
    var txt = hoverTextOf(obj, id);
    if (txt) {
      var cid = cardIdFor(txt);
      tip.innerHTML = txt + (cid ? '<div class="tiphint">clique para abrir o card no guia de estudo →</div>' : ''); tip.style.display = 'block';
      var W = container.clientWidth, Hh = container.clientHeight;
      var left = mouse.x + 16, top = mouse.y + 18;
      if (left + tip.offsetWidth > W - 8) left = mouse.x - tip.offsetWidth - 12;
      if (top + tip.offsetHeight > Hh - 8) top = mouse.y - tip.offsetHeight - 12;
      tip.style.left = left + 'px'; tip.style.top = top + 'px';
      detailBody.innerHTML = txt;
      if (String(txt).indexOf('Bloco 1 ·') >= 0 && !expanded) showHoverBtn(); else scheduleHideBtn(900);
    } else { tip.style.display = 'none'; }
  }
  var downAt = null;
  renderer.domElement.addEventListener('pointerdown', function (e) { downAt = { x: e.clientX, y: e.clientY }; });
  renderer.domElement.addEventListener('click', function (e) {
    if (downAt && (Math.abs(e.clientX - downAt.x) > 4 || Math.abs(e.clientY - downAt.y) > 4)) return; // foi arrasto, nao clique
    if (!hovered) return;
    var t = hoverTextOf(hovered, hoveredId); if (!t) return;
    detailBody.innerHTML = t;
    if (String(t).indexOf('Bloco 1 ·') >= 0 && !expanded) showHoverBtn();
    var cid = cardIdFor(t); if (cid) openCard(cid);
  });

  // ---------- botao flutuante do Bloco 1 ----------
  var hbTimer = null;
  function showHoverBtn() {
    if (expanded || anim) return;
    clearTimeout(hbTimer);
    var left = Math.min(mouse.x + 18, container.clientWidth - 280);
    hb.style.left = left + 'px'; hb.style.top = Math.max(6, mouse.y - 64) + 'px'; hb.style.display = 'block';
  }
  function hideHoverBtn() { hb.style.display = 'none'; }
  function scheduleHideBtn(ms) { clearTimeout(hbTimer); hbTimer = setTimeout(hideHoverBtn, ms); }
  hb.addEventListener('mouseenter', function () { clearTimeout(hbTimer); });
  hb.addEventListener('mouseleave', function () { scheduleHideBtn(400); });
  hb.addEventListener('click', function () { hideHoverBtn(); animate(true); });

  // ---------- regiao expandida: fantasmas e animacao ----------
  var expanded = false, anim = null;
  var CB1 = camFromView(D.cams.b1), CEX = camFromView(D.cams.exp), CBL = camFromView(D.cams.blocks);
  function grow(b, f) { var mx = (b[0] + b[1]) / 2, my = (b[2] + b[3]) / 2, mz = (b[4] + b[5]) / 2; return [mx + (b[0] - mx) * f, mx + (b[1] - mx) * f, my + (b[2] - my) * f, my + (b[3] - my) * f, mz + (b[4] - mz) * f, mz + (b[5] - mz) * f]; }
  function lerpBox(a, b, tz, txy) { return [lerp(a[0], b[0], txy), lerp(a[1], b[1], txy), lerp(a[2], b[2], txy), lerp(a[3], b[3], txy), lerp(a[4], b[4], tz), lerp(a[5], b[5], tz)]; }
  var ghosts = D.ghosts.map(function (g) {
    var m = new THREE.Mesh(unitBox, new THREE.MeshStandardMaterial({ color: col(g.c0), roughness: 0.8, metalness: 0, transparent: true, opacity: 0 }));
    m.visible = false; m.castShadow = true; m.renderOrder = 5; scene.add(m);
    return { g: g, m: m, src: grow(g.src, 1.05) };
  });
  var STAG = ghosts.map(function (_, i) { return 0.22 * i / Math.max(1, ghosts.length - 1); });
  function setGhost(gh, b, hex, op) {
    gh.m.position.set((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2);
    gh.m.scale.set(Math.max(b[1] - b[0], 0.02), Math.max(b[3] - b[2], 0.02), Math.max(b[5] - b[4], 0.02));
    gh.m.material.color.copy(col(hex)); gh.m.material.opacity = op; gh.m.visible = op > 0.01;
  }
  function morph(p, op) {
    ghosts.forEach(function (gh, i) {
      var q = clamp01((p - STAG[i]) / 0.78);
      var tz = ease(q / 0.62), txy = ease((q - 0.3) / 0.7);
      setGhost(gh, lerpBox(gh.src, gh.g.dst, tz, txy), lerpHex(gh.g.c0, gh.g.c1, ease(q)), op);
    });
  }
  function hideGhosts() { ghosts.forEach(function (gh) { gh.m.visible = false; }); }
  function setExpOpacity(t) {
    layers.exp.visible = t > 0.001;
    for (var i = 0; i < expMats.length; i++) { var m = expMats[i]; var bo = m.userData.baseOpacity; m.opacity = bo * t; m.transparent = m.isSpriteMaterial ? true : ((t < 1) || bo < 1); }
  }
  function camLerp(a, b, t) { camera.position.lerpVectors(a.pos, b.pos, t); controls.target.lerpVectors(a.tg, b.tg, t); camera.lookAt(controls.target); }
  function renderForward(u, camStart) {
    var T = PH.A + PH.B + PH.C, t = u * T, p;
    if (t < PH.A) { p = ease(t / PH.A); camLerp(camStart, CB1, p); morph(0, GOP * easeOut(p)); return 'A'; }
    t -= PH.A;
    if (t < PH.B) { p = t / PH.B; morph(p, GOP); camLerp(CB1, CEX, ease(p)); return 'B'; }
    t -= PH.B;
    p = ease(clamp01(t / PH.C)); morph(1, GOP * (1 - p)); setExpOpacity(p); camLerp(CEX, CEX, 1); return 'C';
  }
  function renderBackward(u, camStart) {
    var T = PH.C + PH.B + PH.A, t = u * T, p;
    if (t < PH.C) { p = ease(t / PH.C); morph(1, GOP * p); setExpOpacity(1 - p); camLerp(camStart, CEX, p); return 'C'; }
    t -= PH.C;
    if (t < PH.B) { p = t / PH.B; morph(1 - p, GOP); camLerp(CEX, CB1, ease(p)); return 'B'; }
    t -= PH.B;
    p = ease(clamp01(t / PH.A)); morph(0, GOP * (1 - p)); camLerp(CB1, CBL, p); return 'A';
  }
  function animate(forward, done) {
    if (anim || forward === expanded) { if (done) done(); return; }
    hideHoverBtn(); clearHover(); fly = null; controls.enabled = false;
    anim = { forward: forward, start: null, camStart: { pos: camera.position.clone(), tg: controls.target.clone() }, done: done, total: PH.A + PH.B + PH.C };
  }
  function stepAnim(now) {
    if (!anim) return;
    if (anim.start === null) anim.start = now;
    var u = clamp01((now - anim.start) / anim.total);
    if (anim.forward) renderForward(u, anim.camStart); else renderBackward(u, anim.camStart);
    if (u >= 1) {
      hideGhosts(); expanded = anim.forward; setExpOpacity(expanded ? 1 : 0);
      controls.enabled = true; var d = anim.done; anim = null; setExpButtons(); if (d) d();
    }
  }
  function setExpButtons() {
    document.querySelectorAll('.do-expand').forEach(function (b) { b.disabled = expanded; });
    document.querySelectorAll('.do-collapse').forEach(function (b) { b.disabled = !expanded; });
  }

  // ---------- UI ----------
  document.querySelectorAll('.viewbtn').forEach(function (b) {
    b.addEventListener('click', function () { if (anim) return; flyTo(JSON.parse(b.getAttribute('data-view')), 1000); });
  });
  document.querySelectorAll('.do-expand').forEach(function (b) { b.addEventListener('click', function () { animate(true); }); });
  document.querySelectorAll('.do-collapse').forEach(function (b) { b.addEventListener('click', function () { animate(false); }); });
  var items = document.querySelectorAll('.item[data-cam]');
  items.forEach(function (it) {
    it.querySelector('button.focus').addEventListener('click', function () {
      var cam = JSON.parse(it.getAttribute('data-cam'));
      items.forEach(function (o) { o.classList.remove('active'); }); it.classList.add('active');
      detailBody.innerHTML = '<b>' + it.querySelector('.t').textContent + '</b>' + it.querySelector('.d').textContent;
      if (it.getAttribute('data-exp') === '1' && !expanded) animate(true, function () { flyTo(cam, 900); });
      else if (!anim) flyTo(cam, 1000);
    });
  });
  function setMore(btn, open) {
    var box = btn.nextElementSibling; if (!box) return;
    box.hidden = !open; btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.textContent = open ? 'Saber menos ▴' : 'Saber mais ▾';
  }
  document.querySelectorAll('.more-btn').forEach(function (btn) {
    btn.addEventListener('click', function () { setMore(btn, btn.getAttribute('aria-expanded') !== 'true'); });
  });
  var allOpen = document.getElementById('more-all-open'), allClose = document.getElementById('more-all-close');
  if (allOpen) allOpen.addEventListener('click', function () { document.querySelectorAll('.more-btn').forEach(function (b) { setMore(b, true); }); });
  if (allClose) allClose.addEventListener('click', function () { document.querySelectorAll('.more-btn').forEach(function (b) { setMore(b, false); }); });
  document.querySelectorAll('.lg[data-g]').forEach(function (el) {
    el.addEventListener('click', function () {
      var g = el.getAttribute('data-g'), list = byGroup[g] || [];
      var on = el.classList.toggle('off');
      list.forEach(function (o) { o.visible = !on; });
    });
  });
  setExpButtons();

  // ---------- resize ----------
  function resize() {
    var w = container.clientWidth || 800, h = container.clientHeight || 600;
    renderer.setSize(w, h, false);
    renderer.domElement.style.width = w + 'px'; renderer.domElement.style.height = h + 'px';
    camera.aspect = w / h; camera.updateProjectionMatrix();
    updateSpriteScales();
  }
  window.addEventListener('resize', resize);
  if (window.ResizeObserver) new ResizeObserver(resize).observe(container);
  resize();

  // ---------- estado inicial / depuracao por URL ----------
  setCam(camFromView(D.views[0][1]));
  if (q.has('view')) { var vi = parseInt(q.get('view'), 10); if (D.views[vi]) setCam(camFromView(D.views[vi][1])); }
  if (q.has('exp')) { setExpOpacity(1); expanded = true; setExpButtons(); if (q.has('cam') && D.cams[q.get('cam')]) setCam(camFromView(D.cams[q.get('cam')])); }
  if (q.has('anim')) {
    var u0 = parseFloat(q.get('anim')), dir = q.get('dir') || 'fwd';
    if (dir === 'fwd') { setExpOpacity(0); expanded = false; renderForward(u0, CBL); }
    else { setExpOpacity(1); expanded = true; renderBackward(u0, CEX); }
  }
  if (q.has('dist')) DFAC = parseFloat(q.get('dist')) || 1.0;

  // ---------- loop ----------
  function loop(now) {
    requestAnimationFrame(loop);
    if (anim) stepAnim(now);
    else { stepFly(now); if (!fly) controls.update(); }
    if (needPick) doPick();
    updateLabelLod();
    renderer.render(scene, camera);
  }
  if (STILL) { updateSpriteScales(); updateLabelLod(); renderer.render(scene, camera); } else requestAnimationFrame(loop);
  window.JEV = { flyTo: flyTo, animate: animate, camera: camera, controls: controls, scene: scene };
})();
