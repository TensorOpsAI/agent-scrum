import { useState, useEffect } from 'react';
import { cn } from '../../lib/utils';
import { Bot, Loader2, Clock, CheckCircle, Users } from 'lucide-react';
import { useStoryStore } from '../../store/storyStore';
import { usePipelineStore } from '../../store/pipelineStore';
import { getAgentLabel, getAgentColor } from '../../types';
import { AgentInfoModal } from '../modals/AgentInfoModal';
import type { Agent, AgentType } from '../../types';

interface AgentCardProps {
  agent: Agent;
  onClick: () => void;
}

const STATUS_LABEL: Record<Agent['status'], string> = {
  idle: 'inactivo',
  working: 'trabajando',
  waiting: 'esperando',
};

function AgentCard({ agent, onClick }: AgentCardProps) {
  const statusMeta = {
    idle:    { icon: <CheckCircle className="w-3 h-3" />, color: 'text-emerald-400', dot: 'bg-emerald-400' },
    working: { icon: <Loader2 className="w-3 h-3 animate-spin" />, color: 'text-blue-400', dot: 'bg-blue-400 animate-pulse' },
    waiting: { icon: <Clock className="w-3 h-3" />, color: 'text-amber-400', dot: 'bg-amber-400' },
  } as const;

  const meta = statusMeta[agent.status];

  return (
    <button
      onClick={onClick}
      className="group w-full surface p-2 hover:border-border/100 hover:bg-accent/40 transition-colors cursor-pointer text-left"
    >
      <div className="flex items-center gap-2">
        <div className="relative flex-shrink-0">
          <div className={cn(
            'w-7 h-7 rounded-md flex items-center justify-center ring-1 ring-white/5',
            getAgentColor(agent.type)
          )}>
            <Bot className="w-3.5 h-3.5 text-white" />
          </div>
          <span className={cn(
            'absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full ring-2 ring-card',
            meta.dot
          )} />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-medium text-foreground text-[11px] truncate leading-tight">
            {getAgentLabel(agent.type, agent.name)}
          </h3>
          <span className={cn('text-[10px] capitalize', meta.color)}>
            {STATUS_LABEL[agent.status]}
          </span>
        </div>
      </div>
    </button>
  );
}

export function AgentPanel() {
  const { agents, fetchAgents } = useStoryStore();
  const { currentBoardId } = usePipelineStore();
  const [selectedAgent, setSelectedAgent] = useState<AgentType | null>(null);

  useEffect(() => {
    fetchAgents(currentBoardId ?? undefined);
  }, [fetchAgents, currentBoardId]);

  return (
    <>
      <div className="bg-card/30 px-3 py-3 overflow-y-auto">
        <div className="flex items-center gap-2 mb-2.5">
          <Users className="w-3.5 h-3.5 text-muted-foreground" />
          <h2 className="font-medium text-foreground text-xs uppercase tracking-[0.08em]">
            Agentes
          </h2>
          <span className="text-[10px] text-muted-foreground tabular-nums ml-auto">
            {agents.length}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-1.5">
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
