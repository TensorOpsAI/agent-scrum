import { X, Bot, Cpu, Wrench, MessageSquare } from 'lucide-react';
import { clsx } from 'clsx';
import { getAgentLabel, getAgentColor } from '../../types';
import type { AgentType, BuiltinAgentType } from '../../types';
import { useStoryStore } from '../../store/storyStore';

interface AgentInfoModalProps {
  isOpen: boolean;
  onClose: () => void;
  agentType: AgentType | null;
}

interface AgentConfigItem {
  conversationModel: string;
  workModel: string;
  tools: string[];
  description: string;
}

// Agent configuration - models and tools for each built-in agent
const AGENT_CONFIG: Record<BuiltinAgentType, AgentConfigItem> = {
  product_owner: {
    conversationModel: 'Gemini 2.0 Flash',
    workModel: 'Claude Opus 4.5',
    tools: ['PRD Parser', 'Story Generator', 'Priority Analyzer', 'Acceptance Criteria Writer'],
    description: 'Analyzes PRDs and creates well-structured user stories with clear acceptance criteria.',
  },
  tech_lead: {
    conversationModel: 'Gemini 2.0 Flash',
    workModel: 'Claude Sonnet 4',
    tools: ['Task Reviewer', 'Architecture Analyzer', 'Dependency Checker', 'Technical Debt Scanner'],
    description: 'Reviews task breakdowns for technical feasibility and ensures alignment with best practices.',
  },
  developer: {
    conversationModel: 'Gemini 2.0 Flash',
    workModel: 'Claude Opus 4.5',
    tools: ['Story Breakdown', 'Code Generator', 'Implementation Planner', 'API Designer'],
    description: 'Breaks down stories into tasks and creates detailed implementation notes.',
  },
  code_reviewer: {
    conversationModel: 'Gemini 2.0 Flash',
    workModel: 'Gemini 2.5 Pro',
    tools: ['Code Analyzer', 'Security Scanner', 'Style Checker', 'Performance Profiler'],
    description: 'Reviews implementation for code quality, security issues, and best practices.',
  },
  qa: {
    conversationModel: 'Gemini 2.0 Flash',
    workModel: 'Claude Sonnet 4',
    tools: ['Test Scenario Generator', 'Test Runner', 'Bug Reporter', 'Coverage Analyzer'],
    description: 'Creates test scenarios and validates that implementations meet acceptance criteria.',
  },
  client: {
    conversationModel: 'N/A',
    workModel: 'N/A',
    tools: ['Chat Interface', 'Feedback Provider'],
    description: 'Human user proxy for A2A communication and feedback.',
  },
};

function isBuiltinAgent(type: AgentType): type is BuiltinAgentType {
  return type in AGENT_CONFIG;
}

export function AgentInfoModal({ isOpen, onClose, agentType }: AgentInfoModalProps) {
  const { agents } = useStoryStore();

  if (!isOpen || !agentType) return null;

  // Find the agent in the store for additional info
  const agentInfo = agents.find(a => a.type === agentType || a.id === agentType);

  // Get config - use builtin config or create dynamic config
  const config: AgentConfigItem = isBuiltinAgent(agentType)
    ? AGENT_CONFIG[agentType]
    : {
        conversationModel: 'Gemini 2.0 Flash',
        workModel: 'Claude Sonnet 4',
        tools: ['Dynamic Agent Tools'],
        description: agentInfo?.description || `Dynamic agent: ${agentType}`,
      };

  const agentName = getAgentLabel(agentType, agentInfo?.name);
  const agentColor = getAgentColor(agentType);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-gray-800 rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className={clsx(
              'w-10 h-10 rounded-full flex items-center justify-center',
              agentColor
            )}>
              <Bot className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-lg font-semibold text-white">{agentName}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          {/* Description */}
          <p className="text-gray-300 text-sm">{config.description}</p>

          {/* Models Section */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-gray-400 flex items-center gap-2">
              <Cpu className="w-4 h-4" />
              Models
            </h3>
            <div className="bg-gray-900 rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-blue-400" />
                  <span className="text-gray-300 text-sm">Conversation</span>
                </div>
                <span className="text-sm font-medium text-white bg-gray-700 px-2 py-1 rounded">
                  {config.conversationModel}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Wrench className="w-4 h-4 text-green-400" />
                  <span className="text-gray-300 text-sm">Work/Analysis</span>
                </div>
                <span className="text-sm font-medium text-white bg-gray-700 px-2 py-1 rounded">
                  {config.workModel}
                </span>
              </div>
            </div>
          </div>

          {/* Tools Section */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-gray-400 flex items-center gap-2">
              <Wrench className="w-4 h-4" />
              Tools
            </h3>
            <div className="flex flex-wrap gap-2">
              {config.tools.map((tool) => (
                <span
                  key={tool}
                  className={clsx(
                    'text-xs px-3 py-1.5 rounded-full font-medium',
                    'bg-gray-700 text-gray-200 border border-gray-600'
                  )}
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-700 bg-gray-850">
          <p className="text-xs text-gray-500 text-center">
            This is a demo agent. In production, these would be real AI models performing actual work.
          </p>
        </div>
      </div>
    </div>
  );
}
