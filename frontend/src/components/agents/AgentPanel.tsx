import { useState, useEffect } from 'react';
import { clsx } from 'clsx';
import { Bot, Loader2, Clock, CheckCircle } from 'lucide-react';
import { useStoryStore } from '../../store/storyStore';
import { getAgentLabel, getAgentColor } from '../../types';
import { AgentInfoModal } from '../modals/AgentInfoModal';
import type { Agent, AgentType } from '../../types';

interface AgentCardProps {
  agent: Agent;
  onClick: () => void;
}

function AgentCard({ agent, onClick }: AgentCardProps) {
  const statusIcon = {
    idle: <CheckCircle className="w-3 h-3 text-green-500" />,
    working: <Loader2 className="w-3 h-3 text-blue-500 animate-spin" />,
    waiting: <Clock className="w-3 h-3 text-yellow-500" />,
  };

  return (
    <button
      onClick={onClick}
      className="w-full bg-gray-800 rounded-lg p-2 hover:bg-gray-750 hover:ring-1 hover:ring-gray-600 transition-all cursor-pointer text-left"
    >
      <div className="flex items-center gap-2">
        <div className={clsx(
          'w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0',
          getAgentColor(agent.type)
        )}>
          <Bot className="w-4 h-4 text-white" />
        </div>
        <div className="min-w-0">
          <h3 className="font-medium text-white text-xs truncate">{getAgentLabel(agent.type, agent.name)}</h3>
          <div className="flex items-center gap-1">
            {statusIcon[agent.status]}
            <span className={clsx(
              'text-xs',
              agent.status === 'idle' && 'text-green-400',
              agent.status === 'working' && 'text-blue-400',
              agent.status === 'waiting' && 'text-yellow-400'
            )}>
              {agent.status}
            </span>
          </div>
        </div>
      </div>
    </button>
  );
}

export function AgentPanel() {
  const { agents, fetchAgents } = useStoryStore();
  const [selectedAgent, setSelectedAgent] = useState<AgentType | null>(null);

  // Fetch agents on mount
  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  return (
    <>
      <div className="h-full bg-gray-850 p-3 overflow-y-auto">
        <div className="flex items-center gap-2 mb-3">
          <Bot className="w-4 h-4 text-blue-500" />
          <h2 className="font-semibold text-white text-sm">Agents</h2>
        </div>

        <div className="grid grid-cols-2 gap-2">
          {agents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onClick={() => setSelectedAgent(agent.type)}
            />
          ))}
        </div>
      </div>

      <AgentInfoModal
        isOpen={selectedAgent !== null}
        onClose={() => setSelectedAgent(null)}
        agentType={selectedAgent}
      />
    </>
  );
}
