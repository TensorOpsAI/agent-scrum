import { Outlet } from 'react-router-dom';
import { Bot, Plus, Settings, Users } from 'lucide-react';
import { useState } from 'react';
import { PRDInputModal } from './modals/PRDInputModal';
import { SettingsModal } from './modals/SettingsModal';
import { AgentPanel } from './agents/AgentPanel';
import { AgentManager } from './agents/AgentManager';
import { ChatPanel } from './chat/ChatPanel';
import { StoryDetail } from './story/StoryDetail';
import { useStoryStore } from '../store/storyStore';

export function Layout() {
  const [isPRDModalOpen, setIsPRDModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [isAgentManagerOpen, setIsAgentManagerOpen] = useState(false);
  const { selectedStoryId, setSelectedStory } = useStoryStore();

  return (
    <div className="h-screen bg-gray-900 flex flex-col overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Bot className="w-8 h-8 text-blue-500" />
            <div>
              <h1 className="text-xl font-bold text-white">Agent Scrum</h1>
              <p className="text-xs text-gray-400">
                AI Multi-Agent Demo - Multi-agent collaboration
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsAgentManagerOpen(true)}
              className="flex items-center gap-2 px-3 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
              title="Manage Agents"
            >
              <Users className="w-5 h-5" />
            </button>

            <button
              onClick={() => setIsSettingsModalOpen(true)}
              className="flex items-center gap-2 px-3 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
              title="Settings"
            >
              <Settings className="w-5 h-5" />
            </button>

            <button
              onClick={() => setIsPRDModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
            >
              <Plus className="w-5 h-5" />
              Submit PRD
            </button>
          </div>
        </div>
      </header>

      {/* Main content with panels */}
      <div className="flex-1 flex min-h-0">
        {/* Main content area - Kanban board */}
        <main className="flex-1 py-4 overflow-x-auto overflow-y-hidden">
          <Outlet />
        </main>

        {/* Right side panels */}
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
                ✕
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
