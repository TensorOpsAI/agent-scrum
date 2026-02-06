import { create } from 'zustand';
import type { Story, Task, Agent, StoryStatus, TaskStatus } from '../types';
import { storyApi, taskApi, agentApi } from '../api/client';

interface StoryState {
  stories: Story[];
  tasks: Task[];
  agents: Agent[];
  selectedStoryId: number | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchStories: (boardId?: number) => Promise<void>;
  fetchTasks: (storyId?: number) => Promise<void>;
  fetchAgents: () => Promise<void>;
  setSelectedStory: (id: number | null) => void;
  addStory: (story: Story) => void;
  updateStory: (story: Story) => void;
  addTask: (task: Task) => void;
  updateTask: (task: Task) => void;
  updateAgentStatus: (agentId: string, status: Agent['status'], currentTask?: string | null) => void;
  transitionStoryStatus: (id: number, status: StoryStatus) => Promise<void>;
  transitionTaskStatus: (id: number, status: TaskStatus) => Promise<void>;
}

// Fallback agents while loading from backend
const fallbackAgents: Agent[] = [
  { id: 'product_owner', type: 'product_owner', name: 'Product Owner', status: 'idle', currentTask: null, is_builtin: true },
  { id: 'tech_lead', type: 'tech_lead', name: 'Tech Lead', status: 'idle', currentTask: null, is_builtin: true },
  { id: 'developer', type: 'developer', name: 'Developer', status: 'idle', currentTask: null, is_builtin: true },
  { id: 'code_reviewer', type: 'code_reviewer', name: 'Code Reviewer', status: 'idle', currentTask: null, is_builtin: true },
  { id: 'qa', type: 'qa', name: 'QA', status: 'idle', currentTask: null, is_builtin: true },
];

export const useStoryStore = create<StoryState>((set, get) => ({
  stories: [],
  tasks: [],
  agents: fallbackAgents,
  selectedStoryId: null,
  isLoading: false,
  error: null,

  fetchStories: async (boardId?: number) => {
    // Only show loading spinner if we have no stories yet (first load)
    const hasStories = get().stories.length > 0;
    if (!hasStories) {
      set({ isLoading: true, error: null });
    }
    try {
      const stories = await storyApi.list(boardId);
      set({ stories, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to fetch stories', isLoading: false });
      console.error('Error fetching stories:', error);
    }
  },

  fetchTasks: async (storyId?: number) => {
    set({ isLoading: true, error: null });
    try {
      const tasks = await taskApi.list(storyId);
      set({ tasks, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to fetch tasks', isLoading: false });
      console.error('Error fetching tasks:', error);
    }
  },

  fetchAgents: async () => {
    try {
      const agentsData = await agentApi.list();
      // Transform backend response to frontend Agent format
      const agents: Agent[] = agentsData.map((a: {
        id: string;
        type: string;
        name: string;
        description?: string;
        status: 'idle' | 'working' | 'waiting';
        current_task?: string | null;
        is_builtin?: boolean;
      }) => ({
        id: a.id,
        type: a.type,
        name: a.name,
        description: a.description,
        status: a.status,
        currentTask: a.current_task || null,
        is_builtin: a.is_builtin,
      }));
      set({ agents });
    } catch (error) {
      console.error('Error fetching agents:', error);
      // Keep fallback agents on error
    }
  },

  setSelectedStory: (id: number | null) => {
    set({ selectedStoryId: id });
    if (id) {
      get().fetchTasks(id);
    }
  },

  addStory: (story: Story) => {
    set((state) => {
      // Check if story already exists to prevent duplicates
      const existingIndex = state.stories.findIndex((s) => s.id === story.id);
      if (existingIndex !== -1) {
        // Update existing story instead of adding duplicate
        return {
          stories: state.stories.map((s) => (s.id === story.id ? story : s)),
        };
      }
      return {
        stories: [story, ...state.stories],
      };
    });
  },

  updateStory: (story: Story) => {
    set((state) => ({
      stories: state.stories.map((s) => (s.id === story.id ? story : s)),
    }));
  },

  addTask: (task: Task) => {
    set((state) => {
      // Check if task already exists to prevent duplicates
      const existingIndex = state.tasks.findIndex((t) => t.id === task.id);
      if (existingIndex !== -1) {
        // Update existing task instead of adding duplicate
        return {
          tasks: state.tasks.map((t) => (t.id === task.id ? task : t)),
        };
      }
      return {
        tasks: [task, ...state.tasks],
      };
    });
  },

  updateTask: (task: Task) => {
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === task.id ? task : t)),
    }));
  },

  updateAgentStatus: (agentId: string, status: Agent['status'], currentTask?: string | null) => {
    set((state) => ({
      agents: state.agents.map((a) =>
        // Match by ID or type (for backward compatibility with WebSocket events)
        (a.id === agentId || a.type === agentId)
          ? { ...a, status, currentTask: currentTask ?? a.currentTask }
          : a
      ),
    }));
  },

  transitionStoryStatus: async (id: number, status: StoryStatus) => {
    try {
      const updatedStory = await storyApi.transitionStatus(id, status);
      get().updateStory(updatedStory);
    } catch (error) {
      console.error('Error transitioning story status:', error);
      set({ error: 'Failed to transition story status' });
    }
  },

  transitionTaskStatus: async (id: number, status: TaskStatus) => {
    try {
      const updatedTask = await taskApi.transitionStatus(id, status);
      get().updateTask(updatedTask);
    } catch (error) {
      console.error('Error transitioning task status:', error);
      set({ error: 'Failed to transition task status' });
    }
  },
}));
