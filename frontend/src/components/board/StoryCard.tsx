import { useState } from 'react';
import { CheckCircle2, Circle, FileText, Eye } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { Story } from '../../types';
import { getStatusLabel, getStatusColor } from '../../types';
import { usePipelineStore } from '../../store/pipelineStore';
import { ArticlePreviewModal } from '../modals/ArticlePreviewModal';

interface StoryCardProps {
  story: Story;
  isSelected: boolean;
  isActive?: boolean;
  onClick: () => void;
}

export function StoryCard({ story, isSelected, isActive, onClick }: StoryCardProps) {
  const columns = usePipelineStore((s) => s.activeConfig?.columns ?? []);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  const progress =
    story.task_count > 0
      ? Math.round((story.completed_task_count / story.task_count) * 100)
      : 0;

  const dotColor = getStatusColor(story.status, columns);
  const isPublished = story.status === 'published';

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onClick(); }}
      className={cn(
        'group relative w-full text-left rounded-lg p-3 transition-all cursor-pointer',
        'bg-card border border-border/80 hover:border-border',
        'hover:bg-accent/40 hover:-translate-y-px hover:shadow-lg hover:shadow-black/20',
        isSelected && 'border-primary/60 bg-accent/40 ring-1 ring-primary/40',
        isActive && 'ring-2 ring-primary/60 shadow-lg shadow-primary/20 animate-pulse-active'
      )}
    >
      {isActive && (
        <span
          aria-hidden
          className="absolute -top-1 -right-1 inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-medium bg-primary text-primary-foreground shadow-md animate-fade-in"
        >
          <span className="w-1 h-1 rounded-full bg-white animate-pulse" />
          en vivo
        </span>
      )}
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <h3 className="font-medium text-sm text-foreground leading-snug line-clamp-2 flex-1">
          {story.title}
        </h3>
        <span className="text-[10px] font-mono text-muted-foreground/70 mt-0.5 whitespace-nowrap">
          #{story.id}
        </span>
      </div>

      {story.description && (
        <p className="text-xs text-muted-foreground mb-2.5 line-clamp-2 leading-relaxed">
          {story.description}
        </p>
      )}

      <div className="flex items-center justify-between gap-2 mt-2">
        <span className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <span className={cn('status-dot', dotColor)} />
          {getStatusLabel(story.status, columns)}
        </span>

        {isPublished ? (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsPreviewOpen(true);
            }}
            className="inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline"
          >
            <Eye className="w-3.5 h-3.5" />
            Vista previa
          </button>
        ) : story.task_count > 0 ? (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
              {story.completed_task_count === story.task_count ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              ) : (
                <Circle className="w-3.5 h-3.5" />
              )}
              <span className="tabular-nums">
                {story.completed_task_count}/{story.task_count}
              </span>
            </div>
            <div className="w-12 h-1 bg-secondary rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        ) : (
          <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground/60">
            <FileText className="w-3 h-3" />
            vacío
          </span>
        )}
      </div>

      {isPublished && (
        <ArticlePreviewModal
          isOpen={isPreviewOpen}
          onClose={() => setIsPreviewOpen(false)}
          story={story}
        />
      )}
    </div>
  );
}
