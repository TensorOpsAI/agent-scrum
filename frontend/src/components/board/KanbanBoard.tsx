import { useEffect } from 'react';
import { clsx } from 'clsx';
import { FileText, Sparkles, Zap, CheckCircle2 } from 'lucide-react';
import { useStoryStore } from '../../store/storyStore';
import { usePipelineStore } from '../../store/pipelineStore';
import { useUIStore } from '../../store/uiStore';
import { StoryCard } from './StoryCard';
import type { Story, PipelineColumn } from '../../types';

interface KanbanColumnProps {
  columnKey: string;
  label: string;
  color: string;
  stories: Story[];
  selectedStoryId: number | null;
  onSelectStory: (id: number) => void;
}

function KanbanColumn({
  columnKey,
  label,
  color,
  stories,
  selectedStoryId,
  onSelectStory,
}: KanbanColumnProps) {
  return (
    <div className="flex flex-col min-w-[280px] w-[280px] bg-gray-850 rounded-lg h-full" data-status={columnKey}>
      <div
        className={clsx(
          'px-4 py-3 rounded-t-lg flex items-center justify-between flex-shrink-0',
          color
        )}
      >
        <h2 className="font-semibold text-white text-sm">
          {label}
        </h2>
        <span className="px-2 py-0.5 rounded-full bg-white/20 text-white text-xs font-medium">
          {stories.length}
        </span>
      </div>

      <div className="flex-1 p-3 space-y-3 overflow-y-auto">
        {stories.map((story) => (
          <StoryCard
            key={story.id}
            story={story}
            isSelected={selectedStoryId === story.id}
            onClick={() => onSelectStory(story.id)}
          />
        ))}

        {stories.length === 0 && (
          <div className="text-center py-8 text-gray-500 text-sm">
            No items
          </div>
        )}
      </div>
    </div>
  );
}

// Descriptions of what happens after submission, per template
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
  inputNoun,
  itemNoun,
  templateId,
  onSubmit,
  isPublisher,
  onGenerate,
}: {
  inputNoun: string;
  itemNoun: string;
  templateId: string;
  onSubmit: () => void;
  isPublisher: boolean;
  onGenerate?: () => void;
}) {
  const workflow = WORKFLOW_STEPS[templateId] || WORKFLOW_STEPS.software_dev;

  return (
    <div className="flex items-center justify-center h-full px-8">
      <div className="max-w-lg w-full text-center">
        {/* Hero icon */}
        <div className="mx-auto w-16 h-16 rounded-2xl bg-blue-600/20 flex items-center justify-center text-blue-400 mb-6">
          <Zap className="w-8 h-8" />
        </div>

        <h2 className="text-2xl font-bold text-white mb-2">
          Get started in seconds
        </h2>
        <p className="text-gray-400 mb-8 text-base leading-relaxed">
          Submit {inputNoun === 'PRD' ? 'a' : (/^[aeiou]/i.test(inputNoun) ? 'an' : 'a')}{' '}
          <span className="text-gray-200 font-medium">{inputNoun}</span> and watch AI agents
          turn it into actionable {itemNoun.toLowerCase()}s on this board.
        </p>

        {/* CTA buttons */}
        <div className="flex flex-col items-center gap-3 mb-10">
          {isPublisher ? (
            <button
              onClick={onGenerate}
              className="flex items-center gap-2.5 px-8 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-semibold text-base transition-colors shadow-lg shadow-purple-600/20"
            >
              <Sparkles className="w-5 h-5" />
              Generate {itemNoun}s
            </button>
          ) : (
            <button
              onClick={onSubmit}
              className="flex items-center gap-2.5 px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold text-base transition-colors shadow-lg shadow-blue-600/20"
            >
              <FileText className="w-5 h-5" />
              Submit {inputNoun}
            </button>
          )}
          {!isPublisher && (
            <span className="text-xs text-gray-500">
              Don't have one? The modal includes an example you can try instantly.
            </span>
          )}
        </div>

        {/* How it works */}
        <div className="bg-gray-800/60 rounded-xl border border-gray-700/50 p-5 text-left">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
            How it works
          </h3>
          <div className="space-y-3">
            {workflow.steps.map((step, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-600/20 text-blue-400 flex items-center justify-center text-xs font-bold mt-0.5">
                  {i + 1}
                </div>
                <p className="text-sm text-gray-300 leading-relaxed">{step}</p>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2 mt-4 pt-3 border-t border-gray-700/50">
            <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
            <p className="text-xs text-gray-400">
              Everything happens automatically — just watch your board fill up.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export function KanbanBoard() {
  const { stories, selectedStoryId, setSelectedStory, isLoading } =
    useStoryStore();
  const currentBoard = usePipelineStore((s) => s.currentBoard);
  const epics = usePipelineStore((s) => s.epics);
  const selectedEpicId = usePipelineStore((s) => s.selectedEpicId);
  const setSelectedEpic = usePipelineStore((s) => s.setSelectedEpic);
  const fetchEpics = usePipelineStore((s) => s.fetchEpics);
  const openPRDModal = useUIStore((s) => s.openPRDModal);
  const onGenerate = useUIStore((s) => s.onGenerate);

  const epicNoun = currentBoard?.epic_noun ?? 'Epic';
  const inputNoun = currentBoard?.input_noun ?? 'PRD';
  const itemNoun = currentBoard?.item_noun ?? 'Story';
  const templateId = currentBoard?.template_id ?? 'software_dev';
  const automationEnabled = currentBoard?.agent_automation === true;
  const isPublisher = templateId === 'publisher';

  useEffect(() => {
    if (currentBoard?.id) {
      fetchEpics(currentBoard.id);
    }
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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (columns.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No board selected
      </div>
    );
  }

  // Show guided empty state when board has no stories and automation is on
  const boardIsEmpty = stories.length === 0;
  if (boardIsEmpty && automationEnabled) {
    return (
      <EmptyBoardState
        inputNoun={inputNoun}
        itemNoun={itemNoun}
        templateId={templateId}
        onSubmit={openPRDModal}
        isPublisher={isPublisher}
        onGenerate={onGenerate ?? undefined}
      />
    );
  }

  return (
    <div className="flex flex-col h-full">
      {epics.length > 0 && (
        <div className="px-4 pb-3 flex items-center gap-2">
          <label className="text-sm text-gray-400">{epicNoun}:</label>
          <select
            className="bg-gray-800 text-sm text-gray-200 border border-gray-600 rounded px-2 py-1"
            value={selectedEpicId ?? ''}
            onChange={(e) => setSelectedEpic(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">All {epicNoun}s</option>
            {epics.map((epic) => (
              <option key={epic.id} value={epic.id}>
                {epic.title}
              </option>
            ))}
          </select>
        </div>
      )}
      <div className="flex gap-4 overflow-x-auto px-4 flex-1 pb-4">
      {columns.map((col) => (
        <KanbanColumn
          key={col.key}
          columnKey={col.key}
          label={col.label}
          color={col.color}
          stories={storiesByStatus[col.key] || []}
          selectedStoryId={selectedStoryId}
          onSelectStory={setSelectedStory}
        />
      ))}
      </div>
    </div>
  );
}
