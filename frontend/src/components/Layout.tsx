import { Outlet } from 'react-router-dom';
import { Bot, Plus, Settings, Users, AlertCircle, X, Sparkles, Key, Play, Square, Pause, Loader2 } from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';
import { clsx } from 'clsx';
import { PRDInputModal } from './modals/PRDInputModal';
import { SettingsModal } from './modals/SettingsModal';
import { PipelineModal } from './modals/PipelineModal';
import { WelcomeModal, isOnboardingComplete } from './modals/WelcomeModal';
import { AgentPanel } from './agents/AgentPanel';
import { AgentManager } from './agents/AgentManager';
import { ChatPanel } from './chat/ChatPanel';
import { StoryDetail } from './story/StoryDetail';
import { useStoryStore } from '../store/storyStore';
import { usePipelineStore } from '../store/pipelineStore';
import { storyApi, simulateApi, settingsApi } from '../api/client';

export function Layout() {
  const [isPRDModalOpen, setIsPRDModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [isPipelineModalOpen, setIsPipelineModalOpen] = useState(false);
  const [isAgentManagerOpen, setIsAgentManagerOpen] = useState(false);
  const [isWelcomeOpen, setIsWelcomeOpen] = useState(!isOnboardingComplete());
  const [hasApiKey, setHasApiKey] = useState(!!settingsApi.getLocalApiKey());
  const [swarmStatus, setSwarmStatus] = useState<'running' | 'stopped' | 'paused'>('stopped');
  const [isSwarmLoading, setIsSwarmLoading] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
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

  // Re-check API key when settings modal closes or welcome modal closes
  useEffect(() => {
    if (!isSettingsModalOpen && !isWelcomeOpen) {
      setHasApiKey(!!settingsApi.getLocalApiKey());
    }
  }, [isSettingsModalOpen, isWelcomeOpen]);

  // Fetch swarm status on mount and when board changes
  const fetchSwarmStatus = useCallback(async () => {
    try {
      const res = await settingsApi.getSwarmStatus();
      setSwarmStatus(res.status);
    } catch {
      // ignore – backend may not be ready yet
    }
  }, []);

  useEffect(() => {
    fetchSwarmStatus();
  }, [fetchSwarmStatus, currentBoardId]);

  const handleSwarmAction = useCallback(async (action: 'start' | 'stop' | 'pause' | 'resume') => {
    setIsSwarmLoading(true);
    try {
      let result;
      switch (action) {
        case 'start':  result = await settingsApi.startSwarm(); break;
        case 'stop':   result = await settingsApi.stopSwarm(); break;
        case 'pause':  result = await settingsApi.pauseSwarm(); break;
        case 'resume': result = await settingsApi.resumeSwarm(); break;
      }
      if (result.success) {
        await fetchSwarmStatus();
      }
    } catch (error) {
      console.error(`Failed to ${action} swarm:`, error);
    } finally {
      setIsSwarmLoading(false);
    }
  }, [fetchSwarmStatus]);

  // Auto-clear error after 3 seconds
  useEffect(() => {
    if (addError) {
      const timer = setTimeout(() => setAddError(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [addError]);

  const automationEnabled = currentBoard?.agent_automation === true;
  const itemNoun = currentBoard?.item_noun ?? 'Story';
  const inputNoun = currentBoard?.input_noun ?? 'PRD';
  const isExternalSource = currentBoard?.item_source === 'external';

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

  const handleSimulate = async () => {
    if (!currentBoardId) return;
    setIsSimulating(true);
    setAddError(null);
    try {
      await simulateApi.generate(currentBoardId);
      fetchStories(currentBoardId);
    } catch (error) {
      console.error('Error simulating items:', error);
      setAddError('Failed to simulate items.');
    } finally {
      setIsSimulating(false);
    }
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
            {/* Swarm Controls - visible when automation enabled */}
            {automationEnabled && (
              <div className="flex items-center gap-1.5">
                {swarmStatus === 'stopped' ? (
                  <button
                    onClick={() => handleSwarmAction('start')}
                    disabled={isSwarmLoading}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-green-600 hover:bg-green-700 text-white disabled:opacity-50 transition-colors"
                    title="Start Swarm"
                  >
                    {isSwarmLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                    Start
                  </button>
                ) : (
                  <>
                    <div className={clsx(
                      'px-2 py-1 rounded text-xs font-medium',
                      swarmStatus === 'running' ? 'bg-green-900/40 text-green-400' : 'bg-yellow-900/40 text-yellow-400'
                    )}>
                      {swarmStatus === 'running' ? 'Running' : 'Paused'}
                    </div>
                    {swarmStatus === 'paused' ? (
                      <button
                        onClick={() => handleSwarmAction('resume')}
                        disabled={isSwarmLoading}
                        className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-sm font-medium bg-green-600 hover:bg-green-700 text-white disabled:opacity-50 transition-colors"
                        title="Resume Swarm"
                      >
                        {isSwarmLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                      </button>
                    ) : (
                      <button
                        onClick={() => handleSwarmAction('pause')}
                        disabled={isSwarmLoading}
                        className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-sm font-medium bg-yellow-600 hover:bg-yellow-700 text-white disabled:opacity-50 transition-colors"
                        title="Pause Swarm"
                      >
                        {isSwarmLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Pause className="w-3.5 h-3.5" />}
                      </button>
                    )}
                    <button
                      onClick={() => handleSwarmAction('stop')}
                      disabled={isSwarmLoading}
                      className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-700 text-white disabled:opacity-50 transition-colors"
                      title="Stop Swarm"
                    >
                      <Square className="w-3.5 h-3.5" />
                    </button>
                  </>
                )}
              </div>
            )}

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

            {automationEnabled && (isExternalSource || currentBoard?.template_id === 'publisher') && (
              <button
                onClick={handleSimulate}
                disabled={isSimulating}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
              >
                <Sparkles className="w-5 h-5" />
                {isSimulating ? 'Simulating...' : currentBoard?.template_id === 'publisher' ? `Generate ${itemNoun}s` : `Simulate ${itemNoun}s`}
              </button>
            )}

            {automationEnabled && currentBoard?.template_id !== 'publisher' ? (
              <button
                onClick={() => setIsPRDModalOpen(true)}
                className={clsx(
                  'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
                  isExternalSource
                    ? 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                )}
              >
                <Plus className="w-5 h-5" />
                Submit {inputNoun}
              </button>
            ) : !automationEnabled ? (
              <button
                onClick={handleAddItem}
                disabled={isAdding}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
              >
                <Plus className="w-5 h-5" />
                {isAdding ? 'Adding...' : `Add ${itemNoun}`}
              </button>
            ) : null}

            {addError && (
              <div className="absolute top-full right-0 mt-2 flex items-center gap-2 px-3 py-2 bg-red-900/90 text-red-200 text-sm rounded-lg whitespace-nowrap">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {addError}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* API Key Missing Banner */}
      {!hasApiKey && (
        <div className="flex-shrink-0 bg-amber-900/40 border-b border-amber-700/50 px-6 py-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-amber-200 text-sm">
              <Key className="w-4 h-4 flex-shrink-0" />
              <span>
                <strong>No API key configured.</strong> Agents won't be able to process items without a Gemini API key.
              </span>
            </div>
            <button
              onClick={() => setIsSettingsModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium bg-amber-600 hover:bg-amber-500 text-white rounded-lg transition-colors whitespace-nowrap"
            >
              <Settings className="w-3.5 h-3.5" />
              Open Settings
            </button>
          </div>
        </div>
      )}

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

      {/* Welcome / Onboarding Modal */}
      <WelcomeModal
        isOpen={isWelcomeOpen}
        onClose={() => setIsWelcomeOpen(false)}
        onOpenSettings={() => {
          setIsWelcomeOpen(false);
          setIsSettingsModalOpen(true);
        }}
      />

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
