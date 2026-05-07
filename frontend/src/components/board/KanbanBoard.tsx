import { useEffect } from 'react';
import { cn } from '../../lib/utils';
import { FileText, Sparkles, Zap, CheckCircle2, Play, RotateCcw, X } from 'lucide-react';
import { useStoryStore } from '../../store/storyStore';
import { usePipelineStore } from '../../store/pipelineStore';
import { useUIStore } from '../../store/uiStore';
import { useStoryActivity } from '../../hooks/useStoryActivity';
import { useDemoReplay } from '../../hooks/useDemoReplay';
import { simulateApi } from '../../api/client';
import { StoryCard } from './StoryCard';
import type { Story, PipelineColumn } from '../../types';

interface KanbanColumnProps {
  columnKey: string;
  label: string;
  color: string;
  stories: Story[];
  selectedStoryId: number | null;
  activeIds: Set<number>;
  onSelectStory: (id: number) => void;
}

function KanbanColumn({
  columnKey, label, color, stories, selectedStoryId, activeIds, onSelectStory,
}: KanbanColumnProps) {
  return (
    <div
      className="flex flex-col min-w-[300px] w-[300px] surface-muted h-full"
      data-status={columnKey}
    >
      <div className="px-3.5 py-3 flex items-center justify-between flex-shrink-0 border-b border-border/60">
        <div className="flex items-center gap-2">
          <span className={cn('status-dot', color)} />
          <h2 className="font-medium text-foreground text-[13px] tracking-tight">
            {label}
          </h2>
          <span className="text-[11px] font-medium text-muted-foreground tabular-nums">
            {stories.length}
          </span>
        </div>
      </div>

      <div className="flex-1 p-2.5 space-y-2 overflow-y-auto">
        {stories.map((story) => (
          <StoryCard
            key={story.id}
            story={story}
            isSelected={selectedStoryId === story.id}
            isActive={activeIds.has(story.id)}
            onClick={() => onSelectStory(story.id)}
          />
        ))}

        {stories.length === 0 && (
          <div className="text-center py-10 text-xs text-muted-foreground/60 italic">
            No items
          </div>
        )}
      </div>
    </div>
  );
}

const WORKFLOW_STEPS: Record<string, { icon: React.ReactNode; steps: string[] }> = {
  software_dev: {
    icon: <FileText className="w-6 h-6" />,
    steps: [
      'Product Owner analyzes your PRD and creates user stories',
      'Developer breaks stories into tasks with implementation notes',
      'Tech Lead reviews, then tasks flow through development & QA',
    ],
  },
  publisher: {
    icon: <Sparkles className="w-6 h-6" />,
    steps: [
      'News Curator evaluates the brief and creates article assignments',
      'Journalist drafts content, Editor reviews for quality',
      'Creative Director adds visuals, then articles are published',
    ],
  },
  talent_acquisition: {
    icon: <FileText className="w-6 h-6" />,
    steps: [
      'Sourcing Specialist parses the requisition and finds candidates',
      'Recruiter screens resumes and conducts phone screens',
      'Hiring Manager reviews, then offers are prepared',
    ],
  },
  sales: {
    icon: <FileText className="w-6 h-6" />,
    steps: [
      'Lead Generator qualifies prospects from your lead list',
      'Account Executive creates proposals and runs demos',
      'Contract Specialist handles negotiations through close',
    ],
  },
  ciso: {
    icon: <FileText className="w-6 h-6" />,
    steps: [
      'Threat Analyst assesses and classifies the incident',
      'Security Engineer implements mitigations and patches',
      'Compliance Officer audits and verifies resolution',
    ],
  },
};

function EmptyBoardState({
  inputNoun, itemNoun, templateId, onSubmit, isPublisher, onGenerate, onReplay, hasPlayed,
}: {
  inputNoun: string;
  itemNoun: string;
  templateId: string;
  onSubmit: () => void;
  isPublisher: boolean;
  onGenerate?: () => void;
  onReplay?: () => void;
  hasPlayed?: boolean;
}) {
  const workflow = WORKFLOW_STEPS[templateId] || WORKFLOW_STEPS.software_dev;
  const article = /^[aeiou]/i.test(inputNoun) ? 'an' : 'a';

  return (
    <div className="flex items-center justify-center h-full px-8">
      <div className="max-w-lg w-full text-center animate-fade-in">
        <div className="mx-auto w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500/20 to-indigo-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-6">
          <Zap className="w-7 h-7" />
        </div>

        <h2 className="text-2xl font-semibold tracking-tight text-foreground mb-2">
          Get started in seconds
        </h2>
        <p className="text-muted-foreground mb-8 text-sm leading-relaxed">
          Submit {inputNoun === 'PRD' ? 'a' : article}{' '}
          <span className="text-foreground font-medium">{inputNoun}</span> and watch AI agents
          turn it into actionable {itemNoun.toLowerCase()}s on this board.
        </p>

        <div className="flex flex-col items-center gap-3 mb-8">
          {isPublisher ? (
            <button
              onClick={onGenerate}
              className="inline-flex items-center gap-2 h-11 px-6 rounded-lg font-medium bg-gradient-to-br from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 text-white shadow-lg shadow-purple-600/30 transition-all hover:scale-[1.02]"
            >
              <Sparkles className="w-4 h-4" />
              Generate {itemNoun}s
            </button>
          ) : (
            <button
              onClick={onSubmit}
              className="inline-flex items-center gap-2 h-11 px-6 rounded-lg font-medium bg-gradient-to-br from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-600/30 transition-all hover:scale-[1.02]"
            >
              <FileText className="w-4 h-4" />
              Submit {inputNoun}
            </button>
          )}
          {!isPublisher && (
            <span className="text-xs text-muted-foreground/70">
              Don't have one? The modal includes an example you can try instantly.
            </span>
          )}
          {onReplay && hasPlayed && (
            <button
              onClick={onReplay}
              className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors mt-1"
            >
              <RotateCcw className="w-3 h-3" />
              Replay 30-second demo
            </button>
          )}
        </div>

        <div className="surface p-5 text-left">
          <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-[0.1em] mb-4">
            How it works
          </h3>
          <div className="space-y-3">
            {workflow.steps.map((step, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-md bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center text-[11px] font-semibold mt-0.5">
                  {i + 1}
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">{step}</p>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2 mt-4 pt-3 border-t border-border/60">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
            <p className="text-xs text-muted-foreground">
              Everything happens automatically — just watch your board fill up.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export function KanbanBoard() {
  const { stories, selectedStoryId, setSelectedStory, isLoading } = useStoryStore();
  const currentBoard = usePipelineStore((s) => s.currentBoard);
  const epics = usePipelineStore((s) => s.epics);
  const selectedEpicId = usePipelineStore((s) => s.selectedEpicId);
  const setSelectedEpic = usePipelineStore((s) => s.setSelectedEpic);
  const fetchEpics = usePipelineStore((s) => s.fetchEpics);
  const openPRDModal = useUIStore((s) => s.openPRDModal);
  const { fetchStories } = useStoryStore();
  const activeIds = useStoryActivity();
  const replay = useDemoReplay(currentBoard?.id ?? null);

  const epicNoun = currentBoard?.epic_noun ?? 'Epic';
  const inputNoun = currentBoard?.input_noun ?? 'PRD';
  const itemNoun = currentBoard?.item_noun ?? 'Story';
  const templateId = currentBoard?.template_id ?? 'software_dev';
  const automationEnabled = currentBoard?.agent_automation === true;
  const isPublisher = templateId === 'publisher';

  useEffect(() => {
    if (currentBoard?.id) fetchEpics(currentBoard.id);
  }, [currentBoard?.id, fetchEpics]);

  const columns: PipelineColumn[] = currentBoard?.columns ?? [];

  const filteredStories = selectedEpicId
    ? stories.filter((s) => s.epic_id === selectedEpicId)
    : stories;

  const storiesByStatus = columns.reduce(
    (acc, col) => {
      acc[col.key] = filteredStories.filter((s) => s.status === col.key);
      return acc;
    },
    {} as Record<string, Story[]>
  );

  if (isLoading && stories.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-7 w-7 border-2 border-border border-t-primary" />
      </div>
    );
  }

  if (columns.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-muted-foreground">
        No board selected
      </div>
    );
  }

  const boardIsEmpty = stories.length === 0;
  if (boardIsEmpty && automationEnabled) {
    return (
      <EmptyBoardState
        inputNoun={inputNoun}
        itemNoun={itemNoun}
        templateId={templateId}
        onSubmit={openPRDModal}
        isPublisher={isPublisher}
        onGenerate={async () => {
          if (!currentBoard?.id) return;
          await simulateApi.generate(currentBoard.id);
          fetchStories(currentBoard.id);
        }}
        onReplay={replay.play}
        hasPlayed={replay.hasPlayed}
      />
    );
  }

  return (
    <div className="flex flex-col h-full">
      {replay.isReplaying && (
        <div className="mx-4 mb-3 flex items-center gap-3 px-3 py-2 rounded-md border border-primary/30 bg-primary/8 animate-fade-in">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-primary opacity-75 animate-ping" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
          </span>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-foreground">Demo replay running</div>
            <div className="text-[10px] text-muted-foreground">
              Watching a recorded run of the software dev swarm shipping a feature
            </div>
          </div>
          <button
            onClick={replay.skip}
            className="inline-flex items-center gap-1 h-7 px-2.5 rounded-md text-[11px] font-medium border border-border hover:bg-accent text-foreground transition-colors"
          >
            <X className="w-3 h-3" />
            Skip
          </button>
        </div>
      )}
      {!replay.isReplaying && replay.hasPlayed && stories.some((s) => s.id < 0) && (
        <div className="mx-4 mb-3 flex items-center gap-3 px-3 py-2 rounded-md border border-border bg-card/40 animate-fade-in">
          <Play className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-foreground">This was a demo replay</div>
            <div className="text-[10px] text-muted-foreground">
              Add your Gemini API key in Settings to run your own briefs through real agents
            </div>
          </div>
          <button
            onClick={replay.play}
            className="inline-flex items-center gap-1 h-7 px-2.5 rounded-md text-[11px] font-medium border border-border hover:bg-accent text-foreground transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            Replay
          </button>
        </div>
      )}
      {epics.length > 0 && (
        <div className="px-4 pb-3 flex items-center gap-2">
          <label className="text-xs uppercase tracking-wider text-muted-foreground font-medium">{epicNoun}</label>
          <select
            className="bg-card text-sm text-foreground border border-border rounded-md px-2.5 py-1 h-8 focus:outline-none focus:ring-2 focus:ring-ring"
            value={selectedEpicId ?? ''}
            onChange={(e) => setSelectedEpic(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">All {epicNoun}s</option>
            {epics.map((epic) => (
              <option key={epic.id} value={epic.id}>{epic.title}</option>
            ))}
          </select>
        </div>
      )}
      <div className="flex gap-3 overflow-x-auto px-4 flex-1 pb-4">
        {columns.map((col) => (
          <KanbanColumn
            key={col.key}
            columnKey={col.key}
            label={col.label}
            color={col.color}
            stories={storiesByStatus[col.key] || []}
            selectedStoryId={selectedStoryId}
            activeIds={activeIds}
            onSelectStory={setSelectedStory}
          />
        ))}
      </div>
    </div>
  );
}
