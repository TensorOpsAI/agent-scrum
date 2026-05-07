import { useCallback, useEffect, useRef, useState } from 'react';
import { useStoryStore } from '../store/storyStore';
import { eventBus } from '../lib/eventBus';
import { settingsApi } from '../api/client';
import {
  DEMO_TIMELINE,
  DEMO_STORIES,
  DEMO_TASKS,
  DEMO_DURATION_MS,
  type ReplayStep,
} from '../fixtures/demoReplay';
import type { Story, Task } from '../types';

const REPLAY_DONE_KEY = 'agent-scrum:demo-replay-played';

function buildStory(id: number): Story {
  const seed = DEMO_STORIES[id];
  return { ...seed, created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
}

function buildTask(id: number): Task {
  const seed = DEMO_TASKS[id];
  return { ...seed, created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
}

interface UseDemoReplayResult {
  isReplaying: boolean;
  hasPlayed: boolean;
  play: () => void;
  skip: () => void;
}

/**
 * Plays a pre-recorded "agents shipping a feature" run on first visit.
 * Auto-triggers when there's no API key + the board is empty.
 * Mutates the story store directly and emits chat events on the eventBus.
 */
export function useDemoReplay(boardId: number | null): UseDemoReplayResult {
  const [isReplaying, setIsReplaying] = useState(false);
  const [hasPlayed, setHasPlayed] = useState(
    () => typeof window !== 'undefined' && window.localStorage.getItem(REPLAY_DONE_KEY) === 'true'
  );
  const timersRef = useRef<number[]>([]);

  const dispatch = useCallback((step: ReplayStep) => {
    const store = useStoryStore.getState();
    switch (step.type) {
      case 'story-add': {
        const story = buildStory(step.data.storyId);
        store.addStory(story);
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
        store.addTask(buildTask(step.data.taskId));
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
    // Reset agents to idle
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
    if (isReplaying) return;
    cleanup();
    removeDemoData(); // Clean any leftovers from a previous play
    setIsReplaying(true);
    eventBus.emit('replay:state', { isReplaying: true });

    DEMO_TIMELINE.forEach(({ t, step }) => {
      const id = window.setTimeout(() => dispatch(step), t);
      timersRef.current.push(id);
    });

    const endId = window.setTimeout(finish, DEMO_DURATION_MS + 500);
    timersRef.current.push(endId);
  }, [isReplaying, cleanup, removeDemoData, dispatch, finish]);

  // Auto-play on mount when conditions are right
  useEffect(() => {
    if (boardId == null) return;
    if (hasPlayed) return;

    const hasApiKey = !!settingsApi.getLocalApiKey();
    const realStoryCount = useStoryStore.getState().stories.filter((s) => s.id > 0).length;

    // Only autoplay for first-run users: no key AND no real stories
    if (hasApiKey || realStoryCount > 0) return;

    // Slight delay so the page paints first
    const id = window.setTimeout(() => play(), 600);
    return () => window.clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [boardId, hasPlayed]);

  // Cleanup on unmount
  useEffect(() => () => cleanup(), [cleanup]);

  return { isReplaying, hasPlayed, play, skip };
}
