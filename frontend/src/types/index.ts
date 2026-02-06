// StoryStatus is now a plain string - columns are defined by the active pipeline
export type StoryStatus = string;

export type TaskStatus =
  | 'draft'
  | 'pending_review'
  | 'ready_for_development'
  | 'in_progress'
  | 'code_review'
  | 'ready_for_qa'
  | 'qa_in_progress'
  | 'done';

// Built-in agent types
export type BuiltinAgentType =
  | 'product_owner'
  | 'tech_lead'
  | 'developer'
  | 'code_reviewer'
  | 'qa'
  | 'client';

// AgentType can be built-in or dynamic (any string)
export type AgentType = BuiltinAgentType | string;

export interface Story {
  id: number;
  board_id: number;
  title: string;
  description: string | null;
  acceptance_criteria: string | null;
  status: StoryStatus;
  priority: number;
  prd_content: string | null;
  created_at: string;
  updated_at: string;
  task_count: number;
  completed_task_count: number;
}

export interface Task {
  id: number;
  story_id: number;
  title: string;
  description: string | null;
  implementation_notes: string | null;
  test_scenarios: string | null;
  status: TaskStatus;
  assigned_agent: AgentType | null;
  created_at: string;
  updated_at: string;
}

export interface Comment {
  id: number;
  story_id: number | null;
  task_id: number | null;
  agent_type: AgentType;
  content: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface Agent {
  id: string;
  type: AgentType;
  name: string;
  description?: string;
  status: 'idle' | 'working' | 'waiting';
  currentTask: string | null;
  is_builtin?: boolean;
}

export interface WebSocketMessage {
  event: string;
  data: unknown;
}

// Pipeline types
export interface PipelineColumn {
  key: string;
  label: string;
  color: string;
  position: number;
}

export interface PipelineTemplate {
  template_id: string;
  name: string;
  columns: PipelineColumn[];
  agent_automation: boolean;
  item_noun: string;
  has_tasks: boolean;
}

export interface PipelineConfig {
  id: number;
  template_id: string;
  name: string;
  columns: PipelineColumn[];
  agent_automation: boolean;
  item_noun: string;
  has_tasks: boolean;
  story_count?: number;
}

// Helper: get the label for a status from pipeline columns
export function getStatusLabel(status: string, columns: PipelineColumn[]): string {
  const col = columns.find((c) => c.key === status);
  return col?.label ?? status.split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

// Helper: get the color for a status from pipeline columns
export function getStatusColor(status: string, columns: PipelineColumn[]): string {
  const col = columns.find((c) => c.key === status);
  return col?.color ?? 'bg-gray-600';
}

// Hardcoded label maps kept for backward compat / task status
export const STORY_STATUS_LABELS: Record<string, string> = {
  backlog: 'Backlog',
  ready_for_breakdown: 'Ready for Breakdown',
  in_breakdown: 'In Breakdown',
  tasks_in_review: 'Tasks in Review',
  in_development: 'In Development',
  in_qa: 'In QA',
  done: 'Done',
};

export const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  draft: 'Draft',
  pending_review: 'Pending Review',
  ready_for_development: 'Ready for Dev',
  in_progress: 'In Progress',
  code_review: 'Code Review',
  ready_for_qa: 'Ready for QA',
  qa_in_progress: 'QA In Progress',
  done: 'Done',
};

export const AGENT_LABELS: Record<BuiltinAgentType, string> = {
  product_owner: 'Product Owner',
  tech_lead: 'Tech Lead',
  developer: 'Developer',
  code_reviewer: 'Code Reviewer',
  qa: 'QA',
  client: 'Human',
};

export const AGENT_COLORS: Record<BuiltinAgentType, string> = {
  product_owner: 'bg-blue-500',
  tech_lead: 'bg-purple-500',
  developer: 'bg-green-500',
  code_reviewer: 'bg-orange-500',
  qa: 'bg-pink-500',
  client: 'bg-cyan-500',
};

// Helper functions for dynamic agents
export function getAgentLabel(type: AgentType, name?: string): string {
  if (type in AGENT_LABELS) {
    return AGENT_LABELS[type as BuiltinAgentType];
  }
  // For dynamic agents, use the name or format the type
  return name || type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

export function getAgentColor(type: AgentType): string {
  if (type in AGENT_COLORS) {
    return AGENT_COLORS[type as BuiltinAgentType];
  }
  // Generate a color based on the type string hash
  const colors = ['bg-indigo-500', 'bg-teal-500', 'bg-amber-500', 'bg-rose-500', 'bg-lime-500', 'bg-sky-500'];
  const hash = type.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return colors[hash % colors.length];
}
