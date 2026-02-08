import { useEffect, useRef, useCallback, useState } from 'react';
import { useStoryStore } from '../store/storyStore';
import { usePipelineStore } from '../store/pipelineStore';
import { getSessionId } from '../api/client';
import type { Story, Task, AgentType, PipelineConfig } from '../types';

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
  const { addBoard, removeBoard, fetchBoards } = usePipelineStore();

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws?session_id=${getSessionId()}`;

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

      const currentBoardId = usePipelineStore.getState().currentBoardId;

      switch (message.event) {
        case 'story:created': {
          const story = message.data as Story;
          // Only add if it belongs to the current board
          if (story.board_id === currentBoardId) {
            addStory(story);
          }
          break;
        }

        case 'story:updated': {
          const story = message.data as Story;
          if (story.board_id === currentBoardId) {
            updateStory(story);
          }
          break;
        }

        case 'story:deleted':
          // Refetch stories to ensure consistency
          if (currentBoardId) {
            fetchStories(currentBoardId);
          }
          break;

        case 'task:created':
          addTask(message.data as Task);
          break;

        case 'task:updated':
          updateTask(message.data as Task);
          break;

        case 'task:deleted':
          // Refetch to ensure consistency
          if (currentBoardId) {
            fetchStories(currentBoardId);
          }
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

        case 'board:created': {
          const board = message.data as PipelineConfig;
          addBoard(board);
          break;
        }

        case 'board:deleted': {
          const { id } = message.data as { id: number };
          removeBoard(id);
          break;
        }

        default:
          console.log('Unknown WebSocket event:', message.event);
      }
    },
    [addStory, updateStory, addTask, updateTask, updateAgentStatus, fetchStories, addBoard, removeBoard, fetchBoards]
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
