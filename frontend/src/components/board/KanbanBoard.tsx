import { clsx } from 'clsx';
import { useStoryStore } from '../../store/storyStore';
import { usePipelineStore } from '../../store/pipelineStore';
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
            No stories
          </div>
        )}
      </div>
    </div>
  );
}

export function KanbanBoard() {
  const { stories, selectedStoryId, setSelectedStory, isLoading } =
    useStoryStore();
  const currentBoard = usePipelineStore((s) => s.currentBoard);

  const columns: PipelineColumn[] = currentBoard?.columns ?? [];

  const storiesByStatus = columns.reduce(
    (acc, col) => {
      acc[col.key] = stories.filter((s) => s.status === col.key);
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

  return (
    <div className="flex gap-4 overflow-x-auto px-4 h-full pb-4">
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
  );
}
