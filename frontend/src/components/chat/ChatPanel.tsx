import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { MessageSquare, Bot, ArrowRight, Send, User } from 'lucide-react';
import { clsx } from 'clsx';
import { chatApi, type ChatMessage } from '../../api/client';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useStoryStore } from '../../store/storyStore';

const BUILTIN_AGENT_COLORS: Record<string, string> = {
  product_owner: 'text-purple-400',
  tech_lead: 'text-blue-400',
  developer: 'text-green-400',
  code_reviewer: 'text-yellow-400',
  qa: 'text-pink-400',
  client: 'text-cyan-400',
};

const BUILTIN_AGENT_BG_COLORS: Record<string, string> = {
  product_owner: 'bg-purple-500/20',
  tech_lead: 'bg-blue-500/20',
  developer: 'bg-green-500/20',
  code_reviewer: 'bg-yellow-500/20',
  qa: 'bg-pink-500/20',
  client: 'bg-cyan-500/20',
};

function getAgentTextColor(agentId: string): string {
  return BUILTIN_AGENT_COLORS[agentId] || 'text-gray-400';
}

function getAgentBgColor(agentId: string): string {
  return BUILTIN_AGENT_BG_COLORS[agentId] || 'bg-gray-600';
}

interface ChatMessageItemProps {
  message: ChatMessage;
}

function ChatMessageItem({ message }: ChatMessageItemProps) {
  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const isHuman = message.from_agent === 'client';

  return (
    <div className="px-4 py-3 hover:bg-gray-800/50 transition-colors">
      <div className="flex items-start gap-3">
        <div className={clsx(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          getAgentBgColor(message.from_agent)
        )}>
          {isHuman ? (
            <User className={clsx('w-4 h-4', getAgentTextColor(message.from_agent))} />
          ) : (
            <Bot className={clsx('w-4 h-4', getAgentTextColor(message.from_agent))} />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={clsx('font-medium text-sm', getAgentTextColor(message.from_agent))}>
              {message.from_agent_name}
            </span>
            {message.to_agent && (
              <>
                <ArrowRight className="w-3 h-3 text-gray-500" />
                <span className={clsx('text-sm', getAgentTextColor(message.to_agent))}>
                  @{message.to_agent_name}
                </span>
              </>
            )}
            <span className="text-xs text-gray-500">
              {formatTime(message.created_at)}
            </span>
          </div>
          <p className="text-gray-300 text-sm whitespace-pre-wrap break-words">
            {message.content}
          </p>
          {(message.story_id || message.task_id) && (
            <div className="mt-1 flex gap-2">
              {message.story_id && (
                <span className="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded">
                  STORY-{message.story_id}
                </span>
              )}
              {message.task_id && (
                <span className="text-xs px-2 py-0.5 bg-green-500/20 text-green-400 rounded">
                  TASK-{message.task_id}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [inputValue, setInputValue] = useState('');
  const [targetAgent, setTargetAgent] = useState<string>('');
  const [isSending, setIsSending] = useState(false);
  const [showAgentSelector, setShowAgentSelector] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { lastMessage } = useWebSocket();
  const storeAgents = useStoryStore((s) => s.agents);

  // Derive available agents from the store (board-specific)
  const availableAgents = useMemo(
    () => storeAgents.map((a) => ({ id: a.id, name: a.name })),
    [storeAgents]
  );

  // Load initial messages
  useEffect(() => {
    const loadMessages = async () => {
      try {
        const data = await chatApi.getMessages(100);
        setMessages(data);
      } catch (error) {
        console.error('Failed to load chat messages:', error);
      } finally {
        setIsLoading(false);
      }
    };
    loadMessages();
  }, []);

  // Handle real-time messages via WebSocket
  useEffect(() => {
    if (lastMessage?.event === 'agent:chat') {
      setMessages(prev => [...prev, lastMessage.data as ChatMessage]);
    }
  }, [lastMessage]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || isSending) return;

    setIsSending(true);
    try {
      await chatApi.sendMessage({
        content: inputValue.trim(),
        to_agent: targetAgent || undefined,
      });
      setInputValue('');
      setTargetAgent('');
      setShowAgentSelector(false);
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsSending(false);
    }
  }, [inputValue, targetAgent, isSending]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInputValue(value);

    // Only show agent selector when:
    // 1. Input starts with @ AND
    // 2. No agent has been selected yet AND
    // 3. The @ is the only content or followed by partial typing (no space yet)
    const isTypingMention = value.startsWith('@') && !targetAgent && !value.includes(' ');

    if (isTypingMention) {
      setShowAgentSelector(true);
    } else {
      setShowAgentSelector(false);
    }
  }, [targetAgent]);

  const selectAgent = useCallback((agentId: string) => {
    setTargetAgent(agentId);
    const agentName = availableAgents.find(a => a.id === agentId)?.name || agentId;
    // Remove the @ prefix if present and add the agent mention
    const newValue = inputValue.startsWith('@')
      ? inputValue.replace(/^@\S*\s*/, `@${agentName} `)
      : `@${agentName} ${inputValue}`;
    setInputValue(newValue);
    setShowAgentSelector(false);
    inputRef.current?.focus();
  }, [inputValue]);

  return (
    <div className="flex flex-col h-full bg-gray-850">
      {/* Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-gray-700 flex items-center gap-2">
        <MessageSquare className="w-5 h-5 text-blue-500" />
        <h2 className="font-semibold text-white">Agent Chat</h2>
        <span className="text-xs text-gray-500 ml-auto">
          {messages.length} messages
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-gray-500">
            <MessageSquare className="w-8 h-8 mb-2 opacity-50" />
            <p className="text-sm">No messages yet</p>
            <p className="text-xs">Submit a PRD to see agents collaborate</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-700/50">
            {messages.map((message) => (
              <ChatMessageItem key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 border-t border-gray-700 p-3">
        {/* Agent Selector Popup */}
        {showAgentSelector && (
          <div className="mb-2 bg-gray-800 rounded-lg border border-gray-600 overflow-hidden">
            <div className="px-3 py-1.5 text-xs text-gray-400 border-b border-gray-700">
              Select an agent to message
            </div>
            {availableAgents.map((agent) => (
              <button
                key={agent.id}
                onClick={() => selectAgent(agent.id)}
                className={clsx(
                  'w-full px-3 py-2 text-left text-sm flex items-center gap-2 hover:bg-gray-700 transition-colors',
                  getAgentTextColor(agent.id)
                )}
              >
                <Bot className="w-4 h-4" />
                {agent.name}
              </button>
            ))}
          </div>
        )}

        {/* Selected Agent Badge */}
        {targetAgent && !showAgentSelector && (
          <div className="mb-2 flex items-center gap-2">
            <span className="text-xs text-gray-400">Sending to:</span>
            <span className={clsx(
              'px-2 py-0.5 rounded text-xs font-medium',
              getAgentBgColor(targetAgent),
              getAgentTextColor(targetAgent)
            )}>
              {availableAgents.find(a => a.id === targetAgent)?.name || targetAgent}
            </span>
            <button
              onClick={() => setTargetAgent('')}
              className="text-gray-500 hover:text-gray-300 text-xs"
            >
              ✕
            </button>
          </div>
        )}

        {/* Input Box */}
        <div className="flex items-center gap-2">
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Type a message... (use @ to mention an agent)"
              disabled={isSending}
              className={clsx(
                'w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg',
                'text-sm text-white placeholder-gray-500',
                'focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isSending}
            className={clsx(
              'p-2 rounded-lg transition-colors',
              'bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700',
              'text-white disabled:text-gray-500',
              'disabled:cursor-not-allowed'
            )}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="mt-1 text-xs text-gray-500">
          Press Enter to send • Type @ to select an agent
        </p>
      </div>
    </div>
  );
}
