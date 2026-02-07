import { useState } from 'react';
import { X, FileText, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import { prdApi } from '../../api/client';
import { usePipelineStore } from '../../store/pipelineStore';

interface PRDInputModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function PRDInputModal({ isOpen, onClose }: PRDInputModalProps) {
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const currentBoardId = usePipelineStore((s) => s.currentBoardId);
  const currentBoard = usePipelineStore((s) => s.currentBoard);

  const inputNoun = currentBoard?.input_noun ?? 'PRD';
  const inputPlaceholder = currentBoard?.input_placeholder ??
    `Paste your ${inputNoun} here...`;

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim() || !currentBoardId) return;

    setIsSubmitting(true);
    setError(null);

    try {
      await prdApi.submit(content, currentBoardId, title || undefined);
      setContent('');
      setTitle('');
      onClose();
    } catch (err) {
      setError(`Failed to submit ${inputNoun}. Please try again.`);
      console.error(`Error submitting ${inputNoun}:`, err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <FileText className="w-5 h-5 text-blue-500" />
            <h2 className="text-lg font-semibold text-white">Submit {inputNoun}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            <div>
              <label
                htmlFor="title"
                className="block text-sm font-medium text-gray-300 mb-2"
              >
                Title (optional)
              </label>
              <input
                type="text"
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder={`Enter a title for this ${inputNoun}...`}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label
                htmlFor="content"
                className="block text-sm font-medium text-gray-300 mb-2"
              >
                {inputNoun} Content
              </label>
              <textarea
                id="content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder={inputPlaceholder}
                rows={12}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm resize-none"
              />
            </div>

            {error && (
              <div className="p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-300 text-sm">
                {error}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!content.trim() || !currentBoardId || isSubmitting}
              className={clsx(
                'flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-colors',
                content.trim() && currentBoardId && !isSubmitting
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-gray-600 text-gray-400 cursor-not-allowed'
              )}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                `Submit ${inputNoun}`
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
