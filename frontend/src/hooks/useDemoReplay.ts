import { useCallback, useEffect, useRef, useState } from 'react';
import { useStoryStore } from '../store/storyStore';
import { eventBus } from '../lib/eventBus';
import { settingsApi } from '../api/client';
import { DEMO_TIMELINES, type ReplayStep, type DemoTimeline } from '../fixtures/demoReplay';
import type { Story, Task } from '../types';

const REPLAY_DONE_KEY = 'agent-scrum:demo-replay-played';
/** How long to wait before auto-playing on first run, so the user can orient. */
const AUTOPLAY_DELAY_MS = 3500;

function hydrate<T extends { id: number }>(seed: Omit<T, 'created_at' | 'updated_at'>): T {
  const ts = new Date().toISOString();
  return { ...seed, created_at: ts, updated_at: ts } as unknown as T;
}

interface UseDemoReplayResult {
  isReplaying: boolean;
  hasPlayed: boolean;
  isSupported: boolean;
  headline: string | null;
  play: () => void;
  skip: () => void;
}

/**
 * Plays a pre-recorded run on first visit.
 * Auto-triggers when there's no API key + the board is empty + we have
 * a timeline registered for the current template.
 */
export function useDemoReplay(boardId: number | null, templateId: string | null): UseDemoReplayResult {
  const [isReplaying, setIsReplaying] = useState(false);
  const [hasPlayed, setHasPlayed] = useState(
    () => typeof window !== 'undefined' && window.localStorage.getItem(REPLAY_DONE_KEY) === 'true'
  );
  const timersRef = useRef<number[]>([]);

  const timeline: DemoTimeline | null = templateId ? DEMO_TIMELINES[templateId] ?? null : null;

  const dispatch = useCallback((step: ReplayStep, tl: DemoTimeline) => {
    const store = useStoryStore.getState();
    switch (step.type) {
      case 'story-add': {
        const seed = tl.stories[step.data.storyId];
        if (!seed) return;
        store.addStory(hydrate<Story>(seed));
        break;
      }
      case 'story-update': {
        const existing = useStoryStore.getState().stories.find((s) => s.id === step.data.storyId);
        if (!existing) return;
        store.updateStory({
          ...existing,
          status: step.data.status,
          task_count: step.data.taskCount ?? existing.task_count,
          completed_task_count: step.data.completedCount ?? existing.completed_task_count,
          updated_at: new Date().toISOString(),
        });
        break;
      }
      case 'task-add': {
        const seed = tl.tasks[step.data.taskId];
        if (!seed) return;
        store.addTask(hydrate<Task>(seed));
        break;
      }
      case 'agent-status': {
        store.updateAgentStatus(step.data.agentId, step.data.status, step.data.task ?? null);
        break;
      }
      case 'chat': {
        eventBus.emit('replay:chat', step.data);
        break;
      }
      case 'story-pulse': {
        eventBus.emit('replay:story-pulse', { storyId: step.data.storyId });
        break;
      }
    }
  }, []);

  const cleanup = useCallback(() => {
    timersRef.current.forEach((id) => window.clearTimeout(id));
    timersRef.current = [];
  }, []);

  const removeDemoData = useCallback(() => {
    const store = useStoryStore.getState();
    const realStories = store.stories.filter((s) => s.id > 0);
    useStoryStore.setState({ stories: realStories });
    const realAgents = store.agents.map((a) => ({ ...a, status: 'idle' as const, currentTask: null }));
    useStoryStore.setState({ agents: realAgents });
  }, []);

  const finish = useCallback(() => {
    setIsReplaying(false);
    eventBus.emit('replay:state', { isReplaying: false });
    window.localStorage.setItem(REPLAY_DONE_KEY, 'true');
    setHasPlayed(true);
  }, []);

  const skip = useCallback(() => {
    cleanup();
    removeDemoData();
    finish();
  }, [cleanup, removeDemoData, finish]);

  const play = useCallback(() => {
    if (isReplaying || !timeline) return;
    cleanup();
    removeDemoData();
    setIsReplaying(true);
    eventBus.emit('replay:state', { isReplaying: true });

    timeline.steps.forEach(({ t, step }) => {
      const id = window.setTimeout(() => dispatch(step, timeline), t);
      timersRef.current.push(id);
    });

    const endId = window.setTimeout(finish, timeline.durationMs + 1000);
    timersRef.current.push(endId);
  }, [isReplaying, timeline, cleanup, removeDemoData, dispatch, finish]);

  // Auto-play on first run
  useEffect(() => {
    if (boardId == null || !timeline) return;
    if (hasPlayed) return;

    const hasApiKey = !!settingsApi.getLocalApiKey();
    const realStoryCount = useStoryStore.getState().stories.filter((s) => s.id > 0).length;
    if (hasApiKey || realStoryCount > 0) return;

    const id = window.setTimeout(() => play(), AUTOPLAY_DELAY_MS);
    return () => window.clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [boardId, templateId, hasPlayed]);

  useEffect(() => () => cleanup(), [cleanup]);

  return {
    isReplaying,
    hasPlayed,
    isSupported: timeline != null,
    headline: timeline?.headline ?? null,
    play,
    skip,
  };
}
