import { clsx } from 'clsx';
import { Bot } from 'lucide-react';
import type { Comment } from '../../types';
import { getAgentLabel, getAgentColor } from '../../types';

interface ActivityLogProps {
  comments: Comment[];
}

export function ActivityLog({ comments }: ActivityLogProps) {
  if (comments.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 text-sm">
        No activity yet
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {comments.map((comment) => (
        <div key={comment.id} className="flex gap-3">
          {/* Agent avatar */}
          <div className={clsx(
            'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
            getAgentColor(comment.agent_type)
          )}>
            <Bot className="w-4 h-4 text-white" />
          </div>

          {/* Comment content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium text-white text-sm">
                {getAgentLabel(comment.agent_type)}
              </span>
              <span className="text-xs text-gray-500">
                {formatDate(comment.created_at)}
              </span>
            </div>

            <div className="bg-gray-900 rounded-lg p-3">
              <div className="text-sm text-gray-300 whitespace-pre-wrap">
                {comment.content}
              </div>

              {comment.metadata && Object.keys(comment.metadata).length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-700">
                  <div className="flex flex-wrap gap-2">
                    {'action' in comment.metadata && comment.metadata.action != null && (
                      <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-300">
                        {formatAction(String(comment.metadata.action))}
                      </span>
                    )}
                    {'approved' in comment.metadata && (
                      <span className={clsx(
                        'text-xs px-2 py-0.5 rounded',
                        comment.metadata.approved ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
                      )}>
                        {comment.metadata.approved ? 'Approved' : 'Changes Requested'}
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  // Less than 1 minute
  if (diff < 60000) {
    return 'just now';
  }

  // Less than 1 hour
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000);
    return `${minutes}m ago`;
  }

  // Less than 24 hours
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000);
    return `${hours}h ago`;
  }

  // More than 24 hours
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatAction(action: string): string {
  return action
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
