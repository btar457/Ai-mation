import {Composition} from 'remotion';
import {Engine, TOTAL} from './Engine';
export const RemotionRoot = () => (
  <Composition id="Engine" component={Engine} durationInFrames={TOTAL} fps={30} width={1920} height={1080} />
);
