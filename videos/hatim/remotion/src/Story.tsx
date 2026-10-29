import React, {useEffect, useState} from 'react';
import {
  AbsoluteFill, Audio, Easing, interpolate, OffthreadVideo, random, Sequence, staticFile,
  useCurrentFrame, continueRender, delayRender,
} from 'remotion';
import '@fontsource/noto-kufi-arabic/700.css';
import '@fontsource/noto-kufi-arabic/900.css';
import '@fontsource/amiri/700.css';
import TL from './timeline.json';

const FPS = 30;
export const TOTAL = Math.ceil(TL.total * FPS);
const XF = 8; // crossfade frames
type Scene = {n: number; start: number; dur: number; clip: string};
const SCENES = TL.scenes as Scene[];
const CAPS = TL.caps as {t: string; s: number; e: number; who: string}[];
const KUFI = '"Noto Kufi Arabic"';
const AMIRI = 'Amiri';

const p = (t: number, a: number, b: number, e = Easing.inOut(Easing.cubic)) =>
  interpolate(t, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: e});

const NIGHT_FIRE = new Set([5, 6, 7, 8, 11, 13, 14, 15]);
const DUST = new Set([4, 16, 17, 19]);

// floating particles: embers rise at night by the fire, dust drifts in desert light
const Particles: React.FC<{kind: 'ember' | 'dust'; seed: number}> = ({kind, seed}) => {
  const f = useCurrentFrame();
  const n = kind === 'ember' ? 26 : 34;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {Array.from({length: n}).map((_, i) => {
        const r = (k: string) => random(`${seed}-${kind}-${i}-${k}`);
        const life = (kind === 'ember' ? 90 : 160) * (0.6 + r('l'));
        const ph = ((f + r('o') * life) % life) / life;
        const x = kind === 'ember'
          ? 540 + (r('x') - 0.5) * 900 + Math.sin(ph * 6 + r('w') * 6) * 40
          : (r('x') * 1300 - 110) + ph * 220;
        const y = kind === 'ember' ? 1900 - ph * (900 + r('h') * 700) : 300 + r('y') * 1500 + Math.sin(ph * 4 + i) * 30;
        const s = kind === 'ember' ? 3 + r('s') * 5 : 2 + r('s') * 4;
        const o = Math.sin(ph * Math.PI) * (kind === 'ember' ? 0.95 : 0.5);
        return (
          <div key={i} style={{
            position: 'absolute', left: x, top: y, width: s, height: s, borderRadius: '50%', opacity: o,
            background: kind === 'ember' ? '#ffb347' : '#fff3d6',
            boxShadow: kind === 'ember' ? '0 0 10px 3px rgba(255,130,40,0.85)' : '0 0 6px rgba(255,240,210,0.6)',
          }} />
        );
      })}
    </AbsoluteFill>
  );
};

const SceneView: React.FC<{s: Scene}> = ({s}) => {
  const f = useCurrentFrame();
  const len = Math.round(s.dur * FPS) + XF;
  const fadeIn = s.n === 1 ? 1 : p(f, 0, XF);
  const zoom = 1 + 0.035 * (f / len);
  const flicker = NIGHT_FIRE.has(s.n) ? 0.1 + 0.06 * Math.sin(f * 0.9) + 0.04 * Math.sin(f * 2.3 + 1) : 0;
  return (
    <AbsoluteFill style={{opacity: fadeIn}}>
      <AbsoluteFill style={{transform: `scale(${zoom})`}}>
        <OffthreadVideo src={staticFile(s.clip)} muted style={{width: 1080, height: 1920, objectFit: 'cover'}} />
      </AbsoluteFill>
      {flicker > 0 && (
        <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 85%, rgba(255,140,50,${flicker}) 0%, rgba(255,100,30,${flicker * 0.4}) 40%, transparent 75%)`, mixBlendMode: 'screen'}} />
      )}
      {NIGHT_FIRE.has(s.n) && <Particles kind="ember" seed={s.n} />}
      {DUST.has(s.n) && <Particles kind="dust" seed={s.n} />}
    </AbsoluteFill>
  );
};

export const Story: React.FC = () => {
  const [h] = useState(() => delayRender('fonts'));
  useEffect(() => {
    Promise.all([
      document.fonts.load('900 60px "Noto Kufi Arabic"', 'حاتم'),
      document.fonts.load('700 60px "Noto Kufi Arabic"', 'حاتم'),
      document.fonts.load('700 60px Amiri', 'حاتم'),
    ]).then(() => document.fonts.ready).then(() => continueRender(h));
  }, [h]);

  const f = useCurrentFrame();
  const t = f / FPS;
  const cap = CAPS.find((c) => t >= c.s - 0.03 && t < c.e + 0.06);
  const last = SCENES[SCENES.length - 1];
  const endT = last.start + last.dur - 2.8;
  const endO = p(t, endT, endT + 0.6);

  return (
    <AbsoluteFill style={{background: '#000'}}>
      <Audio src={staticFile('mix.wav')} />
      {SCENES.map((s) => (
        <Sequence key={s.n} from={Math.round(s.start * FPS)} durationInFrames={Math.round(s.dur * FPS) + XF}>
          <SceneView s={s} />
        </Sequence>
      ))}

      {/* cinematic grade: vignette + letterbox gradient for caption legibility */}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, transparent 55%, rgba(0,0,0,0.55) 100%)'}} />
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.35) 0%, transparent 14%, transparent 62%, rgba(0,0,0,0.55) 100%)'}} />

      {/* opening framing line */}
      {t < 3.6 && (
        <div dir="rtl" style={{position: 'absolute', top: 150, left: 0, right: 0, textAlign: 'center', opacity: Math.min(p(t, 0.2, 0.7), 1 - p(t, 3.0, 3.6)),
          fontFamily: AMIRI, fontWeight: 700, fontSize: 46, color: '#f3d58a', textShadow: '0 2px 12px rgba(0,0,0,0.9)'}}>
          يُروى في كتب الأدب العربي…
        </div>
      )}

      {/* captions: 2-3 words, bold white with dark outline, inside the safe band */}
      {cap && t < endT && (() => {
        const k = p(t, cap.s - 0.03, cap.s + 0.1, Easing.out(Easing.back(2)));
        return (
          <div dir="rtl" style={{position: 'absolute', top: 1330, left: 60, right: 60, textAlign: 'center'}}>
            <span style={{
              display: 'inline-block', transform: `scale(${0.85 + 0.15 * k})`, opacity: k,
              fontFamily: KUFI, fontWeight: 900, fontSize: 74, lineHeight: 1.45,
              color: cap.who === 'narr' ? '#ffe39a' : '#ffffff',
              WebkitTextStroke: '10px rgba(0,0,0,0.9)', paintOrder: 'stroke fill',
              textShadow: '0 6px 18px rgba(0,0,0,0.7)',
            }}>{cap.t}</span>
          </div>
        );
      })()}

      {/* cliffhanger end card */}
      {endO > 0 && (
        <AbsoluteFill style={{background: `rgba(0,0,0,${0.55 * endO})`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 26}}>
          <div dir="rtl" style={{opacity: endO, transform: `scale(${0.9 + 0.1 * endO})`, fontFamily: KUFI, fontWeight: 900, fontSize: 112, color: '#fff',
            WebkitTextStroke: '8px rgba(0,0,0,0.85)', paintOrder: 'stroke fill', textShadow: '0 0 40px rgba(255,170,60,0.55)'}}>
            الجزء الثاني…
          </div>
          <div dir="rtl" style={{opacity: p(t, endT + 0.6, endT + 1.1), fontFamily: KUFI, fontWeight: 700, fontSize: 46, color: '#f3d58a', textShadow: '0 2px 10px #000'}}>
            تابعني حتى لا يفوتك ردّ حاتم
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
