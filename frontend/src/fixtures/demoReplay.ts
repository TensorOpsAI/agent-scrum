/**
 * Pre-recorded timeline used by the demo replay mode on first visit.
 * Each step fires at `t` ms from replay start. Steps mutate the store
 * directly (stories/tasks/agents) and emit chat through the event bus.
 *
 * Designed for the software_dev template: a "user auth" PRD comes in,
 * PO breaks it into stories, devs build, reviewer + QA close it out.
 */

import type { Story, Task } from '../types';

type StorySeed = Omit<Story, 'created_at' | 'updated_at'>;

const now = () => new Date().toISOString();

// Synthetic, demo-only ids (negative so they never collide with real ones)
const BOARD_ID = -1;

export const DEMO_STORIES: Record<number, StorySeed> = {
  [-101]: {
    id: -101, board_id: BOARD_ID, epic_id: null,
    title: 'Email + password sign-up flow',
    description: 'Allow new users to register with email and password, send a confirmation email.',
    acceptance_criteria: null,
    status: 'backlog', priority: 1, prd_content: null,
    task_count: 0, completed_task_count: 0,
  },
  [-102]: {
    id: -102, board_id: BOARD_ID, epic_id: null,
    title: 'Login with rate limiting',
    description: 'Auth endpoint with bcrypt + sliding-window rate limit per IP.',
    acceptance_criteria: null,
    status: 'backlog', priority: 1, prd_content: null,
    task_count: 0, completed_task_count: 0,
  },
  [-103]: {
    id: -103, board_id: BOARD_ID, epic_id: null,
    title: 'Password reset via email link',
    description: 'Tokenized reset link with 30-minute expiry.',
    acceptance_criteria: null,
    status: 'backlog', priority: 2, prd_content: null,
    task_count: 0, completed_task_count: 0,
  },
};

export const DEMO_TASKS: Record<number, Omit<Task, 'created_at' | 'updated_at'>> = {
  [-201]: { id: -201, story_id: -102, title: 'Hash & verify passwords with bcrypt', description: null, implementation_notes: null, test_scenarios: null, status: 'in_progress', assigned_agent: 'developer' },
  [-202]: { id: -202, story_id: -102, title: 'Sliding-window rate limiter middleware', description: null, implementation_notes: null, test_scenarios: null, status: 'in_progress', assigned_agent: 'developer' },
  [-203]: { id: -203, story_id: -102, title: 'Login endpoint integration tests', description: null, implementation_notes: null, test_scenarios: null, status: 'pending_review', assigned_agent: 'qa' },
};

const msg = (id: number, from: string, fromName: string, content: string, opts: { to?: string; toName?: string; storyId?: number; taskId?: number } = {}) => ({
  type: 'chat' as const,
  data: {
    id,
    from_agent: from,
    from_agent_name: fromName,
    to_agent: opts.to ?? null,
    to_agent_name: opts.toName ?? null,
    content,
    story_id: opts.storyId ?? null,
    task_id: opts.taskId ?? null,
    message_type: 'text',
    created_at: now(),
  },
});

export type ReplayStep =
  | { type: 'agent-status'; data: { agentId: string; status: 'idle' | 'working' | 'waiting'; task?: string | null } }
  | { type: 'story-add'; data: { storyId: number } }
  | { type: 'story-update'; data: { storyId: number; status: string; taskCount?: number; completedCount?: number } }
  | { type: 'task-add'; data: { taskId: number } }
  | { type: 'chat'; data: ReturnType<typeof msg>['data'] }
  | { type: 'story-pulse'; data: { storyId: number } };

/**
 * Timeline. Times are ms from replay start. ~35 seconds total.
 */
export const DEMO_TIMELINE: Array<{ t: number; step: ReplayStep }> = [
  // === Phase 1: PO receives the PRD and breaks it down (0-8s) ===
  { t:   200, step: { type: 'agent-status', data: { agentId: 'product_owner', status: 'working', task: 'Breaking down auth PRD' } } },
  { t:   300, step: msg(-1, 'product_owner', 'Product Owner', 'Got the auth PRD. Breaking this into 3 stories — sign-up, login, and password reset.') },
  { t:  1500, step: { type: 'story-add', data: { storyId: -101 } } },
  { t:  1500, step: { type: 'story-pulse', data: { storyId: -101 } } },
  { t:  2400, step: { type: 'story-add', data: { storyId: -102 } } },
  { t:  2400, step: { type: 'story-pulse', data: { storyId: -102 } } },
  { t:  3300, step: { type: 'story-add', data: { storyId: -103 } } },
  { t:  3300, step: { type: 'story-pulse', data: { storyId: -103 } } },
  { t:  3800, step: msg(-2, 'product_owner', 'Product Owner', 'Stories created. @Tech Lead can you scope the login one first? It has the most security surface area.', { to: 'tech_lead', toName: 'Tech Lead', storyId: -102 }) },
  { t:  4400, step: { type: 'agent-status', data: { agentId: 'product_owner', status: 'idle', task: null } } },

  // === Phase 2: Tech Lead scopes login (8-14s) ===
  { t:  5000, step: { type: 'agent-status', data: { agentId: 'tech_lead', status: 'working', task: 'Scoping login story' } } },
  { t:  5400, step: { type: 'story-update', data: { storyId: -102, status: 'ready_for_breakdown', taskCount: 0, completedCount: 0 } } },
  { t:  5400, step: { type: 'story-pulse', data: { storyId: -102 } } },
  { t:  6200, step: msg(-3, 'tech_lead', 'Tech Lead', 'Bcrypt for hashing, sliding-window rate limit per IP. Three tasks. @Developer take it.', { to: 'developer', toName: 'Developer', storyId: -102 }) },
  { t:  7000, step: { type: 'story-update', data: { storyId: -102, status: 'in_breakdown', taskCount: 3, completedCount: 0 } } },
  { t:  7000, step: { type: 'story-pulse', data: { storyId: -102 } } },
  { t:  7800, step: { type: 'agent-status', data: { agentId: 'tech_lead', status: 'idle', task: null } } },

  // === Phase 3: Developer implements (14-22s) ===
  { t:  8400, step: { type: 'agent-status', data: { agentId: 'developer', status: 'working', task: 'Implementing login endpoint' } } },
  { t:  9000, step: { type: 'task-add', data: { taskId: -201 } } },
  { t:  9800, step: { type: 'task-add', data: { taskId: -202 } } },
  { t: 10600, step: { type: 'task-add', data: { taskId: -203 } } },
  { t: 11400, step: msg(-4, 'developer', 'Developer', 'Tasks broken out. Hashing + rate limiter look straightforward. Going to write the integration tests last.', { storyId: -102 }) },
  { t: 12200, step: { type: 'story-update', data: { storyId: -102, status: 'in_development', taskCount: 3, completedCount: 0 } } },
  { t: 12200, step: { type: 'story-pulse', data: { storyId: -102 } } },
  { t: 13800, step: { type: 'story-update', data: { storyId: -102, status: 'in_development', taskCount: 3, completedCount: 1 } } },
  { t: 13800, step: { type: 'story-pulse', data: { storyId: -102 } } },
  { t: 15400, step: msg(-5, 'developer', 'Developer', 'Login + bcrypt landed. Pushing for review.', { to: 'code_reviewer', toName: 'Code Reviewer', storyId: -102 }) },
  { t: 15800, step: { type: 'story-update', data: { storyId: -102, status: 'tasks_in_review', taskCount: 3, completedCount: 2 } } },
  { t: 15800, step: { type: 'story-pulse', data: { storyId: -102 } } },
  { t: 16400, step: { type: 'agent-status', data: { agentId: 'developer', status: 'waiting', task: 'Awaiting review' } } },

  // === Phase 4: Code review with a real comment (22-28s) ===
  { t: 17000, step: { type: 'agent-status', data: { agentId: 'code_reviewer', status: 'working', task: 'Reviewing login PR' } } },
  { t: 18000, step: msg(-6, 'code_reviewer', 'Code Reviewer', 'Two things: rate limit window should be configurable, and we should log failed attempts (not just successes). Otherwise LGTM.', { to: 'developer', toName: 'Developer', storyId: -102 }) },
  { t: 19200, step: msg(-7, 'developer', 'Developer', 'Fair point on the logging. Will fix both.', { to: 'code_reviewer', toName: 'Code Reviewer', storyId: -102 }) },
  { t: 20800, step: { type: 'story-update', data: { storyId: -102, status: 'in_qa', taskCount: 3, completedCount: 3 } } },
  { t: 20800, step: { type: 'story-pulse', data: { storyId: -102 } } },
  { t: 21400, step: { type: 'agent-status', data: { agentId: 'developer', status: 'idle', task: null } } },
  { t: 21400, step: { type: 'agent-status', data: { agentId: 'code_reviewer', status: 'idle', task: null } } },

  // === Phase 5: QA verifies (28-34s) ===
  { t: 22200, step: { type: 'agent-status', data: { agentId: 'qa', status: 'working', task: 'Verifying login flow' } } },
  { t: 23000, step: msg(-8, 'qa', 'QA', 'Running the auth scenarios — happy path, wrong password, locked-out account, rate-limit trigger.', { storyId: -102 }) },
  { t: 25000, step: msg(-9, 'qa', 'QA', '4/4 scenarios pass. Closing this out.', { storyId: -102 }) },
  { t: 25800, step: { type: 'story-update', data: { storyId: -102, status: 'done', taskCount: 3, completedCount: 3 } } },
  { t: 25800, step: { type: 'story-pulse', data: { storyId: -102 } } },
  { t: 26800, step: { type: 'agent-status', data: { agentId: 'qa', status: 'idle', task: null } } },
  { t: 27600, step: msg(-10, 'product_owner', 'Product Owner', 'Login shipped 🎉 — moving on to sign-up next sprint.') },
];

export const DEMO_DURATION_MS = 28500;
