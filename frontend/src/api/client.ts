import axios from 'axios';
import type { Story, Task, Comment, Epic, StoryStatus, TaskStatus, PipelineTemplate, PipelineConfig } from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Story API
export const storyApi = {
  list: async (boardId?: number, status?: StoryStatus): Promise<Story[]> => {
    const params: Record<string, unknown> = {};
    if (boardId != null) params.board_id = boardId;
    if (status) params.status = status;
    const response = await api.get<Story[]>('/stories', { params });
    return response.data;
  },

  get: async (id: number): Promise<Story> => {
    const response = await api.get<Story>(`/stories/${id}`);
    return response.data;
  },

  create: async (data: {
    board_id: number;
    title: string;
    description?: string;
    acceptance_criteria?: string;
    priority?: number;
    prd_content?: string;
  }): Promise<Story> => {
    const response = await api.post<Story>('/stories', data);
    return response.data;
  },

  update: async (
    id: number,
    data: Partial<{
      title: string;
      description: string;
      acceptance_criteria: string;
      priority: number;
      status: StoryStatus;
    }>
  ): Promise<Story> => {
    const response = await api.put<Story>(`/stories/${id}`, data);
    return response.data;
  },

  transitionStatus: async (id: number, status: StoryStatus): Promise<Story> => {
    const response = await api.post<Story>(`/stories/${id}/status`, { status });
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/stories/${id}`);
  },

  getComments: async (id: number): Promise<Comment[]> => {
    const response = await api.get<Comment[]>(`/stories/${id}/comments`);
    return response.data;
  },
};

// Task API
export const taskApi = {
  list: async (storyId?: number, status?: TaskStatus): Promise<Task[]> => {
    const params: Record<string, unknown> = {};
    if (storyId) params.story_id = storyId;
    if (status) params.status = status;
    const response = await api.get<Task[]>('/tasks', { params });
    return response.data;
  },

  get: async (id: number): Promise<Task> => {
    const response = await api.get<Task>(`/tasks/${id}`);
    return response.data;
  },

  create: async (data: {
    story_id: number;
    title: string;
    description?: string;
    implementation_notes?: string;
    test_scenarios?: string;
  }): Promise<Task> => {
    const response = await api.post<Task>('/tasks', data);
    return response.data;
  },

  update: async (
    id: number,
    data: Partial<{
      title: string;
      description: string;
      implementation_notes: string;
      test_scenarios: string;
      status: TaskStatus;
    }>
  ): Promise<Task> => {
    const response = await api.put<Task>(`/tasks/${id}`, data);
    return response.data;
  },

  transitionStatus: async (id: number, status: TaskStatus): Promise<Task> => {
    const response = await api.post<Task>(`/tasks/${id}/status`, { status });
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/tasks/${id}`);
  },

  getComments: async (id: number): Promise<Comment[]> => {
    const response = await api.get<Comment[]>(`/tasks/${id}/comments`);
    return response.data;
  },
};

// Input API (generic input submission)
export const inputApi = {
  submit: async (content: string, boardId: number, title?: string): Promise<Story> => {
    const response = await api.post<Story>('/input', { content, title, board_id: boardId });
    return response.data;
  },
};

// PRD API (backward-compatible alias)
export const prdApi = {
  submit: async (content: string, boardId: number, title?: string): Promise<Story> => {
    const response = await api.post<Story>('/prd', { content, title, board_id: boardId });
    return response.data;
  },
};

// Epic API
export const epicApi = {
  list: async (boardId?: number): Promise<Epic[]> => {
    const params: Record<string, unknown> = {};
    if (boardId != null) params.board_id = boardId;
    const response = await api.get<Epic[]>('/epics', { params });
    return response.data;
  },

  get: async (id: number): Promise<Epic> => {
    const response = await api.get<Epic>(`/epics/${id}`);
    return response.data;
  },

  create: async (data: {
    board_id: number;
    title: string;
    description?: string;
  }): Promise<Epic> => {
    const response = await api.post<Epic>('/epics', data);
    return response.data;
  },

  update: async (
    id: number,
    data: Partial<{
      title: string;
      description: string;
      status: string;
    }>
  ): Promise<Epic> => {
    const response = await api.put<Epic>(`/epics/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/epics/${id}`);
  },

  getStories: async (id: number): Promise<Story[]> => {
    const response = await api.get<Story[]>(`/epics/${id}/stories`);
    return response.data;
  },
};

// Agent API
export const agentApi = {
  list: async (boardId?: number): Promise<
    Array<{
      id: string;
      type: string;
      name: string;
      description?: string;
      status: 'idle' | 'working' | 'waiting';
      current_task: string | null;
      is_builtin?: boolean;
    }>
  > => {
    const params: Record<string, unknown> = {};
    if (boardId != null) params.board_id = boardId;
    const response = await api.get('/agents', { params });
    return response.data;
  },
};

// Settings API
export interface AppSettings {
  has_api_key: boolean;
  simulate_mode: boolean;
  model: string;
  swarm_status: 'running' | 'stopped' | 'paused';
}

export interface SwarmStatusResponse {
  status: 'running' | 'stopped' | 'paused';
  is_running: boolean;
}

export const settingsApi = {
  get: async (): Promise<AppSettings> => {
    const response = await api.get<AppSettings>('/settings');
    return response.data;
  },

  updateApiKey: async (apiKey: string): Promise<{ success: boolean; message: string; simulate_mode: boolean }> => {
    const response = await api.post('/settings/api-key', { api_key: apiKey });
    return response.data;
  },

  clearApiKey: async (): Promise<{ success: boolean; message: string; simulate_mode: boolean }> => {
    const response = await api.delete('/settings/api-key');
    return response.data;
  },

  setSimulateMode: async (enabled: boolean): Promise<{ success: boolean; simulate_mode: boolean }> => {
    const response = await api.post(`/settings/simulate-mode?enabled=${enabled}`);
    return response.data;
  },

  resetAllData: async (): Promise<{ success: boolean; message: string }> => {
    const response = await api.post('/settings/reset');
    return response.data;
  },

  // Swarm controls
  getSwarmStatus: async (): Promise<SwarmStatusResponse> => {
    const response = await api.get<SwarmStatusResponse>('/settings/swarm/status');
    return response.data;
  },

  startSwarm: async (): Promise<{ success: boolean; status: string; message: string }> => {
    const response = await api.post('/settings/swarm/start');
    return response.data;
  },

  stopSwarm: async (): Promise<{ success: boolean; status: string; message: string }> => {
    const response = await api.post('/settings/swarm/stop');
    return response.data;
  },

  pauseSwarm: async (): Promise<{ success: boolean; status: string; message: string }> => {
    const response = await api.post('/settings/swarm/pause');
    return response.data;
  },

  resumeSwarm: async (): Promise<{ success: boolean; status: string; message: string }> => {
    const response = await api.post('/settings/swarm/resume');
    return response.data;
  },
};

// Chat API
export interface ChatMessage {
  id: number;
  from_agent: string;
  from_agent_name: string;
  to_agent: string | null;
  to_agent_name: string | null;
  content: string;
  story_id: number | null;
  task_id: number | null;
  message_type: string;
  created_at: string;
}

export interface SendMessageRequest {
  content: string;
  to_agent?: string;
  story_id?: number;
  task_id?: number;
  a2a_task_id?: string;
}

export interface SendMessageResponse {
  success: boolean;
  message: string;
  a2a_task_id?: string;
  response?: string;
}

export const chatApi = {
  getMessages: async (limit = 50): Promise<ChatMessage[]> => {
    const response = await api.get<ChatMessage[]>(`/chat?limit=${limit}`);
    return response.data;
  },

  sendMessage: async (request: SendMessageRequest): Promise<SendMessageResponse> => {
    const response = await api.post<SendMessageResponse>('/chat/send', request);
    return response.data;
  },
};

// Agent Management API
export interface AgentSkill {
  id: string;
  name: string;
  description: string;
  tags: string[];
  examples: string[];
}

export interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  default_tools: string[];
  skills: AgentSkill[];
}

export interface AgentTool {
  id: string;
  name: string;
  description: string;
  category: string;
  capabilities: string[];
  is_builtin: boolean;
}

export interface CreateToolRequest {
  id: string;
  name: string;
  description?: string;
  category: string;
  capabilities: string[];
  config?: Record<string, unknown>;
}

export interface UpdateToolRequest {
  name?: string;
  description?: string;
  category?: string;
  capabilities?: string[];
  config?: Record<string, unknown>;
}

export interface DynamicAgent {
  id: string;
  name: string;
  description: string | null;
  template: string | null;
  tools: string[];
  skills: AgentSkill[];
  capabilities: Record<string, boolean>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateAgentRequest {
  id: string;
  name: string;
  description?: string;
  template?: string;
  tools: string[];
  skills: AgentSkill[];
  capabilities?: Record<string, boolean>;
}

export interface UpdateAgentRequest {
  name?: string;
  description?: string;
  tools?: string[];
  skills?: AgentSkill[];
  capabilities?: Record<string, boolean>;
  is_active?: boolean;
}

export const agentManagementApi = {
  // Templates
  getTemplates: async (): Promise<AgentTemplate[]> => {
    const response = await api.get<AgentTemplate[]>('/agent-management/templates');
    return response.data;
  },

  getTemplate: async (templateId: string): Promise<AgentTemplate> => {
    const response = await api.get<AgentTemplate>(`/agent-management/templates/${templateId}`);
    return response.data;
  },

  // Tools
  getTools: async (category?: string): Promise<AgentTool[]> => {
    const params = category ? { category } : {};
    const response = await api.get<AgentTool[]>('/agent-management/tools', { params });
    return response.data;
  },

  getTool: async (toolId: string): Promise<AgentTool> => {
    const response = await api.get<AgentTool>(`/agent-management/tools/${toolId}`);
    return response.data;
  },

  getToolCategories: async (): Promise<string[]> => {
    const response = await api.get<string[]>('/agent-management/tools/categories');
    return response.data;
  },

  createTool: async (request: CreateToolRequest): Promise<AgentTool> => {
    const response = await api.post<AgentTool>('/agent-management/tools', request);
    return response.data;
  },

  updateTool: async (toolId: string, request: UpdateToolRequest): Promise<AgentTool> => {
    const response = await api.put<AgentTool>(`/agent-management/tools/${toolId}`, request);
    return response.data;
  },

  deleteTool: async (toolId: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete(`/agent-management/tools/${toolId}`);
    return response.data;
  },

  // Dynamic Agents
  listAgents: async (isActive?: boolean): Promise<DynamicAgent[]> => {
    const params = isActive !== undefined ? { is_active: isActive } : {};
    const response = await api.get<DynamicAgent[]>('/agent-management/agents', { params });
    return response.data;
  },

  getAgent: async (agentId: string): Promise<DynamicAgent> => {
    const response = await api.get<DynamicAgent>(`/agent-management/agents/${agentId}`);
    return response.data;
  },

  createAgent: async (request: CreateAgentRequest): Promise<DynamicAgent> => {
    const response = await api.post<DynamicAgent>('/agent-management/agents', request);
    return response.data;
  },

  updateAgent: async (agentId: string, request: UpdateAgentRequest): Promise<DynamicAgent> => {
    const response = await api.put<DynamicAgent>(`/agent-management/agents/${agentId}`, request);
    return response.data;
  },

  deleteAgent: async (agentId: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete(`/agent-management/agents/${agentId}`);
    return response.data;
  },

  toggleActivation: async (agentId: string, activate: boolean): Promise<{ success: boolean; is_active: boolean }> => {
    const response = await api.post(`/agent-management/agents/${agentId}/activate?activate=${activate}`);
    return response.data;
  },

  getAgentCard: async (agentId: string): Promise<Record<string, unknown>> => {
    const response = await api.get(`/agent-management/agents/${agentId}/.well-known/agent.json`);
    return response.data;
  },
};

// Simulate API
export const simulateApi = {
  generate: async (boardId: number, epicId?: number, count?: number): Promise<{ success: boolean; count: number; items: unknown[] }> => {
    const response = await api.post(`/boards/${boardId}/simulate`, {
      epic_id: epicId,
      count: count ?? 5,
    });
    return response.data;
  },
};

// Pipeline API (templates only)
export const pipelineApi = {
  getTemplates: async (): Promise<PipelineTemplate[]> => {
    const response = await api.get<PipelineTemplate[]>('/pipeline/templates');
    return response.data;
  },
};

// Board API
export const boardApi = {
  list: async (): Promise<PipelineConfig[]> => {
    const response = await api.get<PipelineConfig[]>('/boards');
    return response.data;
  },

  get: async (id: number): Promise<PipelineConfig> => {
    const response = await api.get<PipelineConfig>(`/boards/${id}`);
    return response.data;
  },

  create: async (templateId: string, name?: string): Promise<PipelineConfig> => {
    const response = await api.post<PipelineConfig>('/boards', {
      template_id: templateId,
      name,
    });
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/boards/${id}`);
  },
};

export default api;
