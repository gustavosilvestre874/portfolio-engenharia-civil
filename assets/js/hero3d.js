// Modelo 3D da planta do topo do site (Three.js).
// Usa as mesmas coordenadas do desenho SVG (viewBox 800 x 560): x -> x, y do SVG -> z.
// Fluxo: começa em vista de cima (igual à planta 2D), as paredes sobem enquanto a
// câmera inclina até a vista isométrica, gira devagar e o canvas some.
import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.min.js";

const W = 800, H = 560, CX = 400, CZ = 280;
const WALL_H = 120;

// Paredes: [x1, z1, x2, z2] (retângulos em planta, espessura incluída)
const WALLS = [
  [140, 130, 640, 140], [140, 460, 640, 470], [140, 140, 150, 460], [630, 140, 640, 460], // externas
  [375, 140, 385, 325],  // entre sala e cozinha
  [150, 325, 630, 335],  // corredor
  [515, 335, 525, 460],  // escada / dormitório
];
const STAIR = { x1: 535, x2: 623, z1: 345, z2: 450, steps: 7 };

export function createHero3D(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-W / 2, W / 2, H / 2, -H / 2, 1, 4000);
  const target = new THREE.Vector3(CX, 0, CZ);

  const edgeMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.85 });
  const faceMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.07, side: THREE.DoubleSide, depthWrite: false });
  const stairEdge = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.6 });
  const axisMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.2 });
  const dimMat = new THREE.LineBasicMaterial({ color: 0xf0954f, transparent: true, opacity: 0.85 });

  // Caixa com base em y = 0, escalável na altura
  const unitBox = new THREE.BoxGeometry(1, 1, 1).translate(0, 0.5, 0);
  const unitEdges = new THREE.EdgesGeometry(unitBox);
  const risers = [];
  function addBlock(x1, z1, x2, z2, height, edgeMaterial) {
    const g = new THREE.Group();
    g.add(new THREE.Mesh(unitBox, faceMat), new THREE.LineSegments(unitEdges, edgeMaterial));
    g.position.set((x1 + x2) / 2, 0, (z1 + z2) / 2);
    g.scale.set(Math.abs(x2 - x1), 0.001, Math.abs(z2 - z1));
    g.userData.height = height;
    scene.add(g);
    risers.push(g);
  }
  WALLS.forEach(([x1, z1, x2, z2]) => addBlock(x1, z1, x2, z2, WALL_H, edgeMat));
  const sw = (STAIR.x2 - STAIR.x1) / STAIR.steps;
  for (let i = 0; i < STAIR.steps; i++) {
    addBlock(STAIR.x1 + i * sw, STAIR.z1, STAIR.x1 + (i + 1) * sw, STAIR.z2, ((i + 1) / STAIR.steps) * WALL_H * 0.8, stairEdge);
  }

  // Linhas no piso: eixos e cotas (mesmas do desenho 2D)
  function floorLines(segs, mat) {
    const pts = [];
    segs.forEach(([x1, z1, x2, z2]) => pts.push(new THREE.Vector3(x1, 0.5, z1), new THREE.Vector3(x2, 0.5, z2)));
    scene.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(pts), mat));
  }
  floorLines([[140, 54, 140, 520], [380, 54, 380, 520], [640, 54, 640, 520],
              [74, 130, 730, 130], [74, 330, 730, 330], [74, 470, 730, 470]], axisMat);
  floorLines([[134, 95, 646, 95], [140, 88, 140, 120], [380, 88, 380, 120], [640, 88, 640, 120],
              [103, 124, 103, 476], [96, 130, 130, 130], [96, 330, 130, 330], [96, 470, 130, 470],
              [134, 505, 646, 505], [140, 480, 140, 512], [640, 480, 640, 512]], dimMat);
  // Piso
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(500, 340).rotateX(-Math.PI / 2),
    new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.04, depthWrite: false }));
  floor.position.set(390, 0, 300);
  scene.add(floor);

  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
  }
  new ResizeObserver(resize).observe(canvas);
  resize();

  const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  function setView(elevDeg, azDeg, zoom) {
    const el = THREE.MathUtils.degToRad(Math.min(elevDeg, 89.9));
    const az = THREE.MathUtils.degToRad(azDeg);
    const r = 1500;
    camera.position.set(CX + r * Math.cos(el) * Math.sin(az), r * Math.sin(el), CZ + r * Math.cos(el) * Math.cos(az));
    camera.up.set(0, 1, 0);
    camera.lookAt(target);
    camera.zoom = zoom;
    camera.updateProjectionMatrix();
  }
  function setRise(p) {
    risers.forEach((g) => (g.scale.y = Math.max(0.001, g.userData.height * p)));
  }

  // Estado inicial: vista de cima, sem altura (coincide com a planta 2D)
  setRise(0);
  setView(90, 0, 1);
  renderer.render(scene, camera);

  const RISE = 3400, ORBIT = 6500;
  function play(onRiseStart, onDone) {
    const t0 = performance.now();
    let started = false;
    function frame(now) {
      const t = now - t0;
      if (!started) { started = true; onRiseStart && onRiseStart(); }
      if (t < RISE) {
        const p = ease(t / RISE);
        setRise(p);
        setView(90 - 58 * p, 32 * p, 1 - 0.18 * p);
      } else {
        const q = Math.min(1, (t - RISE) / ORBIT);
        setRise(1);
        setView(32, 32 + 48 * q, 0.82);
      }
      renderer.render(scene, camera);
      if (t < RISE + ORBIT) requestAnimationFrame(frame);
      else onDone && onDone();
    }
    requestAnimationFrame(frame);
  }
  function reset() {
    setRise(0);
    setView(90, 0, 1);
    renderer.render(scene, camera);
  }
  return { play, reset };
}
