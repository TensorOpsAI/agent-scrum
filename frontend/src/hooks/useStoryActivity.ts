import { useEffect, useState } from 'react';
import { useWebSocket } from './useWebSocket';
import type { Story } from '../types';

const PULSE_DURATION_MS = 2500;

/**
 * Tracks story IDs that have recently been updated via WebSocket.
 * Used by StoryCard to render a brief pulse animation when an agent
 * touches a story, giving the board a sense of liveness.
 */
export function useStoryActivity(): Set<number> {
  const { lastMessage } = useWebSocket();
  const [activeIds, setActiveIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (!lastMessage) return;
    if (lastMessage.event !== 'story:updated' && lastMessage.event !== 'story:created') return;

    const story = lastMessage.data as Story;
    if (!story?.id) return;

    setActiveIds((prev) => {
      const next = new Set(prev);
      next.add(story.id);
      return next;
    });

    const id = story.id;
    const timer = window.setTimeout(() => {
      setActiveIds((prev) => {
        if (!prev.has(id)) return prev;
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }, PULSE_DURATION_MS);

    return () => window.clearTimeout(timer);
  }, [lastMessage]);

  return activeIds;
}
