import { useEffect, useState } from 'react';
import { X, ChevronRight, FileText, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { clsx } from 'clsx';
import { storyApi, taskApi } from '../../api/client';
import { ActivityLog } from './ActivityLog';
import type { Story, Task, Comment } from '../../types';
import { TASK_STATUS_LABELS, getAgentLabel, getAgentColor, getStatusLabel } from '../../types';
import { usePipelineStore } from '../../store/pipelineStore';

interface StoryDetailProps {
  storyId: number;
  onClose: () => void;
}

const taskStatusColors: Record<string, string> = {
  draft: 'bg-gray-500',
  pending_review: 'bg-yellow-500',
  ready_for_development: 'bg-blue-500',
  in_progress: 'bg-blue-400',
  code_review: 'bg-purple-500',
  ready_for_qa: 'bg-pink-500',
  qa_in_progress: 'bg-pink-400',
  done: 'bg-green-500',
};

export function StoryDetail({ storyId, onClose }: StoryDetailProps) {
  const columns = usePipelineStore((s) => s.activeConfig?.columns ?? []);
  const [story, setStory] = useState<Story | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const [storyData, tasksData, commentsData] = await Promise.all([
          storyApi.get(storyId),
          taskApi.list(storyId),
          storyApi.getComments(storyId),
        ]);
        setStory(storyData);
        setTasks(tasksData);
        setComments(commentsData);
      } catch (error) {
        console.error('Error fetching story details:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [storyId]);

  if (loading) {
    return (
      <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (!story) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-40 flex">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Slide-over panel */}
      <div className="relative ml-auto w-full max-w-4xl bg-gray-800 shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <FileText className="w-5 h-5 text-blue-500" />
            <div>
              <h2 className="text-lg font-semibold text-white">
                Story #{story.id}
              </h2>
              <span className={clsx(
                'text-xs px-2 py-0.5 rounded',
                story.status === 'done' ? 'bg-green-600' : 'bg-gray-600'
              )}>
                {getStatusLabel(story.status, columns)}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Story info */}
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-white mb-2">{story.title}</h3>
            {story.description && (
              <p className="text-gray-300 mb-4">{story.description}</p>
            )}

            {story.acceptance_criteria && (
              <div className="bg-gray-900 rounded-lg p-4 mb-4">
                <h4 className="text-sm font-medium text-gray-400 mb-2">
                  Acceptance Criteria
                </h4>
                <div className="text-gray-300 whitespace-pre-wrap text-sm">
                  {story.acceptance_criteria}
                </div>
              </div>
            )}

            <div className="flex items-center gap-4 text-sm text-gray-400">
              <span>Priority: {story.priority}</span>
              <span>Tasks: {story.completed_task_count}/{story.task_count}</span>
            </div>
          </div>

          {/* Tasks section */}
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-400 mb-3">Tasks</h4>
            {tasks.length === 0 ? (
              <p className="text-gray-500 text-sm">No tasks yet</p>
            ) : (
              <div className="space-y-2">
                {tasks.map((task) => (
                  <div
                    key={task.id}
                    onClick={() => setSelectedTaskId(task.id === selectedTaskId ? null : task.id)}
                    className={clsx(
                      'bg-gray-900 rounded-lg p-4 cursor-pointer transition-all',
                      selectedTaskId === task.id && 'ring-2 ring-blue-500'
                    )}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {task.status === 'done' ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : task.status.includes('progress') ? (
                          <Clock className="w-4 h-4 text-yellow-500" />
                        ) : (
                          <AlertCircle className="w-4 h-4 text-gray-500" />
                        )}
                        <span className="font-medium text-white">{task.title}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={clsx(
                          'text-xs px-2 py-0.5 rounded',
                          taskStatusColors[task.status]
                        )}>
                          {TASK_STATUS_LABELS[task.status]}
                        </span>
                        <ChevronRight className={clsx(
                          'w-4 h-4 text-gray-400 transition-transform',
                          selectedTaskId === task.id && 'rotate-90'
                        )} />
                      </div>
                    </div>

                    {/* Expanded task details */}
                    {selectedTaskId === task.id && (
                      <div className="mt-4 pt-4 border-t border-gray-700">
                        {task.description && (
                          <div className="mb-4">
                            <h5 className="text-xs font-medium text-gray-400 mb-1">Description</h5>
                            <p className="text-sm text-gray-300">{task.description}</p>
                          </div>
                        )}

                        {task.implementation_notes && (
                          <div className="mb-4">
                            <h5 className="text-xs font-medium text-gray-400 mb-1">Implementation Notes</h5>
                            <div className="text-sm text-gray-300 bg-gray-800 rounded p-3 whitespace-pre-wrap max-h-48 overflow-y-auto">
                              {task.implementation_notes}
                            </div>
                          </div>
                        )}

                        {task.test_scenarios && (
                          <div className="mb-4">
                            <h5 className="text-xs font-medium text-gray-400 mb-1">Test Scenarios</h5>
                            <div className="text-sm text-gray-300 bg-gray-800 rounded p-3 whitespace-pre-wrap max-h-48 overflow-y-auto">
                              {task.test_scenarios}
                            </div>
                          </div>
                        )}

                        {task.assigned_agent && (
                          <div className="flex items-center gap-2">
                            <span className={clsx(
                              'text-xs px-2 py-0.5 rounded',
                              getAgentColor(task.assigned_agent)
                            )}>
                              {getAgentLabel(task.assigned_agent)}
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Activity Log */}
          <div>
            <h4 className="text-sm font-medium text-gray-400 mb-3">Activity</h4>
            <ActivityLog comments={comments} />
          </div>
        </div>
      </div>
    </div>
  );
}
