import React, {useEffect, useMemo, useState} from 'react';
import {
  AbsoluteFill, Audio, Easing, interpolate, random, Sequence, staticFile,
  useCurrentFrame, continueRender, delayRender,
} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';
import * as THREE from 'three';
import '@fontsource/lalezar';
import '@fontsource/ibm-plex-sans-arabic/400.css';
import '@fontsource/ibm-plex-sans-arabic/600.css';
import '@fontsource/ibm-plex-sans-arabic/700.css';
import TL from './timeline.json';

const FPS = 30;
const W = 1920, H = 1080;
export const TOTAL = Math.ceil(TL.total * FPS);
const SC = TL.scenes as Record<string, [number, number]>;
const LINES = TL.lines as {scene: string; text: string; file: string; dur: number; start: number}[];
const lineOf = (scene: string, k: number) => LINES.filter((l) => l.scene === scene)[k];

const DISPLAY = 'Lalezar';
const BODY = '"IBM Plex Sans Arabic"';
const C = {cyan: '#4fd1ff', gold: '#ffc857', orange: '#ff7a1a', text: '#f4f7fb', blue: '#3b82f6', gray: '#9aa3ad', red: '#ff4d4d'};

// ---------- helpers ----------
const ease = Easing.inOut(Easing.cubic);
const p = (t: number, a: number, b: number, e = ease) =>
  interpolate(t, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: e});
const win = (t: number, a: number, b: number, fade = 0.5) => Math.min(p(t, a, a + fade), 1 - p(t, b - fade, b));
const PI = Math.PI;

// ---------- engine geometry constants ----------
const CYL_X = [-1.8, -0.6, 0.6, 1.8];
const BORE = 0.43;
const R = 0.35;          // crank radius
const ROD = 1.25;        // rod length
const CRANK_Y = -1.6;
const DECK = 0.55;       // top of cylinder / bottom of head
const PISTON_H = 0.5;
const PIN_TO_TOP = 0.3;
// firing order 1-3-4-2 → phase offsets within the 720° cycle
const PHASE = [0, 3 * PI, PI, 2 * PI];
const THROW = [0, PI, PI, 0];

const cyclePhase = (phi: number, i: number) => {
  const x = (phi - PHASE[i]) % (4 * PI);
  return x < 0 ? x + 4 * PI : x;
};
const pistonPinY = (a: number) => CRANK_Y + R * Math.cos(a) + Math.sqrt(ROD * ROD - (R * Math.sin(a)) ** 2);

// ---------- timeline-driven state ----------
const L = (s: string, k: number) => lineOf(s, k);
const strokeSpan = (s: string): [number, number] => {
  const l = L(s, 1);
  return [l.start - 0.2, l.start + l.dur - 0.3];
};
const crankAngle = (t: number) => {
  const [h0, h1] = SC.hook;
  if (t < SC.parts[0]) return 8 * PI * p(t, h0 + 0.3, h1 - 0.6, Easing.inOut(Easing.sin));
  if (t < SC.intake[0]) return 8 * PI;
  const strokes: [string, number][] = [['intake', 8], ['compress', 9], ['power', 10], ['exhaust', 11]];
  for (const [s, base] of strokes) {
    if (t < SC[s][1]) {
      const [a, b] = strokeSpan(s);
      const e = s === 'power' ? Easing.out(Easing.cubic) : ease;
      return (base + p(t, a, b, e)) * PI;
    }
  }
  // cycle + fact: accelerate
  const t0 = SC.cycle[0];
  const dt = t - t0;
  const w0 = 1.5, w1 = 16, ramp = 9;
  const k = Math.min(dt, ramp);
  let ang = w0 * k + (w1 - w0) * k * k / (2 * ramp);
  if (dt > ramp) ang += w1 * (dt - ramp);
  return 12 * PI + ang;
};

// ---------- camera ----------
type V3 = [number, number, number];
type Key = {t: number; pos: V3; tgt: V3};
const orbit = (ang: number, r: number, y: number, tgt: V3 = [0, 0, 0]): V3 => [tgt[0] + Math.sin(ang) * r, y, tgt[2] + Math.cos(ang) * r];
const FOCUS: V3 = [-0.75, 0.25, 0];
const KEYS: Key[] = [
  {t: 0, pos: orbit(-0.9, 13, 4.5), tgt: [0, -0.3, 0]},
  {t: SC.hook[1] - 1, pos: orbit(0.55, 10.5, 3.2), tgt: [0, -0.3, 0]},
  {t: SC.parts[0] + 1.6, pos: [3.2, 1.6, 12.6], tgt: [0, 0.2, 0]},
  {t: SC.parts[1] - 0.8, pos: [1.6, 1.9, 12.2], tgt: [0, 0.3, 0]},
  {t: SC.intake[0] + 1.6, pos: [FOCUS[0] + 1.6, 1.0, 7.4], tgt: FOCUS},
  {t: SC.exhaust[1] - 0.8, pos: [FOCUS[0] + 0.9, 0.8, 7.0], tgt: FOCUS},
  {t: SC.cycle[0] + 2.0, pos: orbit(0.7, 10.5, 3.6), tgt: [0, -0.2, 0]},
  {t: SC.cycle[1], pos: orbit(0.25, 10.5, 3.2), tgt: [0, -0.4, 0]},
  {t: SC.fact[0] + 6, pos: orbit(-0.45, 9.5, 2.6), tgt: [0, -0.3, 0]},
  {t: TL.total, pos: orbit(-0.8, 12, 4.0), tgt: [0, -0.3, 0]},
];
const camAt = (t: number) => {
  let i = 0;
  while (i < KEYS.length - 2 && t > KEYS[i + 1].t) i++;
  const a = KEYS[i], b = KEYS[i + 1];
  const k = p(t, a.t, b.t);
  const lerp = (u: V3, v: V3): V3 => [u[0] + (v[0] - u[0]) * k, u[1] + (v[1] - u[1]) * k, u[2] + (v[2] - u[2]) * k];
  return {pos: lerp(a.pos, b.pos), tgt: lerp(a.tgt, b.tgt)};
};
const FOV = 32;
const projCam = new THREE.PerspectiveCamera(FOV, W / H, 0.1, 100);
const project = (v: V3, cam: {pos: V3; tgt: V3}) => {
  projCam.position.set(...cam.pos);
  projCam.lookAt(...cam.tgt);
  projCam.updateMatrixWorld();
  const q = new THREE.Vector3(...v).project(projCam);
  return [(q.x + 1) / 2 * W, (1 - q.y) / 2 * H] as const;
};

// ---------- three components ----------
const Rig: React.FC<{pos: V3; tgt: V3}> = ({pos, tgt}) => {
  const {camera, gl, scene} = useThree();
  useMemo(() => {
    gl.toneMapping = THREE.NoToneMapping;
  }, [gl, scene]);
  const c = camera as THREE.PerspectiveCamera;
  c.fov = FOV; c.near = 0.1; c.far = 100; c.updateProjectionMatrix();
  c.position.set(...pos); c.lookAt(...tgt);
  return null;
};

// procedural studio matcaps: chrome-like shading without costly PBR environment sampling
const makeMatcap = (soft: boolean) => {
  const S = 512, cv = document.createElement('canvas');
  cv.width = cv.height = S;
  const g = cv.getContext('2d')!;
  const sky = g.createLinearGradient(0, 0, 0, S);
  if (soft) { sky.addColorStop(0, '#ffffff'); sky.addColorStop(0.55, '#d9dde2'); sky.addColorStop(1, '#6b7380'); }
  else { sky.addColorStop(0, '#f4f8fc'); sky.addColorStop(0.42, '#9aa6b4'); sky.addColorStop(0.5, '#2b3139'); sky.addColorStop(0.62, '#59626e'); sky.addColorStop(1, '#14181d'); }
  g.fillStyle = sky; g.fillRect(0, 0, S, S);
  const hl = g.createRadialGradient(S * 0.34, S * 0.26, 0, S * 0.34, S * 0.26, S * 0.28);
  hl.addColorStop(0, 'rgba(255,255,255,0.95)'); hl.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = hl; g.fillRect(0, 0, S, S);
  const rim = g.createRadialGradient(S / 2, S / 2, S * 0.36, S / 2, S / 2, S * 0.5);
  rim.addColorStop(0, 'rgba(90,180,255,0)'); rim.addColorStop(1, soft ? 'rgba(160,200,255,0.35)' : 'rgba(90,190,255,0.75)');
  g.fillStyle = rim; g.fillRect(0, 0, S, S);
  const warm = g.createRadialGradient(S * 0.75, S * 0.8, 0, S * 0.75, S * 0.8, S * 0.3);
  warm.addColorStop(0, 'rgba(255,170,90,0.35)'); warm.addColorStop(1, 'rgba(255,170,90,0)');
  g.fillStyle = warm; g.fillRect(0, 0, S, S);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
};
const MC = makeMatcap(false), MCS = makeMatcap(true);
const mc = (color: string, soft = false) => new THREE.MeshMatcapMaterial({matcap: soft ? MCS : MC, color});
const mat = {
  steel: mc('#eef2f6'),
  dark: mc('#8c949d'),
  alu: mc('#f2f4f7', true),
  ring: mc('#3c4249'),
  ceramic: mc('#ffffff', true),
  copper: mc('#e0985a'),
};

// cylinder oriented between two points
const Tube: React.FC<{a: V3; b: V3; r: number; material: THREE.Material}> = ({a, b, r, material}) => {
  const va = new THREE.Vector3(...a), vb = new THREE.Vector3(...b);
  const mid = va.clone().add(vb).multiplyScalar(0.5);
  const dir = vb.clone().sub(va);
  const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
  return (
    <mesh position={mid} quaternion={q} material={material}>
      <cylinderGeometry args={[r, r, dir.length(), 28]} />
    </mesh>
  );
};

const Glass: React.FC<{size: V3; pos: V3; color: string; opacity: number; edge: number}> = ({size, pos, color, opacity, edge}) => {
  const edges = useMemo(() => new THREE.EdgesGeometry(new THREE.BoxGeometry(...size)), [size[0], size[1], size[2]]);
  return (
    <group position={pos}>
      <mesh renderOrder={5}>
        <boxGeometry args={size} />
        <meshBasicMaterial color={color} transparent opacity={opacity} depthWrite={false} side={THREE.DoubleSide} />
      </mesh>
      <lineSegments geometry={edges} renderOrder={6}>
        <lineBasicMaterial color={C.cyan} transparent opacity={edge} />
      </lineSegments>
    </group>
  );
};

// cached material variants: never create materials per frame (shader recompiles are very slow)
const glowCache = new Map<string, THREE.MeshMatcapMaterial>();
const CYAN = new THREE.Color(C.cyan);
const glowMat = (key: string, base: THREE.MeshMatcapMaterial, o: number) => {
  let m = glowCache.get(key);
  if (!m) { m = base.clone(); glowCache.set(key, m); }
  m.color.copy(base.color).lerp(CYAN, o * 0.75);
  return m;
};
const fadeCache = new Map<THREE.Material, THREE.Material>();
const fadeMat = (base: THREE.Material, o: number) => {
  let m = fadeCache.get(base) as THREE.MeshMatcapMaterial | undefined;
  if (!m) { m = (base as THREE.MeshMatcapMaterial).clone(); m.transparent = true; m.depthWrite = false; fadeCache.set(base, m); }
  m.opacity = o;
  return m;
};
const runnerIn = new THREE.MeshMatcapMaterial({matcap: MC, color: '#6f8fb3', transparent: true, opacity: 0.5});
const runnerEx = new THREE.MeshMatcapMaterial({matcap: MC, color: '#d9783a', transparent: true, opacity: 0.6});

type EngineState = {
  phi: number; explode: number; focus: number; hi: Record<string, number>; t: number;
};

const EngineModel: React.FC<EngineState> = ({phi, explode, focus, hi, t}) => {
  const E = (v: number) => v * explode;
  const offs = {head: E(1.7), cam: E(2.7), valve: E(1.7), plug: E(2.2), rod: E(-0.7), crank: E(-1.5), pan: E(-2.3), piston: E(0.15)};
  const dim = (i: number) => (i === 0 ? 1 : 1 - focus * 0.88);
  const hiMat = (key: string, base: THREE.MeshMatcapMaterial) => (hi[key] ? glowMat(key, base, hi[key]) : base);

  const pistonMat = hiMat('piston', mat.alu);
  const rodMat = hiMat('rod', mat.steel);
  const crankMat = hiMat('crank', mat.dark);
  const camMat = hiMat('cam', mat.dark);
  const valveMat = hiMat('valve', mat.steel);
  const plugMat = hiMat('plug', mat.ceramic);

  return (
    <group>
      {/* oil pan + block + head (x-ray glass) */}
      <Glass size={[5.4, 1.0, 1.5]} pos={[0, -1.85 + offs.pan, 0]} color="#7aa2c8" opacity={0.08 * (1 - focus * 0.6)} edge={0.35 * (1 - focus * 0.7)} />
      <Glass size={[5.4, 1.85, 1.5]} pos={[0, (DECK - 1.3) / 2 - 0.65 + 0.65, 0]} color={hi.block ? '#4fd1ff' : '#8fc4ff'} opacity={(0.1 + (hi.block ?? 0) * 0.14) * (1 - focus * 0.6)} edge={(0.5 + (hi.block ?? 0) * 0.5) * (1 - focus * 0.6)} />
      <Glass size={[5.4, 0.8, 1.5]} pos={[0, DECK + 0.4 + offs.head, 0]} color={hi.head ? '#4fd1ff' : '#a9d6ff'} opacity={(0.09 + (hi.head ?? 0) * 0.14) * (1 - focus * 0.6)} edge={(0.45 + (hi.head ?? 0) * 0.5) * (1 - focus * 0.6)} />

      {/* crankshaft */}
      <group position={[0, CRANK_Y + offs.crank, 0]} rotation={[phi, 0, 0]}>
        {[-2.4, -1.2, 0, 1.2, 2.4].map((x) => (
          <mesh key={x} position={[x, 0, 0]} rotation={[0, 0, PI / 2]} material={crankMat}><cylinderGeometry args={[0.17, 0.17, 0.42, 32]} /></mesh>
        ))}
        {CYL_X.map((x, i) => {
          const s = THROW[i] === 0 ? 1 : -1;
          return (
            <group key={x}>
              {[-0.21, 0.21].map((dx) => (
                <mesh key={dx} position={[x + dx, s * R * 0.45, 0]} material={crankMat}><boxGeometry args={[0.12, R * 1.9, 0.52]} /></mesh>
              ))}
              <mesh position={[x, s * R, 0]} rotation={[0, 0, PI / 2]} material={crankMat}><cylinderGeometry args={[0.14, 0.14, 0.32, 32]} /></mesh>
              <mesh position={[x, -s * R * 0.55, 0]} material={crankMat}><boxGeometry args={[0.5, 0.32, 0.6]} /></mesh>
            </group>
          );
        })}
        {/* flywheel */}
        <mesh position={[-3.0, 0, 0]} rotation={[0, 0, PI / 2]} material={crankMat}><cylinderGeometry args={[1.0, 1.0, 0.16, 64]} /></mesh>
        <mesh position={[-3.0, 0, 0]} rotation={[0, PI / 2, 0]} material={mat.ring}><torusGeometry args={[1.0, 0.05, 12, 80]} /></mesh>
        {[0, 1, 2, 3, 4, 5].map((k) => (
          <mesh key={k} position={[-3.09, Math.cos(k * PI / 3) * 0.6, Math.sin(k * PI / 3) * 0.6]} rotation={[0, 0, PI / 2]} material={mat.ring}><cylinderGeometry args={[0.1, 0.1, 0.02, 20]} /></mesh>
        ))}
        {/* timing pulley */}
        <mesh position={[2.85, 0, 0]} rotation={[0, 0, PI / 2]} material={mat.steel}><cylinderGeometry args={[0.32, 0.32, 0.2, 40]} /></mesh>
      </group>

      {CYL_X.map((x, i) => {
        const ph = cyclePhase(phi, i);
        const a = phi + THROW[i];
        const pinY = pistonPinY(a);
        const top = pinY + PIN_TO_TOP;
        const crankPin: V3 = [x, CRANK_Y + R * Math.cos(a) + offs.crank, R * Math.sin(a)];
        const pistonPin: V3 = [x, pinY + offs.piston, 0];
        const rodA: V3 = [crankPin[0], crankPin[1] + offs.rod * 0.0, crankPin[2]];
        const o = dim(i);
        const fm = (m: THREE.Material) => (o >= 0.999 ? m : fadeMat(m, o));
        const pM = fm(pistonMat), rM = fm(rodMat), vM = fm(valveMat), plM = fm(plugMat), stM = fm(mat.steel), riM = fm(mat.ring), cuM = fm(mat.copper), dkM = fm(mat.dark), cmM = fm(camMat);
        // valve lift
        const inLift = ph < PI ? Math.sin(ph) * 0.14 : 0;
        const exLift = ph > 3 * PI ? Math.sin(ph - 3 * PI) * 0.14 : 0;
        // gas
        let gasColor = '#4fc3ff', gasOp = 0.0;
        if (ph < PI) { gasColor = '#59c8ff'; gasOp = 0.15 + 0.25 * (ph / PI); }
        else if (ph < 2 * PI) { const k = (ph - PI) / PI; gasColor = new THREE.Color('#59c8ff').lerp(new THREE.Color('#2f6bff'), k).getStyle(); gasOp = 0.4 + 0.3 * k; }
        else if (ph < 3 * PI) { const k = (ph - 2 * PI) / PI; gasColor = new THREE.Color('#fff2a8').lerp(new THREE.Color('#ff6a00'), Math.min(1, k * 2.2)).lerp(new THREE.Color('#8a2b0a'), Math.max(0, k * 1.6 - 0.6)).getStyle(); gasOp = 0.9 - 0.45 * k; }
        else { const k = (ph - 3 * PI) / PI; gasColor = '#8d939c'; gasOp = 0.45 * (1 - k) + 0.05; }
        const gasH = Math.max(0.02, DECK - top);
        const spark = ph > 2 * PI - 0.02 && ph < 2 * PI + 0.5 ? 1 - (ph - 2 * PI) / 0.5 : 0;
        const camRot = (lobePhase: number) => ph / 2 - lobePhase + PI;
        return (
          <group key={x}>
            {/* liner */}
            <mesh position={[x, (DECK - 0.8) / 2, 0]} renderOrder={4}>
              <cylinderGeometry args={[BORE + 0.02, BORE + 0.02, DECK + 0.8, 48, 1, true]} />
              <meshBasicMaterial color="#9fb4c8" transparent opacity={0.16 * o} side={THREE.DoubleSide} depthWrite={false} />
            </mesh>
            {/* gas */}
            {gasOp > 0.01 && (
              <mesh position={[x, top + gasH / 2, 0]} renderOrder={3}>
                <cylinderGeometry args={[BORE - 0.01, BORE - 0.01, gasH, 40]} />
                <meshBasicMaterial color={gasColor} transparent opacity={gasOp * o} depthWrite={false} />
              </mesh>
            )}
            {spark > 0 && o > 0.5 && (
              <>
                <mesh position={[x, DECK - 0.04 + offs.plug * 0, 0]}><sphereGeometry args={[0.06 + spark * 0.12, 16, 16]} /><meshBasicMaterial color="#fffbe0" /></mesh>
              </>
            )}
            {/* piston */}
            <group position={[x, top - PISTON_H / 2 + offs.piston, 0]}>
              <mesh material={pM}><cylinderGeometry args={[BORE - 0.015, BORE - 0.015, PISTON_H, 48]} /></mesh>
              {[0.17, 0.11, 0.05].map((dy) => (
                <mesh key={dy} position={[0, dy, 0]} rotation={[PI / 2, 0, 0]} material={riM}><torusGeometry args={[BORE - 0.012, 0.012, 8, 48]} /></mesh>
              ))}
            </group>
            {/* rod */}
            <Tube a={rodA} b={pistonPin} r={0.06} material={rM} />
            <mesh position={rodA} rotation={[0, 0, PI / 2]} material={rM}><cylinderGeometry args={[0.2, 0.2, 0.2, 32]} /></mesh>
            <mesh position={pistonPin} rotation={[0, 0, PI / 2]} material={rM}><cylinderGeometry args={[0.1, 0.1, 0.22, 24]} /></mesh>
            {/* valves */}
            {[[-0.22, inLift], [0.22, exLift]].map(([z, lift]) => (
              <group key={z} position={[x, DECK + offs.valve - lift, z]}>
                <mesh position={[0, 0.02, 0]} material={vM}><cylinderGeometry args={[0.13, 0.09, 0.04, 32]} /></mesh>
                <mesh position={[0, 0.36, 0]} material={vM}><cylinderGeometry args={[0.025, 0.025, 0.66, 12]} /></mesh>
                <mesh position={[0, 0.62, 0]} material={cuM}><cylinderGeometry args={[0.07, 0.07, 0.03, 20]} /></mesh>
                {[0, 1, 2, 3, 4].map((k) => (
                  <mesh key={k} position={[0, 0.4 + k * (0.045 + lift * 0.0), 0]} rotation={[PI / 2, 0, 0]} material={dkM}><torusGeometry args={[0.055, 0.012, 6, 20]} /></mesh>
                ))}
              </group>
            ))}
            {/* spark plug */}
            <group position={[x, DECK + offs.plug, 0]}>
              <mesh position={[0, 0.06, 0]} material={stM}><cylinderGeometry args={[0.05, 0.05, 0.12, 16]} /></mesh>
              <mesh position={[0, 0.2, 0]} material={stM}><cylinderGeometry args={[0.085, 0.085, 0.12, 6]} /></mesh>
              <mesh position={[0, 0.48, 0]} material={plM}><cylinderGeometry args={[0.055, 0.075, 0.45, 20]} /></mesh>
              <mesh position={[0, 0.76, 0]} material={stM}><cylinderGeometry args={[0.03, 0.03, 0.12, 12]} /></mesh>
            </group>
            {/* cam lobes */}
            {[[-0.25, PI / 4], [0.25, 1.75 * PI]].map(([z, lp]) => (
              <group key={z} position={[x, DECK + 0.95 + offs.cam, z]} rotation={[camRot(lp), 0, 0]}>
                <mesh rotation={[0, 0, PI / 2]} material={cmM}><cylinderGeometry args={[0.12, 0.12, 0.16, 28]} /></mesh>
                <mesh position={[0, 0.07, 0]} rotation={[0, 0, PI / 2]} material={cmM}><cylinderGeometry args={[0.08, 0.08, 0.16, 28]} /></mesh>
              </group>
            ))}
            {/* intake / exhaust runners with flow */}
            <Tube a={[x, DECK + 0.5 + offs.head, -1.15]} b={[x, DECK + 0.12 + offs.head, -0.3]} r={0.1} material={o >= 0.999 ? runnerIn : fadeMat(runnerIn, 0.45 * o)} />
            <Tube a={[x, DECK + 0.5 + offs.head, 1.15]} b={[x, DECK + 0.12 + offs.head, 0.3]} r={0.1} material={o >= 0.999 ? runnerEx : fadeMat(runnerEx, 0.55 * o)} />
            {Array.from({length: 10}).map((_, k) => {
              const inOn = ph < PI ? Math.sin(ph) : 0;
              const exOn = ph > 3 * PI ? Math.sin(ph - 3 * PI) : 0;
              const u = ((t * 1.6 + k / 10) % 1);
              const jitter = (random(`j${i}${k}`) - 0.5) * 0.08;
              return (
                <group key={k}>
                  {inOn > 0.05 && <mesh position={[x + jitter, DECK + 0.5 - 0.42 * u, -1.15 + 0.95 * u]}><sphereGeometry args={[0.035, 8, 8]} /><meshBasicMaterial color="#7fdcff" transparent opacity={inOn * o} /></mesh>}
                  {exOn > 0.05 && <mesh position={[x + jitter, DECK + 0.08 + 0.42 * u, 0.25 + 0.95 * u]}><sphereGeometry args={[0.04, 8, 8]} /><meshBasicMaterial color="#b8bec7" transparent opacity={exOn * o * 0.9} /></mesh>}
                </group>
              );
            })}
          </group>
        );
      })}
      {/* camshafts */}
      {[-0.25, 0.25].map((z) => (
        <group key={z}>
          <mesh position={[0.15, DECK + 0.95 + offs.cam, z]} rotation={[0, 0, PI / 2]} material={camMat}><cylinderGeometry args={[0.06, 0.06, 4.9, 20]} /></mesh>
          <mesh position={[2.75, DECK + 0.95 + offs.cam, z]} rotation={[0, 0, PI / 2]} material={mat.steel}><cylinderGeometry args={[0.28, 0.28, 0.12, 40]} /></mesh>
        </group>
      ))}
    </group>
  );
};

// ---------- 2D overlay components ----------
const Tag: React.FC<{anchor: readonly [number, number]; text: string; o: number; dx: number; dy: number; color?: string}> = ({anchor, text, o, dx, dy, color = C.cyan}) => {
  if (o <= 0) return null;
  const [ax, ay] = anchor;
  const bx = ax + dx, by = ay + dy;
  const k = p(o, 0, 1);
  return (
    <>
      <svg width={W} height={H} style={{position: 'absolute', left: 0, top: 0, opacity: o}}>
        <circle cx={ax} cy={ay} r={7} fill={color} />
        <circle cx={ax} cy={ay} r={14} fill="none" stroke={color} strokeWidth={2} opacity={0.6} />
        <polyline points={`${ax},${ay} ${ax + (bx - ax) * k},${ay + (by - ay) * k}`} stroke={color} strokeWidth={2.5} fill="none" />
      </svg>
      <div dir="rtl" style={{
        position: 'absolute', left: bx, top: by, transform: `translate(${dx > 0 ? '0' : '-100%'},-50%)`, opacity: o,
        fontFamily: BODY, fontWeight: 700, fontSize: 34, color: '#fff', whiteSpace: 'nowrap',
        background: 'rgba(8,14,22,0.82)', border: `2px solid ${color}`, borderRadius: 10, padding: '6px 18px',
        boxShadow: `0 0 24px ${color}44`,
      }}>{text}</div>
    </>
  );
};

const STROKES = [
  {key: 'intake', n: 1, name: 'السحب', color: '#59c8ff'},
  {key: 'compress', n: 2, name: 'الضغط', color: '#3b6bff'},
  {key: 'power', n: 3, name: 'الاحتراق', color: '#ff7a1a'},
  {key: 'exhaust', n: 4, name: 'العادم', color: '#9aa3ad'},
];

export const Engine: React.FC = () => {
  const [h] = useState(() => delayRender('fonts'));
  useEffect(() => {
    Promise.all([
      document.fonts.load('100px Lalezar', 'محرك'),
      document.fonts.load('700 40px "IBM Plex Sans Arabic"', 'محرك'),
      document.fonts.load('600 40px "IBM Plex Sans Arabic"', 'محرك'),
    ]).then(() => document.fonts.ready).then(() => continueRender(h));
  }, [h]);

  const f = useCurrentFrame();
  const t = f / FPS;
  const phi = crankAngle(t);
  const cam = camAt(t);
  const explode = Math.min(p(t, SC.parts[0] + 0.2, SC.parts[0] + 2.4), 1 - p(t, SC.parts[1] - 1.6, SC.parts[1] + 0.3));
  const focus = Math.min(p(t, SC.intake[0] - 0.2, SC.intake[0] + 1.4), 1 - p(t, SC.exhaust[1] - 0.6, SC.exhaust[1] + 1.2));
  const pl = (k: number) => lineOf('parts', k);
  const hiWin = (k: number) => win(t, pl(k).start, pl(k).start + pl(k).dur + 0.5, 0.4) * (0.6 + 0.4 * Math.sin(t * 5));
  const hi: Record<string, number> = {
    block: hiWin(0), piston: hiWin(1), rod: hiWin(2), crank: hiWin(2), head: hiWin(3), valve: hiWin(3), cam: hiWin(3), plug: hiWin(3),
  };

  const sub = LINES.find((l) => t >= l.start - 0.05 && t <= l.start + l.dur + 0.25);
  const curStroke = STROKES.find((s) => t >= SC[s.key][0] && t < SC[s.key][1]);
  const hud = win(t, SC.intake[0] + 0.3, SC.exhaust[1] - 0.2, 0.5);
  const ph1 = cyclePhase(phi, 0);

  // exploded-view label anchors (3D → screen)
  const E = explode;
  const A = (v: V3) => project(v, cam);
  const labelSeq = (k: number, delay = 0) => win(t, pl(k).start + delay, SC.parts[1] - 1.4, 0.4) * E;

  const fl = (k: number) => {
    const st = lineOf('fact', 0).start;
    return p(t, st + k, st + k + 0.6);
  };

  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 40%, #16263a 0%, #0a121c 55%, #05080d 100%)', overflow: 'hidden'}}>
      {LINES.map((l, i) => (
        <Sequence key={i} from={Math.round(l.start * FPS)} durationInFrames={Math.ceil((l.dur + 0.3) * FPS)}>
          <Audio src={staticFile(l.file)} volume={1} />
        </Sequence>
      ))}
      <Audio src={staticFile('music.wav')} volume={0.55} />

      {/* blueprint grid */}
      <AbsoluteFill style={{
        backgroundImage: 'linear-gradient(rgba(79,209,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(79,209,255,0.05) 1px, transparent 1px)',
        backgroundSize: '60px 60px', backgroundPosition: `${(-t * 6) % 60}px 0px`,
      }} />

      <ThreeCanvas width={W} height={H} gl={{antialias: true, alpha: true}} camera={{fov: FOV, position: cam.pos}}>
        <Rig pos={cam.pos} tgt={cam.tgt} />
        <ambientLight intensity={0.35} />
        <directionalLight position={[6, 9, 7]} intensity={2.4} />
        <directionalLight position={[-7, 3, -6]} intensity={1.6} color="#7cc4ff" />
        <directionalLight position={[0, -6, 4]} intensity={0.5} color="#ffb070" />
        <EngineModel phi={phi} explode={explode} focus={focus} hi={hi} t={t} />
        <gridHelper args={[30, 60, '#1f4a66', '#12283a']} position={[0, -2.9, 0]} />
      </ThreeCanvas>

      {/* ---------- HOOK TITLE ---------- */}
      {(() => {
        const o = win(t, 0.6, SC.hook[1] - 0.4, 0.6);
        if (o <= 0) return null;
        const y = interpolate(p(t, 0.6, 1.6, Easing.out(Easing.cubic)), [0, 1], [40, 0]);
        return (
          <div dir="rtl" style={{position: 'absolute', top: 70, left: 0, right: 0, textAlign: 'center', opacity: o, transform: `translateY(${y}px)`}}>
            <div style={{fontFamily: BODY, fontWeight: 700, fontSize: 30, color: C.cyan, letterSpacing: 4}}>هندسة ببساطة</div>
            <div style={{fontFamily: DISPLAY, fontSize: 104, color: C.text, lineHeight: 1.2, textShadow: '0 8px 40px rgba(0,0,0,0.7)'}}>كيف يعمل محرّك السيارة؟</div>
          </div>
        );
      })()}

      {/* ---------- EXPLODED LABELS ---------- */}
      {E > 0.02 && <>
        <Tag anchor={A([2.7, -0.4, 0.75])} text="كتلة المحرّك" o={labelSeq(0)} dx={140} dy={60} />
        <Tag anchor={A([0.6, -0.1, 0])} text="الأسطوانات" o={labelSeq(0, 1.6)} dx={300} dy={-30} />
        <Tag anchor={A([-0.6, pistonPinY(phi + PI) + 0.25 + 0.15, 0.43])} text="المِكبس" o={labelSeq(1)} dx={-260} dy={-40} />
        <Tag anchor={A([-1.8, -1.5, 0.1])} text="ذراع التوصيل" o={labelSeq(2)} dx={-300} dy={10} />
        <Tag anchor={A([1.2, CRANK_Y - 1.5, 0.2])} text="عمود الكرنك" o={labelSeq(2, 2.2)} dx={260} dy={60} />
        <Tag anchor={A([2.7, DECK + 0.4 + 1.7, 0.75])} text="رأس الأسطوانات" o={labelSeq(3)} dx={160} dy={20} />
        <Tag anchor={A([-1.8, DECK + 1.7 + 0.35, 0.22])} text="الصمّامات" o={labelSeq(3, 1.8)} dx={-280} dy={-20} />
        <Tag anchor={A([0.6, DECK + 0.95 + 2.7, 0.25])} text="عمود الكامات" o={labelSeq(3, 3.4)} dx={240} dy={-60} />
        <Tag anchor={A([-0.6, DECK + 2.2 + 0.5, 0])} text="شمعة الإشعال" o={labelSeq(3, 5.2)} dx={-240} dy={-90} />
      </>}

      {/* ---------- STROKE HUD ---------- */}
      {hud > 0 && (
        <div dir="rtl" style={{position: 'absolute', right: 70, top: 80, width: 430, opacity: hud, color: C.text}}>
          <div style={{fontFamily: BODY, fontWeight: 700, fontSize: 26, color: C.cyan, letterSpacing: 2, marginBottom: 14}}>دورة الأشواط الأربعة</div>
          {STROKES.map((s) => {
            const on = curStroke?.key === s.key;
            return (
              <div key={s.key} style={{
                display: 'flex', alignItems: 'center', gap: 18, padding: '12px 18px', marginBottom: 10, borderRadius: 12,
                background: on ? `${s.color}33` : 'rgba(10,18,28,0.6)', border: `2px solid ${on ? s.color : 'rgba(255,255,255,0.08)'}`,
                transform: `scale(${on ? 1.04 : 1})`, transformOrigin: 'right center',
              }}>
                <div style={{width: 52, height: 52, borderRadius: '50%', background: on ? s.color : 'rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: DISPLAY, fontSize: 34, color: on ? '#05080d' : '#8b95a1'}}>{s.n}</div>
                <div style={{fontFamily: DISPLAY, fontSize: 44, opacity: on ? 1 : 0.45}}>{s.name}</div>
              </div>
            );
          })}
          {/* crank dial */}
          <div style={{display: 'flex', alignItems: 'center', gap: 20, marginTop: 18}}>
            <svg width={120} height={120} viewBox="-60 -60 120 120">
              <circle r={50} fill="rgba(10,18,28,0.7)" stroke="rgba(255,255,255,0.12)" strokeWidth={3} />
              {STROKES.map((s, i) => {
                const a0 = i * PI / 2 - PI / 2, a1 = a0 + PI / 2;
                return <path key={s.key} d={`M${50 * Math.cos(a0)},${50 * Math.sin(a0)} A50,50 0 0 1 ${50 * Math.cos(a1)},${50 * Math.sin(a1)}`} stroke={s.color} strokeWidth={6} fill="none" opacity={0.8} />;
              })}
              <line x1={0} y1={0} x2={44 * Math.cos(ph1 / 2 - PI / 2)} y2={44 * Math.sin(ph1 / 2 - PI / 2)} stroke="#fff" strokeWidth={4} strokeLinecap="round" />
              <circle r={6} fill="#fff" />
            </svg>
            <div>
              <div style={{fontFamily: BODY, fontSize: 22, opacity: 0.7}}>زاوية عمود الكرنك</div>
              <div style={{fontFamily: DISPLAY, fontSize: 52}}>{Math.round(ph1 * 180 / PI)}°</div>
            </div>
          </div>
        </div>
      )}

      {/* stroke-specific tags */}
      {focus > 0.5 && (() => {
        const x = -1.8;
        const top = pistonPinY(phi) + PIN_TO_TOP;
        const tags: React.ReactNode[] = [];
        const sIn = lineOf('intake', 1), sCo = lineOf('compress', 1), sPo = lineOf('power', 1), sEx = lineOf('exhaust', 1);
        tags.push(<Tag key="iv" anchor={A([x, DECK + 0.1, -0.3])} text="صمّام الدخول" o={win(t, sIn.start + 1.2, sIn.start + sIn.dur + 0.4)} dx={-330} dy={-140} color="#59c8ff" />);
        tags.push(<Tag key="mix" anchor={A([x, (top + DECK) / 2, 0.3])} text="هواء + وقود" o={win(t, sIn.start + 3.2, sIn.start + sIn.dur + 0.4)} dx={-360} dy={90} color="#59c8ff" />);
        tags.push(<Tag key="pc" anchor={A([x, top - 0.1, 0.43])} text="المكبس يصعد ↑" o={win(t, sCo.start + 1.6, sCo.start + sCo.dur + 0.4)} dx={-360} dy={80} color="#3b6bff" />);
        tags.push(<Tag key="sp" anchor={A([x, DECK + 0.1, 0])} text="شرارة!" o={win(t, sPo.start, sPo.start + 2.6)} dx={-300} dy={-150} color="#ff7a1a" />);
        tags.push(<Tag key="pd" anchor={A([x, top - 0.1, 0.43])} text="قوة الدفع ↓" o={win(t, sPo.start + 2.6, sPo.start + sPo.dur + 0.4)} dx={-360} dy={80} color="#ff7a1a" />);
        tags.push(<Tag key="ev" anchor={A([x, DECK + 0.1, 0.3])} text="صمّام الخروج" o={win(t, sEx.start + 0.4, sEx.start + sEx.dur + 0.4)} dx={-330} dy={-140} color="#9aa3ad" />);
        return tags;
      })()}

      {/* power flash */}
      {(() => {
        const s = lineOf('power', 1).start - 0.2;
        const o = Math.max(0, 1 - Math.abs(t - s - 0.08) / 0.35);
        return o > 0 ? <AbsoluteFill style={{background: `radial-gradient(circle at 40% 45%, rgba(255,180,80,${0.45 * o}) 0%, rgba(255,120,30,${0.18 * o}) 30%, transparent 60%)`}} /> : null;
      })()}

      {/* ---------- CYCLE: firing order ---------- */}
      {(() => {
        const o = win(t, SC.cycle[0] + 1.6, SC.cycle[1] + 0.2, 0.5);
        if (o <= 0) return null;
        const order = [0, 2, 3, 1];
        return <>
          <div dir="rtl" style={{position: 'absolute', top: 70, left: 0, right: 0, textAlign: 'center', opacity: o}}>
            <div style={{fontFamily: BODY, fontWeight: 700, fontSize: 28, color: C.cyan, letterSpacing: 2}}>ترتيب الاشتعال</div>
            <div style={{fontFamily: DISPLAY, fontSize: 84, color: C.text}} dir="ltr">
              {order.map((c, k) => {
                const ph = cyclePhase(phi, c);
                const fire = ph > 2 * PI && ph < 2 * PI + 1.2;
                return <span key={k} style={{color: fire ? '#ff9a3c' : C.text, margin: '0 14px'}}>{c + 1}{k < 3 && <span style={{color: '#55606c', marginLeft: 28}}>←</span>}</span>;
              })}
            </div>
          </div>
        </>;
      })()}

      {/* ---------- FACT + END ---------- */}
      {(() => {
        const st = lineOf('fact', 0).start;
        const o = win(t, st - 0.2, TL.total - 4.6, 0.5);
        const end = p(t, TL.total - 4.4, TL.total - 3.6);
        const rpm = Math.round(interpolate(t, [st, st + 3.5], [800, 3000], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)}));
        return <>
          {o > 0 && (
            <div dir="rtl" style={{position: 'absolute', top: 60, left: 0, right: 0, display: 'flex', justifyContent: 'center', gap: 60, opacity: o, color: C.text}}>
              <div style={{textAlign: 'center', background: 'rgba(8,14,22,0.75)', padding: '18px 40px', borderRadius: 16, border: '2px solid rgba(79,209,255,0.4)'}}>
                <div style={{fontFamily: DISPLAY, fontSize: 96, color: C.cyan, lineHeight: 1.1}}>{rpm.toLocaleString('en-US')}</div>
                <div style={{fontFamily: BODY, fontWeight: 600, fontSize: 30}}>دورة في الدقيقة</div>
              </div>
              <div style={{textAlign: 'center', background: 'rgba(8,14,22,0.75)', padding: '18px 40px', borderRadius: 16, border: '2px solid rgba(255,154,60,0.5)', opacity: fl(5.2), transform: `scale(${0.8 + 0.2 * fl(5.2)})`}}>
                <div style={{fontFamily: DISPLAY, fontSize: 96, color: '#ff9a3c', lineHeight: 1.1}}>25</div>
                <div style={{fontFamily: BODY, fontWeight: 600, fontSize: 30}}>اشتعالاً في الثانية لكل أسطوانة</div>
              </div>
            </div>
          )}
          <AbsoluteFill style={{background: `rgba(5,8,13,${0.8 * end})`}} />
          {end > 0 && (
            <div dir="rtl" style={{position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 20, opacity: end, color: C.text}}>
              <div style={{fontFamily: BODY, fontWeight: 700, fontSize: 30, color: C.cyan, letterSpacing: 4}}>هندسة ببساطة</div>
              <div style={{fontFamily: DISPLAY, fontSize: 110, lineHeight: 1.2}}>الحلقة القادمة: ناقل الحركة</div>
              <div style={{width: 560 * p(t, TL.total - 3.8, TL.total - 2.8), height: 6, background: C.cyan, borderRadius: 3}} />
              <div style={{fontFamily: BODY, fontWeight: 600, fontSize: 40, opacity: 0.85}}>اشترك حتى لا تفوتك</div>
            </div>
          )}
        </>;
      })()}

      {/* ---------- SUBTITLES ---------- */}
      {sub && t < TL.total - 4.6 && (
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 52, display: 'flex', justifyContent: 'center'}}>
          <div dir="rtl" style={{fontFamily: BODY, fontWeight: 600, fontSize: 40, color: '#fff', background: 'rgba(0,0,0,0.6)', padding: '10px 30px', borderRadius: 10, opacity: p(t, sub.start - 0.05, sub.start + 0.12), maxWidth: 1500, textAlign: 'center'}}>
            {sub.text}
          </div>
        </div>
      )}

      {/* film look */}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.6) 100%)'}} />
      <AbsoluteFill style={{backgroundImage: `url(${staticFile('noise.png')})`, opacity: 0.05, mixBlendMode: 'overlay',
        backgroundPosition: `${Math.floor(random('gx' + f) * 512)}px ${Math.floor(random('gy' + f) * 512)}px`}} />
    </AbsoluteFill>
  );
};
