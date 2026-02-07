import { useState, useEffect } from 'react';
import { X, Loader2, Bot, Users } from 'lucide-react';
import { clsx } from 'clsx';
import { usePipelineStore } from '../../store/pipelineStore';
import { useStoryStore } from '../../store/storyStore';
import type { PipelineTemplate } from '../../types';

interface PipelineModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function PipelineModal({ isOpen, onClose }: PipelineModalProps) {
  const { templates, fetchTemplates, createBoard, isLoading } = usePipelineStore();
  const { fetchStories } = useStoryStore();
  const [selectedTemplate, setSelectedTemplate] = useState<PipelineTemplate | null>(null);
  const [boardName, setBoardName] = useState('');
  const [showNameInput, setShowNameInput] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchTemplates();
      setSelectedTemplate(null);
      setBoardName('');
      setShowNameInput(false);
    }
  }, [isOpen, fetchTemplates]);

  const handleSelect = (template: PipelineTemplate) => {
    setSelectedTemplate(template);
    setBoardName(template.name);
    setShowNameInput(true);
  };

  const handleCreate = async () => {
    if (!selectedTemplate) return;
    const board = await createBoard(selectedTemplate.template_id, boardName || undefined);
    fetchStories(board.id);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />

      <div className="relative bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700 shrink-0">
          <h2 className="text-lg font-semibold text-white">New Board</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-700 rounded-lg transition-colors">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1">
          {/* Name input */}
          {showNameInput && selectedTemplate && (
            <div className="mb-6 bg-gray-900 rounded-lg p-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Board Name
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={boardName}
                  onChange={(e) => setBoardName(e.target.value)}
                  placeholder={selectedTemplate.name}
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  autoFocus
                  onKeyDown={(e) => { if (e.key === 'Enter') handleCreate(); }}
                />
                <button
                  onClick={handleCreate}
                  disabled={isLoading}
                  className="px-4 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 font-medium transition-colors"
                >
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create'}
                </button>
                <button
                  onClick={() => { setShowNameInput(false); setSelectedTemplate(null); }}
                  className="px-3 py-2 text-sm rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors"
                >
                  Back
                </button>
              </div>
            </div>
          )}

          {/* Template cards */}
          <div className="grid grid-cols-1 gap-4">
            {templates.map((template) => (
              <div
                key={template.template_id}
                onClick={() => handleSelect(template)}
                className={clsx(
                  'rounded-lg border p-4 transition-all cursor-pointer',
                  selectedTemplate?.template_id === template.template_id
                    ? 'border-blue-500 bg-blue-900/20'
                    : 'border-gray-700 hover:border-gray-500 hover:bg-gray-750'
                )}
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium text-white">{template.name}</h3>
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    {template.agent_automation ? (
                      <span className="flex items-center gap-1">
                        <Bot className="w-3.5 h-3.5" /> Automated
                      </span>
                    ) : (
                      <span className="flex items-center gap-1">
                        <Users className="w-3.5 h-3.5" /> Manual
                      </span>
                    )}
                    <span className="text-gray-600">|</span>
                    <span>{template.item_noun}s</span>
                  </div>
                </div>

                {/* Column preview */}
                <div className="flex gap-1.5 overflow-x-auto">
                  {template.columns.map((col) => (
                    <div
                      key={col.key}
                      className={clsx(
                        'px-2 py-1 rounded text-xs text-white whitespace-nowrap',
                        col.color
                      )}
                    >
                      {col.label}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
