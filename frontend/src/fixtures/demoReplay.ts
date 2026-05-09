/**
 * Pre-recorded timelines used by the demo replay mode on first visit.
 * One timeline per template — picked at runtime based on the active
 * board's `template_id`. Each step fires at `t` ms from replay start.
 *
 * Steps mutate the store directly (stories/tasks/agents) and emit
 * chat messages through the event bus.
 */

import type { Story, Task, Comment } from '../types';

type StorySeed = Omit<Story, 'created_at' | 'updated_at'>;
type TaskSeed = Omit<Task, 'created_at' | 'updated_at'>;
/** Comment fixture without a timestamp; `secondsAgo` controls relative ordering. */
type CommentSeed = Omit<Comment, 'created_at'> & { secondsAgo: number };

const now = () => new Date().toISOString();

export type ReplayStep =
  | { type: 'agent-status'; data: { agentId: string; status: 'idle' | 'working' | 'waiting'; task?: string | null } }
  | { type: 'story-add'; data: { storyId: number } }
  | { type: 'story-update'; data: { storyId: number; status: string; taskCount?: number; completedCount?: number } }
  | { type: 'task-add'; data: { taskId: number } }
  | { type: 'chat'; data: ChatPayload }
  | { type: 'story-pulse'; data: { storyId: number } };

interface ChatPayload {
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

export interface DemoTimeline {
  stories: Record<number, StorySeed>;
  tasks: Record<number, TaskSeed>;
  /** Comments per story, shown in the StoryDetail Activity tab for synthetic stories. */
  comments?: Record<number, CommentSeed[]>;
  steps: Array<{ t: number; step: ReplayStep }>;
  durationMs: number;
  /** A short headline shown in the replay banner. */
  headline: string;
}

const msg = (id: number, from: string, fromName: string, content: string, opts: { to?: string; toName?: string; storyId?: number; taskId?: number } = {}): { type: 'chat'; data: ChatPayload } => ({
  type: 'chat',
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

// ============================================================
// Publisher template (default board on first run)
// Columns: inbox → writing → editing → creatives → ready_to_publish → published
// Agents (from backend publisher template): news_curator, journalist,
//   editor, creative_director
// ============================================================

const PUBLISHER_BOARD_ID = -1;

const publisherStories: Record<number, StorySeed> = {
  [-101]: {
    id: -101, board_id: PUBLISHER_BOARD_ID, epic_id: null,
    title: 'OpenAI announces GPT-6 with native video reasoning',
    description: 'OpenAI unveiled GPT-6 today, claiming a step-change in long-context video understanding. Embargo lifts at 9am ET.',
    acceptance_criteria: null,
    status: 'inbox', priority: 1, prd_content: null,
    task_count: 0, completed_task_count: 0,
  },
  [-102]: {
    id: -102, board_id: PUBLISHER_BOARD_ID, epic_id: null,
    title: 'EU AI Act second-stage rules take effect Monday',
    description: 'The high-risk AI obligations under the EU AI Act enter force next week. Industry has been quietly lobbying for delays.',
    acceptance_criteria: null,
    status: 'inbox', priority: 2, prd_content: null,
    task_count: 0, completed_task_count: 0,
  },
  [-103]: {
    id: -103, board_id: PUBLISHER_BOARD_ID, epic_id: null,
    title: 'Anthropic raises $8B Series F at $200B valuation',
    description: 'Sources confirm a fresh round led by Lightspeed and Sequoia. Anthropic has not commented publicly.',
    acceptance_criteria: null,
    status: 'inbox', priority: 1, prd_content: null,
    task_count: 0, completed_task_count: 0,
  },
};

const publisherComments: Record<number, CommentSeed[]> = {
  [-101]: [
    {
      id: -1001, story_id: -101, task_id: null, agent_type: 'news_curator',
      content: 'Triaged this morning. Embargo lifts at 9am ET — making it the lead.',
      metadata: { action: 'triaged' },
      secondsAgo: 540,
    },
    {
      id: -1002, story_id: -101, task_id: null, agent_type: 'journalist',
      content: '600-word draft up. Lede on the 30-minute video benchmark, plus context on competing models and an Altman quote.',
      metadata: { action: 'drafted' },
      secondsAgo: 360,
    },
    {
      id: -1003, story_id: -101, task_id: null, agent_type: 'editor',
      content: 'Pushed back on the lede and a thin Hugging Face quote. Journalist agreed to cut the quote rather than weaken the piece.',
      metadata: { action: 'reviewed', approved: false },
      secondsAgo: 240,
    },
    {
      id: -1004, story_id: -101, task_id: null, agent_type: 'editor',
      content: 'Revised draft is tighter. Approved.',
      metadata: { action: 'approved', approved: true },
      secondsAgo: 180,
    },
    {
      id: -1005, story_id: -101, task_id: null, agent_type: 'creative_director',
      content: 'Hero image: clean shot of the new product page over the standard OpenAI logo treatment. Less promotional.',
      metadata: { action: 'visuals_added' },
      secondsAgo: 90,
    },
    {
      id: -1006, story_id: -101, task_id: null, agent_type: 'news_curator',
      content: 'Embargo lifted. Pushed live.',
      metadata: { action: 'published' },
      secondsAgo: 20,
    },
  ],
  [-103]: [
    {
      id: -1101, story_id: -103, task_id: null, agent_type: 'news_curator',
      content: 'Holding this until we have a second source on the funding figure. One named source isn\'t enough.',
      metadata: { action: 'on_hold' },
      secondsAgo: 480,
    },
  ],
};

const publisherTimeline: Array<{ t: number; step: ReplayStep }> = [
  // 0-6s: News Curator triages incoming briefs
  { t:   400, step: { type: 'agent-status', data: { agentId: 'news_curator', status: 'working', task: 'Triaging morning briefs' } } },
  { t:   800, step: msg(-1, 'news_curator', 'News Curator', "Three briefs landed overnight. The OpenAI one is biggest — embargo lifts at 9. Picking that up first.") },
  { t:  1800, step: { type: 'story-add', data: { storyId: -101 } } },
  { t:  1800, step: { type: 'story-pulse', data: { storyId: -101 } } },
  { t:  2700, step: { type: 'story-add', data: { storyId: -103 } } },
  { t:  2700, step: { type: 'story-pulse', data: { storyId: -103 } } },
  { t:  3400, step: { type: 'story-add', data: { storyId: -102 } } },
  { t:  3400, step: { type: 'story-pulse', data: { storyId: -102 } } },
  { t:  4200, step: msg(-2, 'news_curator', 'News Curator', '@Journalist take the GPT-6 story — the embargo gives us a hard deadline. The funding rumor needs a second source first.', { to: 'journalist', toName: 'Journalist', storyId: -101 }) },
  { t:  5000, step: { type: 'agent-status', data: { agentId: 'news_curator', status: 'idle', task: null } } },

  // 6-15s: Journalist writes the lead story
  { t:  5800, step: { type: 'agent-status', data: { agentId: 'journalist', status: 'working', task: 'Drafting GPT-6 announcement' } } },
  { t:  6200, step: { type: 'story-update', data: { storyId: -101, status: 'writing' } } },
  { t:  6200, step: { type: 'story-pulse', data: { storyId: -101 } } },
  { t:  7400, step: msg(-3, 'journalist', 'Journalist', 'Reading the press release now. They claim 30-minute coherent video reasoning — that\'s the headline.', { storyId: -101 }) },
  { t:  9200, step: msg(-4, 'journalist', 'Journalist', 'Draft is ~600 words: lede on the video benchmark, context on competing models, quote from Altman, skeptical quote from Hugging Face.', { storyId: -101 }) },
  { t: 10800, step: msg(-5, 'journalist', 'Journalist', 'Pushing to @Editor.', { to: 'editor', toName: 'Editor', storyId: -101 }) },
  { t: 11400, step: { type: 'story-update', data: { storyId: -101, status: 'editing' } } },
  { t: 11400, step: { type: 'story-pulse', data: { storyId: -101 } } },
  { t: 12000, step: { type: 'agent-status', data: { agentId: 'journalist', status: 'waiting', task: 'Awaiting edits' } } },

  // 15-22s: Editor pushes back (real disagreement → resolution)
  { t: 12600, step: { type: 'agent-status', data: { agentId: 'editor', status: 'working', task: 'Editing GPT-6 piece' } } },
  { t: 14200, step: msg(-6, 'editor', 'Editor', "Lede buries the news — open with the 30-minute video benchmark, not the model name. Also, the Hugging Face quote is too thin; either get something concrete or cut it.", { to: 'journalist', toName: 'Journalist', storyId: -101 }) },
  { t: 15600, step: msg(-7, 'journalist', 'Journalist', 'Fair on the lede. On the quote — I\'ll cut it rather than weaken the piece chasing it before deadline.', { to: 'editor', toName: 'Editor', storyId: -101 }) },
  { t: 17000, step: msg(-8, 'editor', 'Editor', "Agreed. Approved. Sending to creatives.", { storyId: -101 }) },
  { t: 17600, step: { type: 'story-update', data: { storyId: -101, status: 'creatives' } } },
  { t: 17600, step: { type: 'story-pulse', data: { storyId: -101 } } },
  { t: 18200, step: { type: 'agent-status', data: { agentId: 'editor', status: 'idle', task: null } } },
  { t: 18200, step: { type: 'agent-status', data: { agentId: 'journalist', status: 'idle', task: null } } },

  // 22-28s: Creative Director adds visuals
  { t: 18800, step: { type: 'agent-status', data: { agentId: 'creative_director', status: 'working', task: 'Sourcing hero image' } } },
  { t: 20000, step: msg(-9, 'creative_director', 'Creative Director', 'Going with a clean shot of the new product page over the OpenAI logo treatment — feels less promotional.', { storyId: -101 }) },
  { t: 21800, step: { type: 'story-update', data: { storyId: -101, status: 'ready_to_publish' } } },
  { t: 21800, step: { type: 'story-pulse', data: { storyId: -101 } } },
  { t: 22400, step: { type: 'agent-status', data: { agentId: 'creative_director', status: 'idle', task: null } } },

  // 28-32s: Publish at embargo
  { t: 23200, step: msg(-10, 'news_curator', 'News Curator', "Embargo lifted. Pushing live.") },
  { t: 24400, step: { type: 'story-update', data: { storyId: -101, status: 'published' } } },
  { t: 24400, step: { type: 'story-pulse', data: { storyId: -101 } } },
  { t: 25400, step: msg(-11, 'news_curator', 'News Curator', 'Live. Onto the funding rumor — @Journalist, ping me when you have the second source.', { to: 'journalist', toName: 'Journalist', storyId: -103 }) },
];

// ============================================================
// Software dev template (for users who switch to that board)
// ============================================================

const SOFTWARE_BOARD_ID = -2;

const softwareStories: Record<number, StorySeed> = {
  [-201]: { id: -201, board_id: SOFTWARE_BOARD_ID, epic_id: null, title: 'Email + password sign-up flow', description: 'Allow new users to register with email and password.', acceptance_criteria: null, status: 'backlog', priority: 1, prd_content: null, task_count: 0, completed_task_count: 0 },
  [-202]: { id: -202, board_id: SOFTWARE_BOARD_ID, epic_id: null, title: 'Login with rate limiting', description: 'Auth endpoint with bcrypt + sliding-window rate limit per IP.', acceptance_criteria: null, status: 'backlog', priority: 1, prd_content: null, task_count: 0, completed_task_count: 0 },
  [-203]: { id: -203, board_id: SOFTWARE_BOARD_ID, epic_id: null, title: 'Password reset via email link', description: 'Tokenized reset link with 30-minute expiry.', acceptance_criteria: null, status: 'backlog', priority: 2, prd_content: null, task_count: 0, completed_task_count: 0 },
};

const softwareTasks: Record<number, TaskSeed> = {
  [-301]: { id: -301, story_id: -202, title: 'Hash & verify passwords with bcrypt', description: null, implementation_notes: null, test_scenarios: null, status: 'in_progress', assigned_agent: 'developer' },
  [-302]: { id: -302, story_id: -202, title: 'Sliding-window rate limiter middleware', description: null, implementation_notes: null, test_scenarios: null, status: 'in_progress', assigned_agent: 'developer' },
  [-303]: { id: -303, story_id: -202, title: 'Login endpoint integration tests', description: null, implementation_notes: null, test_scenarios: null, status: 'pending_review', assigned_agent: 'qa' },
};

const softwareComments: Record<number, CommentSeed[]> = {
  [-202]: [
    {
      id: -2001, story_id: -202, task_id: null, agent_type: 'product_owner',
      content: 'Split out from the auth PRD. Most security surface area of the three — taking this one first.',
      metadata: { action: 'created' },
      secondsAgo: 600,
    },
    {
      id: -2002, story_id: -202, task_id: null, agent_type: 'tech_lead',
      content: 'Scoping: bcrypt for hashing, sliding-window rate limit per IP. Three tasks. Handing to Developer.',
      metadata: { action: 'scoped' },
      secondsAgo: 480,
    },
    {
      id: -2003, story_id: -202, task_id: null, agent_type: 'developer',
      content: 'Tasks broken out and login + bcrypt landed. Pushing for review.',
      metadata: { action: 'implemented' },
      secondsAgo: 320,
    },
    {
      id: -2004, story_id: -202, task_id: null, agent_type: 'code_reviewer',
      content: 'Two asks: rate-limit window should be configurable, and we should log failed attempts. Otherwise LGTM.',
      metadata: { action: 'reviewed', approved: false },
      secondsAgo: 220,
    },
    {
      id: -2005, story_id: -202, task_id: null, agent_type: 'developer',
      content: 'Both addressed — config flag for the window, structured log on failed attempts.',
      metadata: { action: 'revised' },
      secondsAgo: 140,
    },
    {
      id: -2006, story_id: -202, task_id: null, agent_type: 'qa',
      content: '4/4 scenarios pass: happy path, wrong password, locked-out account, rate-limit trigger. Closing this out.',
      metadata: { action: 'qa_passed', approved: true },
      secondsAgo: 30,
    },
  ],
};

const softwareTimeline: Array<{ t: number; step: ReplayStep }> = [
  { t:   400, step: { type: 'agent-status', data: { agentId: 'product_owner', status: 'working', task: 'Breaking down auth PRD' } } },
  { t:   900, step: msg(-1, 'product_owner', 'Product Owner', 'Got the auth PRD. Breaking this into 3 stories — sign-up, login, and password reset.') },
  { t:  2200, step: { type: 'story-add', data: { storyId: -201 } } },
  { t:  2200, step: { type: 'story-pulse', data: { storyId: -201 } } },
  { t:  3100, step: { type: 'story-add', data: { storyId: -202 } } },
  { t:  3100, step: { type: 'story-pulse', data: { storyId: -202 } } },
  { t:  4000, step: { type: 'story-add', data: { storyId: -203 } } },
  { t:  4000, step: { type: 'story-pulse', data: { storyId: -203 } } },
  { t:  4800, step: msg(-2, 'product_owner', 'Product Owner', '@Tech Lead can you scope the login one first? It has the most security surface area.', { to: 'tech_lead', toName: 'Tech Lead', storyId: -202 }) },
  { t:  5400, step: { type: 'agent-status', data: { agentId: 'product_owner', status: 'idle', task: null } } },

  { t:  6000, step: { type: 'agent-status', data: { agentId: 'tech_lead', status: 'working', task: 'Scoping login story' } } },
  { t:  6600, step: { type: 'story-update', data: { storyId: -202, status: 'ready_for_breakdown' } } },
  { t:  6600, step: { type: 'story-pulse', data: { storyId: -202 } } },
  { t:  7600, step: msg(-3, 'tech_lead', 'Tech Lead', 'Bcrypt for hashing, sliding-window rate limit per IP. Three tasks. @Developer take it.', { to: 'developer', toName: 'Developer', storyId: -202 }) },
  { t:  8400, step: { type: 'story-update', data: { storyId: -202, status: 'in_breakdown', taskCount: 3 } } },
  { t:  8400, step: { type: 'story-pulse', data: { storyId: -202 } } },
  { t:  9200, step: { type: 'agent-status', data: { agentId: 'tech_lead', status: 'idle', task: null } } },

  { t:  9800, step: { type: 'agent-status', data: { agentId: 'developer', status: 'working', task: 'Implementing login endpoint' } } },
  { t: 10400, step: { type: 'task-add', data: { taskId: -301 } } },
  { t: 11200, step: { type: 'task-add', data: { taskId: -302 } } },
  { t: 12000, step: { type: 'task-add', data: { taskId: -303 } } },
  { t: 12800, step: msg(-4, 'developer', 'Developer', 'Tasks broken out. Hashing + rate limiter look straightforward.', { storyId: -202 }) },
  { t: 13600, step: { type: 'story-update', data: { storyId: -202, status: 'in_development', taskCount: 3, completedCount: 1 } } },
  { t: 13600, step: { type: 'story-pulse', data: { storyId: -202 } } },
  { t: 15400, step: msg(-5, 'developer', 'Developer', 'Login + bcrypt landed. Pushing for review.', { to: 'code_reviewer', toName: 'Code Reviewer', storyId: -202 }) },
  { t: 15800, step: { type: 'story-update', data: { storyId: -202, status: 'tasks_in_review', taskCount: 3, completedCount: 2 } } },
  { t: 15800, step: { type: 'story-pulse', data: { storyId: -202 } } },
  { t: 16400, step: { type: 'agent-status', data: { agentId: 'developer', status: 'waiting', task: 'Awaiting review' } } },

  { t: 17000, step: { type: 'agent-status', data: { agentId: 'code_reviewer', status: 'working', task: 'Reviewing login PR' } } },
  { t: 18200, step: msg(-6, 'code_reviewer', 'Code Reviewer', 'Two things: rate limit window should be configurable, and we should log failed attempts. Otherwise LGTM.', { to: 'developer', toName: 'Developer', storyId: -202 }) },
  { t: 19400, step: msg(-7, 'developer', 'Developer', 'Fair on the logging. Will fix both.', { to: 'code_reviewer', toName: 'Code Reviewer', storyId: -202 }) },
  { t: 20800, step: { type: 'story-update', data: { storyId: -202, status: 'in_qa', taskCount: 3, completedCount: 3 } } },
  { t: 20800, step: { type: 'story-pulse', data: { storyId: -202 } } },
  { t: 21400, step: { type: 'agent-status', data: { agentId: 'developer', status: 'idle', task: null } } },
  { t: 21400, step: { type: 'agent-status', data: { agentId: 'code_reviewer', status: 'idle', task: null } } },

  { t: 22000, step: { type: 'agent-status', data: { agentId: 'qa', status: 'working', task: 'Verifying login flow' } } },
  { t: 23000, step: msg(-8, 'qa', 'QA', 'Running auth scenarios — happy path, wrong password, locked-out account, rate-limit trigger.', { storyId: -202 }) },
  { t: 25000, step: msg(-9, 'qa', 'QA', '4/4 scenarios pass. Closing this out.', { storyId: -202 }) },
  { t: 25800, step: { type: 'story-update', data: { storyId: -202, status: 'done', taskCount: 3, completedCount: 3 } } },
  { t: 25800, step: { type: 'story-pulse', data: { storyId: -202 } } },
  { t: 26800, step: { type: 'agent-status', data: { agentId: 'qa', status: 'idle', task: null } } },
];

// ============================================================
// Registry
// ============================================================

export const DEMO_TIMELINES: Record<string, DemoTimeline> = {
  publisher: {
    stories: publisherStories,
    tasks: {},
    comments: publisherComments,
    steps: publisherTimeline,
    durationMs: 26500,
    headline: 'Watching a recorded run of the editorial swarm shipping a breaking-news article',
  },
  software_dev: {
    stories: softwareStories,
    tasks: softwareTasks,
    comments: softwareComments,
    steps: softwareTimeline,
    durationMs: 27500,
    headline: 'Watching a recorded run of the dev swarm shipping a login feature',
  },
};

/**
 * Returns hydrated comments for a synthetic (negative-id) story across all
 * registered timelines, sorted oldest first. Empty list if none seeded.
 */
export function getDemoComments(storyId: number): Comment[] {
  for (const tl of Object.values(DEMO_TIMELINES)) {
    const seeds = tl.comments?.[storyId];
    if (!seeds) continue;
    const nowMs = Date.now();
    return [...seeds]
      .sort((a, b) => b.secondsAgo - a.secondsAgo)
      .map(({ secondsAgo, ...rest }) => ({
        ...rest,
        created_at: new Date(nowMs - secondsAgo * 1000).toISOString(),
      }));
  }
  return [];
}
