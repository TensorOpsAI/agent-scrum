import { clsx } from 'clsx';
import { FileText, CheckCircle, Circle } from 'lucide-react';
import type { Story } from '../../types';
import { getStatusLabel, getStatusColor } from '../../types';
import { usePipelineStore } from '../../store/pipelineStore';

interface StoryCardProps {
  story: Story;
  isSelected: boolean;
  onClick: () => void;
}

export function StoryCard({ story, isSelected, onClick }: StoryCardProps) {
  const columns = usePipelineStore((s) => s.activeConfig?.columns ?? []);

  const progress =
    story.task_count > 0
      ? Math.round((story.completed_task_count / story.task_count) * 100)
      : 0;

  // Derive border color from the column's bg color
  const bgColor = getStatusColor(story.status, columns);
  const borderColor = bgColor.replace('bg-', 'border-l-');

  return (
    <div
      onClick={onClick}
      className={clsx(
        'bg-gray-800 rounded-lg p-4 cursor-pointer transition-all border-l-4',
        'hover:bg-gray-750 hover:shadow-lg',
        borderColor,
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
          {getStatusLabel(story.status, columns)}
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
