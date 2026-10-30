import {Composition} from 'remotion';
import {Story, TOTAL} from './Story';
export const RemotionRoot = () => (
  <Composition id="Story" component={Story} durationInFrames={TOTAL} fps={30} width={1920} height={1080} />
);
