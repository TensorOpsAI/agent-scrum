import { useEffect } from 'react';
import { clsx } from 'clsx';
import { useStoryStore } from '../../store/storyStore';
import { StoryCard } from './StoryCard';
import type { Story, StoryStatus } from '../../types';
import { STORY_STATUS_LABELS } from '../../types';

const BOARD_COLUMNS: StoryStatus[] = [
  'backlog',
  'ready_for_breakdown',
  'in_breakdown',
  'tasks_in_review',
  'in_development',
  'in_qa',
  'done',
];

const columnColors: Record<StoryStatus, string> = {
  backlog: 'bg-gray-600',
  ready_for_breakdown: 'bg-blue-600',
  in_breakdown: 'bg-blue-500',
  tasks_in_review: 'bg-purple-600',
  in_development: 'bg-yellow-600',
  in_qa: 'bg-pink-600',
  done: 'bg-green-600',
};

interface KanbanColumnProps {
  status: StoryStatus;
  stories: Story[];
  selectedStoryId: number | null;
  onSelectStory: (id: number) => void;
}

function KanbanColumn({
  status,
  stories,
  selectedStoryId,
  onSelectStory,
}: KanbanColumnProps) {
  return (
    <div className="flex flex-col min-w-[280px] w-[280px] bg-gray-850 rounded-lg h-full">
      <div
        className={clsx(
          'px-4 py-3 rounded-t-lg flex items-center justify-between flex-shrink-0',
          columnColors[status]
        )}
      >
        <h2 className="font-semibold text-white text-sm">
          {STORY_STATUS_LABELS[status]}
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
            No stories
          </div>
        )}
      </div>
    </div>
  );
}

export function KanbanBoard() {
  const { stories, selectedStoryId, setSelectedStory, fetchStories, isLoading } =
    useStoryStore();

  useEffect(() => {
    fetchStories();
  }, [fetchStories]);

  const storiesByStatus = BOARD_COLUMNS.reduce(
    (acc, status) => {
      acc[status] = stories.filter((s) => s.status === status);
      return acc;
    },
    {} as Record<StoryStatus, Story[]>
  );

  if (isLoading && stories.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div className="flex gap-4 overflow-x-auto px-4 h-full pb-4">
      {BOARD_COLUMNS.map((status) => (
        <KanbanColumn
          key={status}
          status={status}
          stories={storiesByStatus[status]}
          selectedStoryId={selectedStoryId}
          onSelectStory={setSelectedStory}
        />
      ))}
    </div>
  );
}
