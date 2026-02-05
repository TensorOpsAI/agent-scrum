import { useEffect, useRef, useCallback, useState } from 'react';
import { useStoryStore } from '../store/storyStore';
import type { Story, Task, AgentType } from '../types';

interface WebSocketMessage {
  event: string;
  data: unknown;
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const { addStory, updateStory, addTask, updateTask, updateAgentStatus, fetchStories } =
    useStoryStore();

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      // Clear any pending reconnect
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        handleMessage(message);
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected, reconnecting...');
      // Reconnect after 3 seconds
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }, []);

  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      // Store the last message for components that want to react to all events
      setLastMessage(message);

      switch (message.event) {
        case 'story:created':
          addStory(message.data as Story);
          break;

        case 'story:updated':
          updateStory(message.data as Story);
          break;

        case 'story:deleted':
          // Refetch stories to ensure consistency
          fetchStories();
          break;

        case 'task:created':
          addTask(message.data as Task);
          break;

        case 'task:updated':
          updateTask(message.data as Task);
          break;

        case 'task:deleted':
          // Refetch to ensure consistency
          fetchStories();
          break;

        case 'agent:status_changed': {
          const { agent_type, status, current_task } = message.data as {
            agent_type: AgentType;
            status: 'idle' | 'working' | 'waiting';
            current_task: string | null;
          };
          updateAgentStatus(agent_type, status, current_task);
          break;
        }

        case 'agent:activity':
          // Could be used to show activity notifications
          console.log('Agent activity:', message.data);
          break;

        default:
          console.log('Unknown WebSocket event:', message.event);
      }
    },
    [addStory, updateStory, addTask, updateTask, updateAgentStatus, fetchStories]
  );

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const send = useCallback((event: string, data: unknown) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ event, data }));
    }
  }, []);

  return { send, lastMessage };
}
