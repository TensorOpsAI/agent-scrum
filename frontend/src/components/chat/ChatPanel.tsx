import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { MessageSquare, Bot, ArrowRight, Send, User, Filter, X as XIcon } from 'lucide-react';
import { cn } from '../../lib/utils';
import { chatApi, type ChatMessage } from '../../api/client';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useStoryStore } from '../../store/storyStore';
import { eventBus } from '../../lib/eventBus';

const BUILTIN_AGENT_COLORS: Record<string, string> = {
  product_owner: 'text-purple-400',
  tech_lead:     'text-blue-400',
  developer:     'text-emerald-400',
  code_reviewer: 'text-amber-400',
  qa:            'text-pink-400',
  client:        'text-cyan-400',
};

const BUILTIN_AGENT_BG_COLORS: Record<string, string> = {
  product_owner: 'bg-purple-500/15 ring-purple-500/30',
  tech_lead:     'bg-blue-500/15 ring-blue-500/30',
  developer:     'bg-emerald-500/15 ring-emerald-500/30',
  code_reviewer: 'bg-amber-500/15 ring-amber-500/30',
  qa:            'bg-pink-500/15 ring-pink-500/30',
  client:        'bg-cyan-500/15 ring-cyan-500/30',
};

const getAgentTextColor = (id: string) => BUILTIN_AGENT_COLORS[id] || 'text-muted-foreground';
const getAgentBgColor = (id: string) => BUILTIN_AGENT_BG_COLORS[id] || 'bg-secondary ring-border';

interface ChatMessageItemProps {
  message: ChatMessage;
}

function ChatMessageItem({ message }: ChatMessageItemProps) {
  const formatTime = (dateStr: string) =>
    new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const isHuman = message.from_agent === 'client';

  return (
    <div className="px-4 py-2.5 hover:bg-accent/30 transition-colors group">
      <div className="flex items-start gap-2.5">
        <div className={cn(
          'w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0 ring-1',
          getAgentBgColor(message.from_agent)
        )}>
          {isHuman ? (
            <User className={cn('w-3.5 h-3.5', getAgentTextColor(message.from_agent))} />
          ) : (
            <Bot className={cn('w-3.5 h-3.5', getAgentTextColor(message.from_agent))} />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className={cn('font-medium text-xs', getAgentTextColor(message.from_agent))}>
              {message.from_agent_name}
            </span>
            {message.to_agent && (
              <>
                <ArrowRight className="w-2.5 h-2.5 text-muted-foreground/60" />
                <span className={cn('text-xs', getAgentTextColor(message.to_agent))}>
                  @{message.to_agent_name}
                </span>
              </>
            )}
            <span className="text-[10px] text-muted-foreground/60 ml-1 tabular-nums">
              {formatTime(message.created_at)}
            </span>
          </div>
          <p className="text-foreground/90 text-[13px] leading-relaxed whitespace-pre-wrap break-words">
            {message.content}
          </p>
          {(message.story_id || message.task_id) && (
            <div className="mt-1.5 flex gap-1.5">
              {message.story_id && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 bg-blue-500/10 border border-blue-500/20 text-blue-300 rounded">
                  STORY-{message.story_id}
                </span>
              )}
              {message.task_id && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded">
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
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { lastMessage } = useWebSocket();
  const storeAgents = useStoryStore((s) => s.agents);
  const selectedStoryId = useStoryStore((s) => s.selectedStoryId);
  const setSelectedStory = useStoryStore((s) => s.setSelectedStory);
  const [filterByStory, setFilterByStory] = useState(true);

  const availableAgents = useMemo(
    () => storeAgents.map((a) => ({ id: a.id, name: a.name })),
    [storeAgents]
  );

  // When story selection changes, reset the filter to "on" by default
  useEffect(() => {
    if (selectedStoryId) setFilterByStory(true);
  }, [selectedStoryId]);

  const visibleMessages = useMemo(() => {
    if (selectedStoryId && filterByStory) {
      return messages.filter((m) => m.story_id === selectedStoryId);
    }
    return messages;
  }, [messages, selectedStoryId, filterByStory]);

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

  useEffect(() => {
    if (lastMessage?.event === 'agent:chat') {
      setMessages(prev => [...prev, lastMessage.data as ChatMessage]);
    }
  }, [lastMessage]);

  // Demo replay messages (and clear-on-replay-skip)
  useEffect(() => {
    const offChat = eventBus.on('replay:chat', (msg) => {
      setMessages((prev) => [...prev, msg]);
    });
    const offState = eventBus.on('replay:state', ({ isReplaying }) => {
      if (!isReplaying) {
        // When replay finishes/is skipped, drop synthetic (negative-id) messages
        setMessages((prev) => prev.filter((m) => m.id > 0));
      }
    });
    return () => { offChat(); offState(); };
  }, []);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;
    const { scrollTop, scrollHeight, clientHeight } = container;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 120;
    if (isNearBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
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
    const isTypingMention = value.startsWith('@') && !targetAgent && !value.includes(' ');
    setShowAgentSelector(isTypingMention);
  }, [targetAgent]);

  const selectAgent = useCallback((agentId: string) => {
    setTargetAgent(agentId);
    const agentName = availableAgents.find(a => a.id === agentId)?.name || agentId;
    const newValue = inputValue.startsWith('@')
      ? inputValue.replace(/^@\S*\s*/, `@${agentName} `)
      : `@${agentName} ${inputValue}`;
    setInputValue(newValue);
    setShowAgentSelector(false);
    inputRef.current?.focus();
  }, [inputValue, availableAgents]);

  return (
    <div className="flex flex-col h-full bg-card/20">
      {/* Header */}
      <div className="flex-shrink-0 px-4 h-11 border-b border-border flex items-center gap-2">
        <MessageSquare className="w-3.5 h-3.5 text-muted-foreground" />
        <h2 className="font-medium text-foreground text-xs uppercase tracking-[0.08em]">
          Chat
        </h2>
        <span className="text-[10px] text-muted-foreground ml-auto tabular-nums">
          {visibleMessages.length}{visibleMessages.length !== messages.length && `/${messages.length}`}
        </span>
      </div>

      {/* Story-scoped filter banner */}
      {selectedStoryId && (
        <div className="flex-shrink-0 px-3 py-1.5 bg-primary/8 border-b border-primary/20 flex items-center gap-2 animate-fade-in">
          <Filter className="w-3 h-3 text-primary flex-shrink-0" />
          <span className="text-[11px] text-foreground/90 flex-1 truncate">
            {filterByStory ? (
              <>Filtered to <span className="font-mono text-primary">STORY-{selectedStoryId}</span></>
            ) : (
              <>Showing all messages</>
            )}
          </span>
          <button
            onClick={() => setFilterByStory((v) => !v)}
            className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
          >
            {filterByStory ? 'show all' : 'filter'}
          </button>
          <button
            onClick={() => setSelectedStory(null)}
            className="text-muted-foreground hover:text-foreground transition-colors"
            title="Deselect story"
          >
            <XIcon className="w-3 h-3" />
          </button>
        </div>
      )}

      {/* Messages */}
      <div ref={messagesContainerRef} className="flex-1 min-h-0 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-border border-t-primary" />
          </div>
        ) : visibleMessages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-muted-foreground/60 px-6 text-center">
            <MessageSquare className="w-7 h-7 mb-2 opacity-50" />
            <p className="text-xs font-medium text-muted-foreground">
              {selectedStoryId && filterByStory ? 'No messages for this story yet' : 'No messages yet'}
            </p>
            <p className="text-[11px] mt-0.5">
              {selectedStoryId && filterByStory
                ? 'Agents will post here as they work on it'
                : 'Submit a PRD to see agents collaborate'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-border/40">
            {visibleMessages.map((message) => (
              <ChatMessageItem key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="flex-shrink-0 border-t border-border p-3 bg-card/30">
        {showAgentSelector && (
          <div className="mb-2 surface overflow-hidden animate-fade-in">
            <div className="px-3 py-1.5 text-[10px] uppercase tracking-wider text-muted-foreground border-b border-border">
              Select agent
            </div>
            {availableAgents.map((agent) => (
              <button
                key={agent.id}
                onClick={() => selectAgent(agent.id)}
                className={cn(
                  'w-full px-3 py-1.5 text-left text-xs flex items-center gap-2 hover:bg-accent transition-colors',
                  getAgentTextColor(agent.id)
                )}
              >
                <Bot className="w-3.5 h-3.5" />
                {agent.name}
              </button>
            ))}
          </div>
        )}

        {targetAgent && !showAgentSelector && (
          <div className="mb-2 flex items-center gap-2 animate-fade-in">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">To</span>
            <span className={cn(
              'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-medium ring-1',
              getAgentBgColor(targetAgent),
              getAgentTextColor(targetAgent)
            )}>
              <Bot className="w-3 h-3" />
              {availableAgents.find(a => a.id === targetAgent)?.name || targetAgent}
            </span>
            <button
              onClick={() => setTargetAgent('')}
              className="text-muted-foreground hover:text-foreground text-xs ml-auto"
            >
              ✕
            </button>
          </div>
        )}

        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Type a message…  use @ to mention"
            disabled={isSending}
            className={cn(
              'flex-1 h-9 px-3 bg-input border border-border rounded-md',
              'text-sm text-foreground placeholder-muted-foreground/60',
              'focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent',
              'disabled:opacity-50 transition-all'
            )}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isSending}
            className={cn(
              'h-9 w-9 inline-flex items-center justify-center rounded-md transition-all',
              'bg-primary hover:bg-primary/90 text-primary-foreground',
              'disabled:bg-secondary disabled:text-muted-foreground/50 disabled:cursor-not-allowed'
            )}
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
        <p className="mt-1.5 text-[10px] text-muted-foreground/60">
          Enter to send · @ to mention an agent
        </p>
      </div>
    </div>
  );
}
