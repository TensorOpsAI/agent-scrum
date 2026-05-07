/**
 * Lightweight in-process event bus used by demo replay mode.
 * Lets the replay hook fan out chat messages and story pulses to
 * components that normally listen to WebSocket events.
 */

import type { ChatMessage } from '../api/client';

type BusEvents = {
  'replay:chat': ChatMessage;
  'replay:story-pulse': { storyId: number };
  'replay:state': { isReplaying: boolean };
};

class TypedEventBus {
  private target = new EventTarget();

  emit<K extends keyof BusEvents>(event: K, data: BusEvents[K]) {
    this.target.dispatchEvent(new CustomEvent(event, { detail: data }));
  }

  on<K extends keyof BusEvents>(event: K, handler: (data: BusEvents[K]) => void) {
    const listener = (e: Event) => handler((e as CustomEvent<BusEvents[K]>).detail);
    this.target.addEventListener(event, listener);
    return () => this.target.removeEventListener(event, listener);
  }
}

export const eventBus = new TypedEventBus();
