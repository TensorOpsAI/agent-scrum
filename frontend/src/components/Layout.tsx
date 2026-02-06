import { Outlet } from 'react-router-dom';
import { Bot, Plus, Settings, Users, AlertCircle, X } from 'lucide-react';
import { useState, useEffect } from 'react';
import { clsx } from 'clsx';
import { PRDInputModal } from './modals/PRDInputModal';
import { SettingsModal } from './modals/SettingsModal';
import { PipelineModal } from './modals/PipelineModal';
import { AgentPanel } from './agents/AgentPanel';
import { AgentManager } from './agents/AgentManager';
import { ChatPanel } from './chat/ChatPanel';
import { StoryDetail } from './story/StoryDetail';
import { useStoryStore } from '../store/storyStore';
import { usePipelineStore } from '../store/pipelineStore';
import { storyApi } from '../api/client';

export function Layout() {
  const [isPRDModalOpen, setIsPRDModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [isPipelineModalOpen, setIsPipelineModalOpen] = useState(false);
  const [isAgentManagerOpen, setIsAgentManagerOpen] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const { selectedStoryId, setSelectedStory, fetchStories } = useStoryStore();
  const {
    boards,
    currentBoardId,
    currentBoard,
    fetchBoards,
    setCurrentBoard,
    deleteBoard,
  } = usePipelineStore();

  useEffect(() => {
    fetchBoards();
  }, [fetchBoards]);

  // Re-fetch stories when currentBoardId changes
  useEffect(() => {
    if (currentBoardId != null) {
      fetchStories(currentBoardId);
    }
  }, [currentBoardId, fetchStories]);

  // Auto-clear error after 3 seconds
  useEffect(() => {
    if (addError) {
      const timer = setTimeout(() => setAddError(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [addError]);

  const automationEnabled = currentBoard?.agent_automation === true;
  const itemNoun = currentBoard?.item_noun ?? 'Story';

  const handleAddItem = async () => {
    if (!currentBoardId) return;
    setIsAdding(true);
    setAddError(null);
    try {
      await storyApi.create({
        board_id: currentBoardId,
        title: `New ${itemNoun}`,
        description: '',
        priority: 0,
      });
      fetchStories(currentBoardId);
    } catch (error) {
      console.error('Error creating item:', error);
      setAddError('Failed to create item. Is the backend running?');
    } finally {
      setIsAdding(false);
    }
  };

  const handleDeleteBoard = async (boardId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const board = boards.find((b) => b.id === boardId);
    if (!board) return;
    if (!confirm(`Delete board "${board.name}"? All its stories will be permanently deleted.`)) return;
    await deleteBoard(boardId);
    // Fetch stories for the new current board
    const newCurrentId = usePipelineStore.getState().currentBoardId;
    if (newCurrentId) fetchStories(newCurrentId);
  };

  return (
    <div className="h-screen bg-gray-900 flex flex-col overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 bg-gray-800 border-b border-gray-700 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <Bot className="w-7 h-7 text-blue-500 flex-shrink-0" />
            <h1 className="text-lg font-bold text-white whitespace-nowrap">Agent Scrum</h1>

            {/* Board Tabs */}
            <div className="flex items-center gap-1 ml-4 overflow-x-auto">
              {boards.map((board) => (
                <button
                  key={board.id}
                  onClick={() => setCurrentBoard(board.id)}
                  className={clsx(
                    'group flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm whitespace-nowrap transition-colors',
                    board.id === currentBoardId
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-700'
                  )}
                >
                  {board.name}
                  {boards.length > 1 && (
                    <X
                      className={clsx(
                        'w-3.5 h-3.5 rounded-sm transition-colors',
                        board.id === currentBoardId
                          ? 'hover:bg-blue-500'
                          : 'opacity-0 group-hover:opacity-100 hover:bg-gray-600'
                      )}
                      onClick={(e) => handleDeleteBoard(board.id, e)}
                    />
                  )}
                </button>
              ))}
              <button
                onClick={() => setIsPipelineModalOpen(true)}
                className="flex items-center gap-1 px-2.5 py-1.5 text-sm text-gray-500 hover:text-white hover:bg-gray-700 rounded-lg transition-colors whitespace-nowrap"
                title="New Board"
              >
                <Plus className="w-4 h-4" />
                New Board
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3 relative flex-shrink-0">
            {automationEnabled && (
              <button
                onClick={() => setIsAgentManagerOpen(true)}
                className="flex items-center gap-2 px-3 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
                title="Manage Agents"
              >
                <Users className="w-5 h-5" />
              </button>
            )}

            <button
              onClick={() => setIsSettingsModalOpen(true)}
              className="flex items-center gap-2 px-3 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
              title="Settings"
            >
              <Settings className="w-5 h-5" />
            </button>

            {automationEnabled ? (
              <button
                onClick={() => setIsPRDModalOpen(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
              >
                <Plus className="w-5 h-5" />
                Submit PRD
              </button>
            ) : (
              <button
                onClick={handleAddItem}
                disabled={isAdding}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
              >
                <Plus className="w-5 h-5" />
                {isAdding ? 'Adding...' : `Add ${itemNoun}`}
              </button>
            )}

            {addError && (
              <div className="absolute top-full right-0 mt-2 flex items-center gap-2 px-3 py-2 bg-red-900/90 text-red-200 text-sm rounded-lg whitespace-nowrap">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {addError}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main content with panels */}
      <div className="flex-1 flex min-h-0">
        {/* Main content area - Kanban board */}
        <main className="flex-1 py-4 overflow-x-auto overflow-y-hidden">
          <Outlet />
        </main>

        {/* Right side panels - only show when automation is enabled */}
        {automationEnabled && (
          <div className="w-96 flex-shrink-0 flex flex-col border-l border-gray-700">
            {/* Agent Panel - compact */}
            <div className="flex-shrink-0 border-b border-gray-700">
              <AgentPanel />
            </div>
            {/* Chat Panel - fills remaining space */}
            <div className="flex-1 min-h-0 overflow-hidden">
              <ChatPanel />
            </div>
          </div>
        )}
      </div>

      {/* PRD Modal */}
      <PRDInputModal
        isOpen={isPRDModalOpen}
        onClose={() => setIsPRDModalOpen(false)}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
      />

      {/* Create Board Modal */}
      <PipelineModal
        isOpen={isPipelineModalOpen}
        onClose={() => setIsPipelineModalOpen(false)}
      />

      {/* Story Detail Panel */}
      {selectedStoryId && (
        <StoryDetail
          storyId={selectedStoryId}
          onClose={() => setSelectedStory(null)}
        />
      )}

      {/* Agent Manager Modal */}
      {isAgentManagerOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden border border-gray-700">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
              <h2 className="text-lg font-semibold text-white">Agent Manager</h2>
              <button
                onClick={() => setIsAgentManagerOpen(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="overflow-y-auto max-h-[calc(80vh-60px)]">
              <AgentManager />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
