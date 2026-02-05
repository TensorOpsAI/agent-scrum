import { clsx } from 'clsx';
import { FileText, CheckCircle, Circle } from 'lucide-react';
import type { Story } from '../../types';
import { STORY_STATUS_LABELS } from '../../types';

interface StoryCardProps {
  story: Story;
  isSelected: boolean;
  onClick: () => void;
}

const statusColors: Record<string, string> = {
  backlog: 'border-l-gray-500',
  ready_for_breakdown: 'border-l-blue-500',
  in_breakdown: 'border-l-blue-400',
  tasks_in_review: 'border-l-purple-500',
  in_development: 'border-l-yellow-500',
  in_qa: 'border-l-pink-500',
  done: 'border-l-green-500',
};

export function StoryCard({ story, isSelected, onClick }: StoryCardProps) {
  const progress =
    story.task_count > 0
      ? Math.round((story.completed_task_count / story.task_count) * 100)
      : 0;

  return (
    <div
      onClick={onClick}
      className={clsx(
        'bg-gray-800 rounded-lg p-4 cursor-pointer transition-all border-l-4',
        'hover:bg-gray-750 hover:shadow-lg',
        statusColors[story.status],
        isSelected && 'ring-2 ring-blue-500 bg-gray-750'
      )}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="font-medium text-gray-100 line-clamp-2">{story.title}</h3>
        <span className="text-xs text-gray-400 whitespace-nowrap">
          #{story.id}
        </span>
      </div>

      {story.description && (
        <p className="text-sm text-gray-400 mb-3 line-clamp-2">
          {story.description}
        </p>
      )}

      <div className="flex items-center justify-between text-xs">
        <span className="px-2 py-1 rounded bg-gray-700 text-gray-300">
          {STORY_STATUS_LABELS[story.status]}
        </span>

        {story.task_count > 0 && (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 text-gray-400">
              {story.completed_task_count === story.task_count ? (
                <CheckCircle className="w-4 h-4 text-green-500" />
              ) : (
                <Circle className="w-4 h-4" />
              )}
              <span>
                {story.completed_task_count}/{story.task_count}
              </span>
            </div>
            <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {story.task_count === 0 && (
          <div className="flex items-center gap-1 text-gray-500">
            <FileText className="w-4 h-4" />
            <span>No tasks</span>
          </div>
        )}
      </div>
    </div>
  );
}
