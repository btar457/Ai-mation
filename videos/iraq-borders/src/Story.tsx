import React, {useEffect, useState} from 'react';
import {
  AbsoluteFill, Audio, Easing, Img, interpolate, random, staticFile,
  useCurrentFrame, continueRender, delayRender,
} from 'remotion';
import {geoMercator, geoPath, geoGraticule10} from 'd3-geo';
import '@fontsource/lalezar';
import '@fontsource/ibm-plex-sans-arabic/400.css';
import '@fontsource/ibm-plex-sans-arabic/600.css';
import '@fontsource/ibm-plex-sans-arabic/700.css';
import geo from './geo.json';
import subs from './subs.json';

const FPS = 30;
export const TOTAL = 77 * FPS;
const W = 1920, H = 1080;

// ---------- palette ----------
const C = {
  sea1: '#14303f', sea2: '#0a1a25', land: '#e7dcc3', landEdge: '#9c8a6a',
  iraq: '#f2c14e', ink: '#d7263d', blue: '#2f6fd6', green: '#5f9a6b', brick: '#c4693f',
  steel: '#4f86b8', text: '#fbf6ea', dark: '#0d1820', orange: '#ef8a2b',
};
const DISPLAY = 'Lalezar';
const BODY = '"IBM Plex Sans Arabic"';

// ---------- geography ----------
type LL = [number, number];
const proj = geoMercator().fitExtent([[0, 0], [W, H]], {
  type: 'MultiPoint', coordinates: [[30, 22], [56, 41]],
} as any);
const path = geoPath(proj);
const P = (ll: LL) => proj(ll) as [number, number];
const countries = (geo as any).countries.features as any[];
const byName = (n: string) => countries.find((f) => f.properties.name === n);
const IRAQ = path(byName('Iraq'))!;
const TURKEY = path(byName('Turkey'))!;
const M = (geo as any).meshes;
const mesh = (k: string) => path(M[k])!;
const GRAT = path(geoGraticule10())!;
const poly = (pts: LL[]) => path({type: 'Polygon', coordinates: [[...pts, pts[0]]]} as any)!;
const line = (pts: LL[]) => path({type: 'LineString', coordinates: pts} as any)!;

// Ottoman vilayets (approximate)
const MOSUL_V = poly([[38, 38.5], [50, 38.5], [50, 34.5], [45.8, 34.5], [44.5, 34.6], [43.3, 35.0], [41, 35.6], [38, 35.6]] as LL[]);
const BASRA_V = poly([[38, 31.0], [40.5, 31.0], [44.5, 31.8], [46, 32.6], [47.5, 33.0], [50, 33], [50, 27.5], [38, 27.5]] as LL[]);
// Sykes–Picot zones (approximate)
const SP_LINE: LL[] = [[35.6, 32.8], [39.5, 33.0], [42.0, 34.6], [43.8, 35.3], [45.3, 35.8], [46.2, 35.8]];
const FR_ZONE = poly([...SP_LINE, [45.0, 37.3], [42.3, 37.3], [36.6, 37.0], [35.9, 36.0]].reverse() as LL[]);
const UK_ZONE = poly([...SP_LINE, [46.2, 35.8], [47.6, 32.6], [48.6, 30.0], [47.4, 29.5], [44.2, 29.1], [38.5, 30.0], [35.2, 29.7]] as LL[]);
// Neutral zones (approximate)
const NZ_IRAQ = poly([[44.73, 29.2], [45.45, 29.5], [46.42, 29.1], [45.5, 28.75]]);
const NZ_KUW = poly([[47.0, 28.52], [48.43, 28.53], [48.6, 28.03], [47.5, 28.0]]);
// Rivers (approximate)
const TIGRIS = line([[42.0, 37.2], [42.7, 36.6], [43.13, 36.34], [43.4, 35.0], [44.0, 34.4], [44.37, 33.31], [45.0, 32.8], [45.8, 32.4], [46.8, 31.6], [47.42, 31.0]]);
const EUPHRATES = line([[40.1, 35.1], [40.9, 34.4], [41.9, 34.4], [42.4, 34.0], [43.3, 33.4], [44.3, 32.0], [45.0, 31.5], [46.3, 31.0], [47.42, 31.0], [47.8, 30.5], [48.5, 29.95]]);
const COAST = line([[47.98, 29.98], [48.54, 29.96]]);

const CITY: Record<string, LL> = {
  mosul: [43.13, 36.34], baghdad: [44.37, 33.31], basra: [47.78, 30.51], uqair: [50.22, 25.65], kuwait: [47.98, 29.37],
};

// ---------- timing helpers ----------
const ease = Easing.inOut(Easing.cubic);
const p = (t: number, a: number, b: number, e = ease) =>
  interpolate(t, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: e});
const win = (t: number, a: number, b: number, fade = 0.5) => Math.min(p(t, a, a + fade), 1 - p(t, b - fade, b));

// ---------- camera ----------
const KEYS: [number, number, number, number][] = [
  [0, 43.7, 33.3, 1.0], [2.4, 43.7, 33.3, 1.25], [4.2, 40.4, 32.6, 2.3], [11.6, 40.6, 32.6, 2.5],
  [13.2, 44.0, 33.6, 1.35], [22.4, 44.0, 33.6, 1.42], [24.2, 40.5, 33.8, 1.0], [33.6, 40.8, 33.8, 1.06],
  [35.2, 43.1, 35.9, 2.0], [37.0, 43.1, 35.9, 2.1], [38.6, 42.4, 35.4, 1.3], [48.8, 43.4, 34.2, 1.3],
  [50.8, 47.6, 28.0, 1.1], [59.8, 47.2, 28.4, 1.18], [61.8, 48.25, 30.0, 4.2], [66.2, 48.25, 30.0, 4.5],
  [67.8, 44.0, 33.0, 1.3], [70.2, 43.8, 32.6, 1.05], [77, 43.8, 32.6, 0.98],
];
const camera = (t: number) => {
  let i = 0;
  while (i < KEYS.length - 2 && t > KEYS[i + 1][0]) i++;
  const [t0, x0, y0, z0] = KEYS[i];
  const [t1, x1, y1, z1] = KEYS[i + 1];
  const k = p(t, t0, t1);
  const lon = x0 + (x1 - x0) * k, lat = y0 + (y1 - y0) * k;
  const z = Math.exp(Math.log(z0) + (Math.log(z1) - Math.log(z0)) * k);
  const [cx, cy] = P([lon, lat]);
  return {cx, cy, z};
};

// ---------- small components ----------
const Draw: React.FC<{d: string; k: number; color: string; w: number; glow?: boolean; dash?: string; opacity?: number}> = ({d, k, color, w, glow, dash, opacity = 1}) =>
  k <= 0 ? null : (
    <g opacity={opacity}>
      {glow && <path d={d} fill="none" stroke={color} strokeWidth={w * 4} strokeOpacity={0.25} vectorEffect="non-scaling-stroke" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - k} strokeLinecap="round" />}
      <path d={d} fill="none" stroke={color} strokeWidth={w} vectorEffect="non-scaling-stroke" pathLength={dash ? undefined : 1}
        strokeDasharray={dash ?? '1 1'} strokeDashoffset={dash ? 0 : 1 - k} strokeLinecap="round" strokeLinejoin="round" />
    </g>
  );

const Label: React.FC<{x: number; y: number; text: string; size?: number; o: number; color?: string; font?: string; bg?: string}> = ({x, y, text, size = 34, o, color = C.dark, font = BODY, bg}) =>
  o <= 0 ? null : (
    <div dir="rtl" style={{
      position: 'absolute', left: x, top: y, transform: `translate(-50%,-50%) scale(${0.85 + 0.15 * o})`, opacity: o,
      fontFamily: font, fontWeight: 700, fontSize: size, color, whiteSpace: 'nowrap',
      textShadow: bg ? 'none' : '0 0 10px rgba(255,248,230,0.9), 0 0 3px rgba(255,248,230,1)',
      background: bg, padding: bg ? '6px 18px' : 0, borderRadius: 8,
    }}>{text}</div>
  );

const Pin: React.FC<{x: number; y: number; o: number; color: string; t: number}> = ({x, y, o, color, t}) =>
  o <= 0 ? null : (
    <div style={{position: 'absolute', left: x, top: y, opacity: o}}>
      {[0, 0.5].map((d) => {
        const ph = ((t + d) % 1);
        return <div key={d} style={{position: 'absolute', left: -40 * ph, top: -40 * ph, width: 80 * ph, height: 80 * ph, borderRadius: '50%', border: `3px solid ${color}`, opacity: 1 - ph}} />;
      })}
      <div style={{position: 'absolute', left: -11, top: -11, width: 22, height: 22, borderRadius: '50%', background: color, border: '4px solid white', boxShadow: '0 2px 10px rgba(0,0,0,0.5)'}} />
    </div>
  );

const Callout: React.FC<{t: number; a: number; b: number; children: React.ReactNode; x: number; y: number; size?: number; color?: string; rot?: number}> = ({t, a, b, children, x, y, size = 96, color = C.text, rot = 0}) => {
  const o = win(t, a, b, 0.35);
  if (o <= 0) return null;
  const s = interpolate(p(t, a, a + 0.45, Easing.out(Easing.back(2))), [0, 1], [0.6, 1]);
  return (
    <div dir="rtl" style={{
      position: 'absolute', left: x, top: y, transform: `translate(-50%,-50%) scale(${s}) rotate(${rot}deg)`, opacity: o,
      fontFamily: DISPLAY, fontSize: size, color, whiteSpace: 'nowrap', lineHeight: 1.25,
      textShadow: '0 6px 30px rgba(0,0,0,0.65), 0 2px 0 rgba(0,0,0,0.4)',
    }}>{children}</div>
  );
};

const Stamp: React.FC<{t: number; a: number; b: number; x: number; y: number; lines: string[]; color: string}> = ({t, a, b, x, y, lines, color}) => {
  const o = win(t, a, b, 0.3);
  if (o <= 0) return null;
  const s = interpolate(p(t, a, a + 0.25, Easing.out(Easing.quad)), [0, 1], [2.4, 1]);
  return (
    <div dir="rtl" style={{
      position: 'absolute', left: x, top: y, transform: `translate(-50%,-50%) rotate(-8deg) scale(${s})`, opacity: o,
      border: `7px double ${color}`, color, padding: '14px 34px', borderRadius: 14, textAlign: 'center',
      fontFamily: DISPLAY, background: 'rgba(251,246,234,0.88)', boxShadow: '0 10px 40px rgba(0,0,0,0.4)',
    }}>
      <div style={{fontSize: 64, lineHeight: 1.15}}>{lines[0]}</div>
      {lines[1] && <div style={{fontSize: 36, fontFamily: BODY, fontWeight: 700}}>{lines[1]}</div>}
    </div>
  );
};

const Card: React.FC<{t: number; a: number; b: number; title: string; sub: string; tag?: string; accent: string}> = ({t, a, b, title, sub, tag, accent}) => {
  const o = win(t, a, b, 0.4);
  if (o <= 0) return null;
  const x = interpolate(p(t, a, a + 0.6, Easing.out(Easing.cubic)), [0, 1], [-80, 0]);
  return (
    <div dir="rtl" style={{
      position: 'absolute', left: 90 + x, top: 230, width: 600, opacity: o, background: 'rgba(13,24,32,0.9)',
      borderRight: `10px solid ${accent}`, borderRadius: 16, padding: '28px 36px', color: C.text, boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
    }}>
      {tag && <div style={{fontFamily: BODY, fontWeight: 700, fontSize: 26, color: accent, letterSpacing: 1}}>{tag}</div>}
      <div style={{fontFamily: DISPLAY, fontSize: 58, lineHeight: 1.3}}>{title}</div>
      <div style={{fontFamily: BODY, fontWeight: 400, fontSize: 30, opacity: 0.85, lineHeight: 1.5}}>{sub}</div>
    </div>
  );
};

// ---------- chapters (top-right) ----------
const CHAPTERS: [number, number, string, string][] = [
  [0.3, 11.9, '', 'خطوط في الرمل'],
  [12.1, 22.7, 'قبل 1914', 'الولايات العثمانية'],
  [22.9, 37.1, '1916', 'سايكس – بيكو'],
  [37.3, 45.4, '1918', 'معركة الموصل'],
  [45.5, 49.2, '1926', 'معركة الموصل'],
  [49.4, 60.4, '1922', 'مؤتمر العُقير'],
  [60.6, 69.2, 'اليوم', 'النتيجة'],
];

export const Story: React.FC = () => {
  const [h] = useState(() => delayRender('fonts'));
  useEffect(() => {
    Promise.all([
      document.fonts.load('100px Lalezar', 'العراق'),
      document.fonts.load('700 40px "IBM Plex Sans Arabic"', 'العراق'),
      document.fonts.load('400 40px "IBM Plex Sans Arabic"', 'العراق'),
    ]).then(() => document.fonts.ready).then(() => continueRender(h));
  }, [h]);

  const f = useCurrentFrame();
  const t = f / FPS;
  const {cx, cy, z} = camera(t);
  const S = (ll: LL) => { const [x, y] = P(ll); return [(x - cx) * z + W / 2, (y - cy) * z + H / 2] as const; };

  // layer states
  const vilayets = win(t, 19.4, 23.4, 0.6);
  const iraqFill = 1 - Math.min(p(t, 13.4, 14.6), 1 - p(t, 46.2, 47.4));
  const zones = win(t, 25.8, 37.6, 0.8);
  const mosulBlue = win(t, 34.2, 38.4, 0.4);
  const mosulRed = win(t, 38.0, 47.4, 0.6);
  const turkeyGlow = win(t, 40.5, 45.8, 0.5) * (0.55 + 0.45 * Math.sin(t * 6));
  const allRed = win(t, 66.6, 70.0, 0.4);
  const endDim = p(t, 69.4, 70.6);

  const sub = (subs as any[]).find((s) => t >= s.s - 0.05 && t <= s.e + 0.35);

  const [mx, my] = S(CITY.mosul), [bx, by] = S(CITY.baghdad), [sx, sy] = S(CITY.basra), [ux, uy] = S(CITY.uqair);
  const ja = S([38.774, 33.372]), jb = S([39.145, 32.125]);
  const rulerAng = Math.atan2(jb[1] - ja[1], jb[0] - ja[0]) * 180 / Math.PI;
  const rulerLen = Math.hypot(jb[0] - ja[0], jb[1] - ja[1]) * 1.6;
  const rulerIn = win(t, 5.3, 11.8, 0.6);
  const ca = S([47.98, 29.98]), cb = S([48.54, 29.96]);

  return (
    <AbsoluteFill style={{background: C.sea2, overflow: 'hidden'}}>
      <Audio src={staticFile('mix.wav')} />
      {/* ---------- MAP ---------- */}
      <svg width={W} height={H} style={{position: 'absolute'}}>
        <defs>
          <radialGradient id="sea" cx="50%" cy="45%" r="75%"><stop offset="0" stopColor={C.sea1} /><stop offset="1" stopColor={C.sea2} /></radialGradient>
          <clipPath id="iraqClip"><path d={IRAQ} /></clipPath>
          {[['hb', C.blue], ['hr', C.ink], ['hg', '#555']].map(([id, col]) => (
            <pattern key={id} id={id} width={7} height={7} patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <rect width={7} height={7} fill={col} fillOpacity={0.18} />
              <line x1={0} y1={0} x2={0} y2={7} stroke={col} strokeWidth={2.4} strokeOpacity={0.75} />
            </pattern>
          ))}
        </defs>
        <rect width={W} height={H} fill="url(#sea)" />
        <g transform={`translate(${W / 2},${H / 2}) scale(${z}) translate(${-cx},${-cy})`}>
          <path d={GRAT} fill="none" stroke="#ffffff" strokeOpacity={0.06} strokeWidth={1} vectorEffect="non-scaling-stroke" />
          {countries.map((c) => (
            <path key={c.properties.name} d={path(c)!} fill={C.land} stroke={C.landEdge} strokeWidth={1.3} vectorEffect="non-scaling-stroke" />
          ))}
          <path d={TURKEY} fill={C.orange} fillOpacity={turkeyGlow * 0.55} />
          {/* Iraq */}
          <path d={IRAQ} fill={C.iraq} fillOpacity={0.92 * iraqFill} />
          <g clipPath="url(#iraqClip)" opacity={vilayets}>
            <path d={IRAQ} fill={C.green} fillOpacity={0.85} />
            <path d={MOSUL_V} fill={C.brick} fillOpacity={0.9} opacity={p(t, 19.6, 20.2)} />
            <path d={BASRA_V} fill={C.steel} fillOpacity={0.9} opacity={p(t, 21.0, 21.6)} />
            <path d={line([[38, 35.6], [41, 35.6], [43.3, 35.0], [44.5, 34.6], [45.8, 34.5], [50, 34.5]])} fill="none" stroke="#fff" strokeWidth={2} strokeDasharray="6 5" vectorEffect="non-scaling-stroke" />
            <path d={line([[38, 31.0], [40.5, 31.0], [44.5, 31.8], [46, 32.6], [47.5, 33.0], [50, 33]])} fill="none" stroke="#fff" strokeWidth={2} strokeDasharray="6 5" vectorEffect="non-scaling-stroke" />
          </g>
          {/* Mosul state during dispute */}
          <g clipPath="url(#iraqClip)">
            <path d={MOSUL_V} fill={C.blue} fillOpacity={0.75 * mosulBlue * (1 - p(t, 38.0, 38.8))} />
            <path d={MOSUL_V} fill={C.ink} fillOpacity={0.7 * mosulRed} />
          </g>
          {/* Sykes–Picot */}
          <g opacity={zones}>
            <path d={FR_ZONE} fill="url(#hb)" stroke={C.blue} strokeWidth={2.5} vectorEffect="non-scaling-stroke" />
            <path d={UK_ZONE} fill="url(#hr)" stroke={C.ink} strokeWidth={2.5} vectorEffect="non-scaling-stroke" />
          </g>
          <Draw d={line(SP_LINE)} k={p(t, 26.0, 28.6) * zones} color="#111" w={5} />
          {/* Rivers */}
          <Draw d={TIGRIS} k={p(t, 12.6, 15.8)} color="#3d86c6" w={3} opacity={1 - endDim * 0.5} />
          <Draw d={EUPHRATES} k={p(t, 13.0, 16.4)} color="#3d86c6" w={3} opacity={1 - endDim * 0.5} />
          {/* Iraq outline */}
          <path d={IRAQ} fill="none" stroke="#8a5a00" strokeWidth={3} vectorEffect="non-scaling-stroke"
            strokeDasharray={iraqFill < 0.5 ? '8 7' : undefined} strokeOpacity={0.35 + 0.65 * iraqFill} />
          {/* S1: straight lines */}
          <Draw d={mesh('jordan')} k={p(t, 2.6, 3.8)} color={C.ink} w={5} glow opacity={1 - p(t, 12, 13)} />
          <Draw d={mesh('saudi')} k={p(t, 3.2, 5.2)} color={C.ink} w={5} glow opacity={1 - p(t, 12, 13)} />
          <Draw d={mesh('syria')} k={p(t, 3.0, 4.8)} color={C.ink} w={5} glow opacity={1 - p(t, 12, 13)} />
          {/* S5: Cox's pen */}
          <Draw d={mesh('saudi')} k={p(t, 54.1, 56.0)} color={C.ink} w={5} glow opacity={1 - p(t, 60.4, 61.2)} />
          <Draw d={mesh('kuwait')} k={p(t, 55.0, 56.4)} color={C.ink} w={5} glow opacity={1 - p(t, 60.4, 61.2)} />
          <Draw d={mesh('kuwaitSaudi')} k={p(t, 55.6, 57.0)} color={C.ink} w={5} glow opacity={1 - p(t, 60.4, 61.2)} />
          <g opacity={win(t, 57.7, 60.8, 0.5)}>
            <path d={NZ_IRAQ} fill="url(#hg)" stroke="#333" strokeWidth={2} vectorEffect="non-scaling-stroke" />
            <path d={NZ_KUW} fill="url(#hg)" stroke="#333" strokeWidth={2} vectorEffect="non-scaling-stroke" />
          </g>
          {/* S6: coast */}
          <Draw d={COAST} k={p(t, 62.0, 63.0)} color={C.ink} w={7} glow opacity={1 - p(t, 66.4, 67.2)} />
          {/* all borders drawn by others */}
          {['syria', 'jordan', 'saudi', 'kuwait', 'iran', 'turkey'].map((k) => (
            <Draw key={k} d={mesh(k)} k={allRed > 0 ? p(t, 66.6, 67.8) : 0} color={C.ink} w={5} glow opacity={allRed} />
          ))}
        </g>
      </svg>

      {/* ---------- MAP LABELS (screen space) ---------- */}
      {(() => {
        const L = (ll: LL, text: string, o: number, size = 34, color = C.dark) => { const [x, y] = S(ll); return <Label key={text + ll[0]} x={x} y={y} text={text} o={o} size={size} color={color} />; };
        const base = 1 - endDim;
        return <>
          {L([38.6, 35.3], 'سوريا', base * (1 - vilayets) * (1 - zones) * (t < 61.5 || t > 66.5 ? 1 : 0))}
          {L([36.6, 31.0], 'الأردن', base * (t < 61.5 || t > 66.5 ? 1 : 0))}
          {L([44.0, 26.2], 'السعودية', base * (t < 61.5 || t > 66.5 ? 1 : 0), 38)}
          {L([51.5, 32.8], 'إيران', base * (t < 61.5 || t > 66.5 ? 1 : 0), 38)}
          {L([36.5, 38.9], 'تركيا', base * (t < 61.5 || t > 66.5 ? 1 : 0), 38)}
          {L([43.6, 33.0], 'العراق', base * iraqFill * (1 - mosulRed) * (t < 61.5 || t > 66.5 ? 1 : 0) * (1 - p(t, 3.0, 3.6) + p(t, 11.6, 12.4)), 56, '#5b3b00')}
          {L([47.75, 29.3], 'الكويت', win(t, 50.6, 61.4) + win(t, 61.8, 66.4) * 0.0, 26)}
          {L([48.9, 30.35], 'الفاو', win(t, 61.8, 66.4), 30)}
          {L([47.6, 30.25], 'الكويت', win(t, 61.8, 66.4), 30)}
          {L([49.1, 30.6], 'إيران', win(t, 61.8, 66.4), 30)}
          {L([42.6, 30.0], 'السعودية', win(t, 50.6, 60.4), 34)}
          {/* vilayets */}
          {L([43.2, 36.4], 'ولاية الموصل', vilayets * p(t, 19.6, 20.2), 34, '#fff')}
          {L([42.6, 33.2], 'ولاية بغداد', vilayets * p(t, 20.3, 20.9), 34, '#fff')}
          {L([45.6, 31.0], 'ولاية البصرة', vilayets * p(t, 21.0, 21.6), 34, '#fff')}
          {L([37.6, 36.8], 'الدولة العثمانية', win(t, 16.4, 22.8), 40, '#6b3b1f')}
          {L([44.9, 33.9], 'دجلة', win(t, 14.5, 22.8), 24, '#1f5c94')}
          {L([41.6, 33.6], 'الفرات', win(t, 15.0, 22.8), 24, '#1f5c94')}
          {/* Sykes–Picot */}
          {L([39.5, 35.8], 'نفوذ فرنسي', zones * p(t, 26.4, 27.2), 44, C.blue)}
          {L([40.5, 31.4], 'نفوذ بريطاني', zones * p(t, 27.0, 27.8), 44, C.ink)}
          {/* neutral zones */}
          {L([45.5, 28.45], 'منطقة محايدة', win(t, 57.9, 60.8), 30, '#222')}
          {L([47.8, 27.6], 'منطقة محايدة', win(t, 58.2, 60.8), 30, '#222')}
          {L([47.0, 25.4], 'مواقع تقريبية', win(t, 58.2, 60.8) * 0.8, 22, '#444')}
          {L([42.0, 30.1], 'حدود تقريبية', win(t, 21.6, 22.8) * 0.8, 22, '#ddd')}
        </>;
      })()}

      {/* pins */}
      <Pin x={mx} y={my} o={win(t, 19.6, 23.0) + win(t, 34.3, 47.2)} color={t > 38.2 && t < 47.2 ? C.ink : t > 34 ? C.blue : C.brick} t={t} />
      <Pin x={bx} y={by} o={win(t, 20.3, 23.0) + win(t, 37.2, 39.4)} color={t > 37 ? C.ink : C.green} t={t} />
      <Pin x={sx} y={sy} o={win(t, 21.0, 23.0)} color={C.steel} t={t} />
      <Pin x={ux} y={uy} o={win(t, 50.6, 57.4)} color={C.ink} t={t} />
      <Label x={ux} y={uy + 50} text="العُقير" o={win(t, 50.8, 57.4)} size={34} />
      <Label x={mx} y={my - 48} text="الموصل" o={win(t, 34.3, 47.2)} size={36} />

      {/* S1 ruler */}
      {rulerIn > 0 && (() => {
        const mxp = (ja[0] + jb[0]) / 2, myp = (ja[1] + jb[1]) / 2;
        const off = interpolate(rulerIn, [0, 1], [260, 46]);
        return (
          <div style={{position: 'absolute', left: mxp, top: myp, opacity: rulerIn, transform: `translate(-50%,-50%) rotate(${rulerAng}deg) translateY(${-off}px)`}}>
            <div style={{width: rulerLen, height: 70, background: 'linear-gradient(#f7e7b4,#e6cf8a)', borderRadius: 6, boxShadow: '0 10px 30px rgba(0,0,0,0.45)', position: 'relative', border: '2px solid #a88a3c'}}>
              {Array.from({length: Math.floor(rulerLen / 16)}).map((_, i) => (
                <div key={i} style={{position: 'absolute', left: 8 + i * 16, bottom: 0, width: 2, height: i % 5 === 0 ? 30 : 16, background: '#5a4410'}} />
              ))}
            </div>
          </div>
        );
      })()}

      {/* Mosul arrows */}
      {(() => {
        const k = p(t, 37.4, 38.4) * win(t, 37.3, 40.4);
        const [tx, ty] = S([41.6, 38.0]);
        const k2 = p(t, 40.7, 41.6) * win(t, 40.6, 45.6);
        return (
          <svg width={W} height={H} style={{position: 'absolute'}}>
            <defs>
              <marker id="ar" markerWidth={6} markerHeight={6} refX={3} refY={3} orient="auto"><path d="M0,0 L6,3 L0,6 z" fill={C.ink} /></marker>
              <marker id="ao" markerWidth={6} markerHeight={6} refX={3} refY={3} orient="auto"><path d="M0,0 L6,3 L0,6 z" fill={C.orange} /></marker>
            </defs>
            {k > 0 && <path d={`M${bx},${by} Q${bx - 160},${(by + my) / 2} ${mx + 10},${my + 40}`} stroke={C.ink} strokeWidth={9} fill="none" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - k} markerEnd={k > 0.95 ? 'url(#ar)' : undefined} strokeLinecap="round" />}
            {k2 > 0 && <path d={`M${tx},${ty} Q${(tx + mx) / 2 - 40},${ty - 30} ${mx - 30},${my - 30}`} stroke={C.orange} strokeWidth={9} fill="none" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - k2} markerEnd={k2 > 0.95 ? 'url(#ao)' : undefined} strokeLinecap="round" />}
          </svg>
        );
      })()}

      {/* ---------- CALLOUTS ---------- */}
      <Callout t={t} a={5.5} b={8.6} x={W / 2} y={170}>كأنها رُسمت بالمسطرة...</Callout>
      <Stamp t={t} a={9.3} b={11.9} x={W / 2 + 330} y={830} lines={['فعلاً!']} color={C.ink} />
      <Callout t={t} a={12.2} b={16.3} x={W / 2} y={150} size={84}>قبل 100 عام: لا دولة اسمها العراق</Callout>
      <Card t={t} a={30.4} b={33.8} tag="وثيقة سرّية · 1916" title="اتفاقية سايكس – بيكو" sub="مارك سايكس (بريطانيا) و فرانسوا جورج بيكو (فرنسا) يقتسمان المشرق على الخريطة" accent={C.blue} />
      <Callout t={t} a={34.4} b={37.3} x={W / 2} y={150} size={88} color="#cfe0ff">المفاجأة: الموصل من حصة فرنسا!</Callout>
      <Label x={(bx + mx) / 2 - 190} y={(by + my) / 2} text="احتلال بريطاني 1918" o={win(t, 38.0, 40.4)} size={34} color="#fff" bg={C.ink} />
      <Label x={S([41.6, 38.0])[0]} y={S([41.6, 38.0])[1] - 50} text="تركيا تطالب بالموصل" o={win(t, 40.8, 45.6)} size={34} color="#fff" bg={C.orange} />
      <Stamp t={t} a={45.6} b={49.2} x={W / 2 + 420} y={760} lines={['عصبة الأمم', 'الموصل للعراق · 1926']} color="#1e5aa8" />
      <Card t={t} a={50.7} b={56.8} tag="مؤتمر العُقير · 1922" title="السير بيرسي كوكس" sub="المندوب السامي البريطاني، رسم بقلمه حدود العراق ونجد والكويت" accent={C.ink} />

      {/* coast measure + bars */}
      {(() => {
        const o = win(t, 62.6, 66.4, 0.4);
        if (o <= 0) return null;
        return <>
          <div style={{position: 'absolute', left: ca[0], top: ca[1] + 40, width: cb[0] - ca[0], height: 24, borderLeft: '4px solid #fff', borderRight: '4px solid #fff', borderBottom: '4px solid #fff', opacity: o}} />
          <Label x={(ca[0] + cb[0]) / 2} y={ca[1] + 110} text="≈ 58 كم فقط" o={o} size={46} color="#fff" bg={C.ink} />
          <div dir="rtl" style={{position: 'absolute', right: 80, top: 230, width: 620, background: 'rgba(13,24,32,0.92)', borderRadius: 16, padding: '26px 34px', color: C.text, opacity: o, boxShadow: '0 20px 60px rgba(0,0,0,0.5)'}}>
            <div style={{fontFamily: DISPLAY, fontSize: 46, marginBottom: 14}}>طول الساحل البحري</div>
            {[['السعودية', 2640, '#8aa3b8'], ['الكويت', 499, '#8aa3b8'], ['العراق', 58, C.ink]].map(([n, v, col], i) => {
              const k = p(t, 63.0 + i * 0.35, 64.0 + i * 0.35, Easing.out(Easing.cubic));
              return (
                <div key={n as string} style={{display: 'flex', alignItems: 'center', gap: 16, margin: '12px 0', fontFamily: BODY, fontWeight: 700, fontSize: 28}}>
                  <div style={{width: 120}}>{n}</div>
                  <div style={{flex: 1}}><div style={{width: `${Math.max(1.2, (v as number) / 2640 * 100) * k}%`, height: 30, background: col as string, borderRadius: 4}} /></div>
                  <div style={{width: 110, textAlign: 'left'}}>{Math.round((v as number) * k)} كم</div>
                </div>
              );
            })}
            <div style={{fontFamily: BODY, fontSize: 18, opacity: 0.6, marginTop: 6}}>المصدر: CIA World Factbook</div>
          </div>
        </>;
      })()}
      <Callout t={t} a={66.8} b={69.3} x={W / 2} y={150} size={92}>حدود لم يرسمها أهلها</Callout>

      {/* ---------- END ---------- */}
      <AbsoluteFill style={{background: `rgba(8,16,22,${0.72 * endDim})`}} />
      {(() => {
        const o1 = win(t, 69.5, 74.6, 0.5);
        const n = Math.round(interpolate(t, [72.0, 73.6], [0, 100], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)}));
        const o2 = p(t, 74.6, 75.3);
        return <>
          {o1 > 0 && (
            <div dir="rtl" style={{position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', opacity: o1, color: C.text}}>
              <div style={{fontFamily: BODY, fontWeight: 600, fontSize: 52, opacity: 0.9}}>هذه الحدود التي نراها ثابتة...</div>
              <div style={{fontFamily: DISPLAY, fontSize: 230, lineHeight: 1.2, color: C.iraq, opacity: p(t, 71.8, 72.2), textShadow: '0 10px 50px rgba(242,193,78,0.35)'}}>عمرها {n} عام</div>
              <div style={{fontFamily: DISPLAY, fontSize: 70, opacity: p(t, 73.4, 73.9)}}>فقط.</div>
            </div>
          )}
          {o2 > 0 && (
            <div dir="rtl" style={{position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', opacity: o2, color: C.text, gap: 18}}>
              <div style={{fontFamily: BODY, fontWeight: 700, fontSize: 30, color: C.iraq, letterSpacing: 2}}>خرائط تحكي</div>
              <div style={{fontFamily: DISPLAY, fontSize: 104, lineHeight: 1.25}}>لماذا حدود العراق بهذا الشكل؟</div>
              <div style={{width: 520 * p(t, 75.0, 75.8), height: 6, background: C.ink, borderRadius: 3}} />
              <div style={{fontFamily: BODY, fontWeight: 600, fontSize: 40, opacity: 0.9}}>أي حدود تريد أن نروي قصتها؟ اكتبها في التعليقات</div>
            </div>
          )}
        </>;
      })()}

      {/* ---------- CHAPTER TAG ---------- */}
      {CHAPTERS.map(([a, b, year, title]) => {
        const o = win(t, a, b, 0.4);
        if (o <= 0) return null;
        return (
          <div key={a} dir="rtl" style={{position: 'absolute', right: 70, top: 50, opacity: o, textAlign: 'right', color: C.text}}>
            {year && <div style={{fontFamily: DISPLAY, fontSize: 84, lineHeight: 1, color: C.iraq, textShadow: '0 4px 20px rgba(0,0,0,0.6)'}}>{year}</div>}
            <div style={{fontFamily: BODY, fontWeight: 700, fontSize: 30, background: 'rgba(13,24,32,0.8)', padding: '6px 16px', borderRadius: 8, marginTop: 8, display: 'inline-block'}}>{title}</div>
          </div>
        );
      })}

      {/* ---------- SUBTITLES ---------- */}
      {sub && t < 74.4 && t < 69.3 && (
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 56, display: 'flex', justifyContent: 'center'}}>
          <div dir="rtl" style={{fontFamily: BODY, fontWeight: 600, fontSize: 42, color: '#fff', background: 'rgba(0,0,0,0.62)', padding: '10px 30px', borderRadius: 10, opacity: p(t, sub.s - 0.05, sub.s + 0.12)}}>
            {sub.t}
          </div>
        </div>
      )}

      {/* ---------- FILM LOOK ---------- */}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)', pointerEvents: 'none'}} />
      <AbsoluteFill style={{
        backgroundImage: `url(${staticFile('noise.png')})`, backgroundSize: '512px 512px', opacity: 0.07, mixBlendMode: 'overlay',
        backgroundPosition: `${Math.floor(random('gx' + f) * 512)}px ${Math.floor(random('gy' + f) * 512)}px`,
      }} />
      <Img src={staticFile('noise.png')} style={{display: 'none'}} />
    </AbsoluteFill>
  );
};
