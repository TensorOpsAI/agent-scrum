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
    title: 'OpenAI anuncia GPT-6 con razonamiento de vídeo nativo',
    description: 'OpenAI presentó hoy GPT-6, con lo que asegura un salto cualitativo en la comprensión de vídeo de contexto largo. El embargo se levanta a las 9h (hora de Nueva York).',
    acceptance_criteria: null,
    status: 'inbox', priority: 1, prd_content: null,
    task_count: 0, completed_task_count: 0,
  },
  [-102]: {
    id: -102, board_id: PUBLISHER_BOARD_ID, epic_id: null,
    title: 'La segunda fase del Reglamento de IA de la UE entra en vigor el lunes',
    description: 'Las obligaciones para la IA de alto riesgo del Reglamento de IA de la UE entran en vigor la próxima semana. El sector ha presionado discretamente para retrasarlas.',
    acceptance_criteria: null,
    status: 'inbox', priority: 2, prd_content: null,
    task_count: 0, completed_task_count: 0,
  },
  [-103]: {
    id: -103, board_id: PUBLISHER_BOARD_ID, epic_id: null,
    title: 'Anthropic capta 8.000 millones de dólares en una ronda Serie F con una valoración de 200.000 millones',
    description: 'Fuentes confirman una nueva ronda liderada por Lightspeed y Sequoia. Anthropic no ha hecho declaraciones públicas.',
    acceptance_criteria: null,
    status: 'inbox', priority: 1, prd_content: null,
    task_count: 0, completed_task_count: 0,
  },
};

const publisherComments: Record<number, CommentSeed[]> = {
  [-101]: [
    {
      id: -1001, story_id: -101, task_id: null, agent_type: 'news_curator',
      content: 'Clasificado esta mañana. El embargo se levanta a las 9h — será la noticia principal.',
      metadata: { action: 'triaged' },
      secondsAgo: 540,
    },
    {
      id: -1002, story_id: -101, task_id: null, agent_type: 'journalist',
      content: 'Borrador de 600 palabras listo. Entradilla sobre el hito de los 30 minutos de vídeo, más contexto sobre modelos de la competencia y una cita de Altman.',
      metadata: { action: 'drafted' },
      secondsAgo: 360,
    },
    {
      id: -1003, story_id: -101, task_id: null, agent_type: 'editor',
      content: 'Cuestioné la entradilla y una cita poco sólida de Hugging Face. El periodista aceptó eliminarla en lugar de debilitar la pieza.',
      metadata: { action: 'reviewed', approved: false },
      secondsAgo: 240,
    },
    {
      id: -1004, story_id: -101, task_id: null, agent_type: 'editor',
      content: 'El borrador revisado es más sólido. Aprobado.',
      metadata: { action: 'approved', approved: true },
      secondsAgo: 180,
    },
    {
      id: -1005, story_id: -101, task_id: null, agent_type: 'creative_director',
      content: 'Imagen principal: una captura limpia de la nueva página del producto en lugar del tratamiento habitual con el logo de OpenAI. Menos promocional.',
      metadata: { action: 'visuals_added' },
      secondsAgo: 90,
    },
    {
      id: -1006, story_id: -101, task_id: null, agent_type: 'news_curator',
      content: 'Embargo levantado. Publicado.',
      metadata: { action: 'published' },
      secondsAgo: 20,
    },
  ],
  [-103]: [
    {
      id: -1101, story_id: -103, task_id: null, agent_type: 'news_curator',
      content: 'Retenido hasta tener una segunda fuente sobre la cifra de financiación. Una sola fuente identificada no es suficiente.',
      metadata: { action: 'on_hold' },
      secondsAgo: 480,
    },
  ],
};

const publisherTimeline: Array<{ t: number; step: ReplayStep }> = [
  // 0-5s: News Curator triages incoming briefs and splits up the work
  { t:   400, step: { type: 'agent-status', data: { agentId: 'news_curator', status: 'working', task: 'Clasificando los briefs de la mañana' } } },
  { t:   800, step: msg(-1, 'news_curator', 'Curador de Noticias', "Llegaron tres briefs durante la noche. Vamos a repartirlos entre el equipo.") },
  { t:  1800, step: { type: 'story-add', data: { storyId: -101 } } },
  { t:  1800, step: { type: 'story-pulse', data: { storyId: -101 } } },
  { t:  2700, step: { type: 'story-add', data: { storyId: -103 } } },
  { t:  2700, step: { type: 'story-pulse', data: { storyId: -103 } } },
  { t:  3400, step: { type: 'story-add', data: { storyId: -102 } } },
  { t:  3400, step: { type: 'story-pulse', data: { storyId: -102 } } },
  { t:  4200, step: msg(-2, 'news_curator', 'Curador de Noticias', '@Periodista, la de OpenAI tiene embargo a las 9h — empieza por ahí. Yo redacto la de la UE mientras confirmamos la segunda fuente de Anthropic.', { to: 'journalist', toName: 'Periodista', storyId: -101 }) },
  { t:  5000, step: { type: 'agent-status', data: { agentId: 'news_curator', status: 'idle', task: null } } },

  // 5-11s: Journalist starts the lead story, while News Curator kicks off the EU piece in parallel
  { t:  5800, step: { type: 'agent-status', data: { agentId: 'journalist', status: 'working', task: 'Redactando el anuncio de GPT-6' } } },
  { t:  6200, step: { type: 'story-update', data: { storyId: -101, status: 'writing' } } },
  { t:  6200, step: { type: 'story-pulse', data: { storyId: -101 } } },
  { t:  7000, step: msg(-3, 'journalist', 'Periodista', 'Leyendo el comunicado de OpenAI. Razonamiento de vídeo coherente de 30 minutos — ese es el titular.', { storyId: -101 }) },
  { t:  8000, step: { type: 'agent-status', data: { agentId: 'news_curator', status: 'working', task: 'Redactando la nota sobre el Reglamento de IA de la UE' } } },
  { t:  8000, step: { type: 'story-update', data: { storyId: -102, status: 'writing' } } },
  { t:  8000, step: { type: 'story-pulse', data: { storyId: -102 } } },
  { t:  9000, step: msg(-4, 'news_curator', 'Curador de Noticias', 'Nota breve sobre las nuevas obligaciones de la UE — la envío a @Editor.', { to: 'editor', toName: 'Editor', storyId: -102 }) },
  { t:  9400, step: { type: 'story-update', data: { storyId: -102, status: 'editing' } } },
  { t:  9400, step: { type: 'story-pulse', data: { storyId: -102 } } },
  { t:  9800, step: { type: 'agent-status', data: { agentId: 'news_curator', status: 'idle', task: null } } },

  // 9-12s: Journalist wraps the OpenAI draft, Editor starts on the EU piece
  { t:  9800, step: msg(-5, 'journalist', 'Periodista', 'El borrador de OpenAI tiene ~600 palabras: entradilla sobre el vídeo, cita de Altman, cita escéptica de Hugging Face.', { storyId: -101 }) },
  { t: 10800, step: { type: 'agent-status', data: { agentId: 'editor', status: 'working', task: 'Revisando la nota sobre la UE' } } },
  { t: 11400, step: msg(-6, 'journalist', 'Periodista', 'Lo envío a @Editor.', { to: 'editor', toName: 'Editor', storyId: -101 }) },
  { t: 11800, step: { type: 'story-update', data: { storyId: -101, status: 'editing' } } },
  { t: 11800, step: { type: 'story-pulse', data: { storyId: -101 } } },
  { t: 12200, step: { type: 'agent-status', data: { agentId: 'journalist', status: 'waiting', task: 'Esperando la edición' } } },

  // 12-15s: EU piece clears editing and creatives while Editor also has OpenAI queued
  { t: 12200, step: msg(-7, 'editor', 'Editor', 'La nota de la UE está bien — aprobada. Pasa a creativos.', { storyId: -102 }) },
  { t: 12600, step: { type: 'story-update', data: { storyId: -102, status: 'creatives' } } },
  { t: 12600, step: { type: 'story-pulse', data: { storyId: -102 } } },
  { t: 13000, step: { type: 'agent-status', data: { agentId: 'editor', status: 'working', task: 'Editando la pieza de GPT-6' } } },
  { t: 13000, step: { type: 'agent-status', data: { agentId: 'creative_director', status: 'working', task: 'Buscando imagen para la nota de la UE' } } },
  { t: 14000, step: { type: 'story-update', data: { storyId: -102, status: 'ready_to_publish' } } },
  { t: 14000, step: { type: 'story-pulse', data: { storyId: -102 } } },
  { t: 14400, step: msg(-8, 'creative_director', 'Director Creativo', 'Imagen lista para la nota de la UE.', { storyId: -102 }) },
  { t: 14800, step: { type: 'story-update', data: { storyId: -102, status: 'published' } } },
  { t: 14800, step: { type: 'story-pulse', data: { storyId: -102 } } },
  { t: 14800, step: { type: 'agent-status', data: { agentId: 'creative_director', status: 'idle', task: null } } },

  // 15-19s: Editor pushes back on OpenAI (real disagreement → resolution)
  { t: 15200, step: msg(-9, 'editor', 'Editor', "La entradilla de OpenAI entierra la noticia — abre con el hito del vídeo, no con el modelo. Y la cita de Hugging Face es floja.", { to: 'journalist', toName: 'Periodista', storyId: -101 }) },
  { t: 16600, step: msg(-10, 'journalist', 'Periodista', 'De acuerdo. La quito antes que debilitar la pieza contra el plazo.', { to: 'editor', toName: 'Editor', storyId: -101 }) },
  { t: 18000, step: msg(-11, 'editor', 'Editor', "Aprobado. Lo envío a creativos.", { storyId: -101 }) },
  { t: 18400, step: { type: 'story-update', data: { storyId: -101, status: 'creatives' } } },
  { t: 18400, step: { type: 'story-pulse', data: { storyId: -101 } } },
  { t: 18800, step: { type: 'agent-status', data: { agentId: 'editor', status: 'idle', task: null } } },
  { t: 18800, step: { type: 'agent-status', data: { agentId: 'journalist', status: 'idle', task: null } } },

  // 19-21s: Creative Director works OpenAI visuals while second source for Anthropic comes through
  { t: 18800, step: { type: 'agent-status', data: { agentId: 'creative_director', status: 'working', task: 'Buscando la imagen principal de OpenAI' } } },
  { t: 19000, step: { type: 'agent-status', data: { agentId: 'news_curator', status: 'working', task: 'Confirmando la segunda fuente de la ronda de Anthropic' } } },
  { t: 20000, step: msg(-12, 'news_curator', 'Curador de Noticias', 'Segunda fuente confirmada. @Periodista, adelante con la de Anthropic.', { to: 'journalist', toName: 'Periodista', storyId: -103 }) },
  { t: 20400, step: { type: 'story-update', data: { storyId: -103, status: 'writing' } } },
  { t: 20400, step: { type: 'story-pulse', data: { storyId: -103 } } },
  { t: 20400, step: { type: 'agent-status', data: { agentId: 'news_curator', status: 'idle', task: null } } },
  { t: 20400, step: { type: 'agent-status', data: { agentId: 'journalist', status: 'working', task: 'Redactando la financiación de Anthropic' } } },

  // 21-23s: OpenAI visuals land, ready to publish
  { t: 21000, step: msg(-13, 'creative_director', 'Director Creativo', 'Imagen de OpenAI lista — captura limpia de la web del producto, menos promocional.', { storyId: -101 }) },
  { t: 21400, step: { type: 'story-update', data: { storyId: -101, status: 'ready_to_publish' } } },
  { t: 21400, step: { type: 'story-pulse', data: { storyId: -101 } } },
  { t: 21400, step: { type: 'agent-status', data: { agentId: 'creative_director', status: 'idle', task: null } } },

  // 22-24s: Anthropic draft moves to editing while OpenAI publishes at embargo
  { t: 22400, step: msg(-14, 'journalist', 'Periodista', 'Anthropic: 8.000 millones liderados por Lightspeed y Sequoia. Lo envío a @Editor.', { to: 'editor', toName: 'Editor', storyId: -103 }) },
  { t: 22800, step: { type: 'story-update', data: { storyId: -103, status: 'editing' } } },
  { t: 22800, step: { type: 'story-pulse', data: { storyId: -103 } } },
  { t: 22800, step: { type: 'agent-status', data: { agentId: 'journalist', status: 'idle', task: null } } },
  { t: 23200, step: { type: 'agent-status', data: { agentId: 'editor', status: 'working', task: 'Revisando la financiación de Anthropic' } } },
  { t: 23800, step: msg(-15, 'news_curator', 'Curador de Noticias', 'Embargo levantado en la de OpenAI. Publicando.') },
  { t: 24400, step: { type: 'story-update', data: { storyId: -101, status: 'published' } } },
  { t: 24400, step: { type: 'story-pulse', data: { storyId: -101 } } },

  // 25-28s: Anthropic piece clears the rest of the pipeline
  { t: 25000, step: msg(-16, 'editor', 'Editor', 'Aprobada la de Anthropic.', { storyId: -103 }) },
  { t: 25400, step: { type: 'story-update', data: { storyId: -103, status: 'creatives' } } },
  { t: 25400, step: { type: 'story-pulse', data: { storyId: -103 } } },
  { t: 25400, step: { type: 'agent-status', data: { agentId: 'editor', status: 'idle', task: null } } },
  { t: 25800, step: { type: 'agent-status', data: { agentId: 'creative_director', status: 'working', task: 'Buscando imagen para Anthropic' } } },
  { t: 26800, step: { type: 'story-update', data: { storyId: -103, status: 'ready_to_publish' } } },
  { t: 26800, step: { type: 'story-pulse', data: { storyId: -103 } } },
  { t: 27200, step: msg(-17, 'creative_director', 'Director Creativo', 'Imagen de Anthropic lista.', { storyId: -103 }) },
  { t: 27600, step: { type: 'story-update', data: { storyId: -103, status: 'published' } } },
  { t: 27600, step: { type: 'story-pulse', data: { storyId: -103 } } },
  { t: 27600, step: { type: 'agent-status', data: { agentId: 'creative_director', status: 'idle', task: null } } },
  { t: 27600, step: msg(-18, 'news_curator', 'Curador de Noticias', 'Las tres noticias están publicadas. Buen ritmo esta mañana.') },
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
    durationMs: 29000,
    headline: 'Viendo una repetición grabada del equipo editorial publicando tres artículos en paralelo',
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
