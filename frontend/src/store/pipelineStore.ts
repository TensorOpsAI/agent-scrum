import { create } from 'zustand';
import type { PipelineConfig, PipelineTemplate } from '../types';
import { pipelineApi, boardApi } from '../api/client';

const CURRENT_BOARD_KEY = 'board_current_id';

function getSavedBoardId(): number | null {
  try {
    const raw = localStorage.getItem(CURRENT_BOARD_KEY);
    return raw ? Number(raw) : null;
  } catch {
    return null;
  }
}

function saveBoardId(id: number) {
  localStorage.setItem(CURRENT_BOARD_KEY, String(id));
}

interface BoardState {
  boards: PipelineConfig[];
  currentBoardId: number | null;
  templates: PipelineTemplate[];
  isLoading: boolean;

  // Derived
  currentBoard: PipelineConfig | null;

  // Keep old alias for backward compat during migration
  activeConfig: PipelineConfig | null;

  fetchBoards: () => Promise<void>;
  fetchTemplates: () => Promise<void>;
  createBoard: (templateId: string, name?: string) => Promise<PipelineConfig>;
  deleteBoard: (id: number) => Promise<void>;
  setCurrentBoard: (id: number) => void;
  addBoard: (board: PipelineConfig) => void;
  removeBoard: (id: number) => void;
}

function deriveCurrentBoard(boards: PipelineConfig[], currentBoardId: number | null): PipelineConfig | null {
  if (currentBoardId == null) return boards[0] ?? null;
  return boards.find((b) => b.id === currentBoardId) ?? boards[0] ?? null;
}

export const usePipelineStore = create<BoardState>((set, get) => ({
  boards: [],
  currentBoardId: getSavedBoardId(),
  templates: [],
  isLoading: false,
  currentBoard: null,
  activeConfig: null,

  fetchBoards: async () => {
    try {
      const boards = await boardApi.list();
      const currentBoardId = get().currentBoardId;
      const current = deriveCurrentBoard(boards, currentBoardId);
      // If saved ID not found in boards, default to first
      const resolvedId = current?.id ?? null;
      if (resolvedId && resolvedId !== currentBoardId) {
        saveBoardId(resolvedId);
      }
      set({
        boards,
        currentBoardId: resolvedId,
        currentBoard: current,
        activeConfig: current,
      });
    } catch (error) {
      console.error('Error fetching boards:', error);
    }
  },

  fetchTemplates: async () => {
    try {
      const templates = await pipelineApi.getTemplates();
      set({ templates });
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  },

  createBoard: async (templateId: string, name?: string) => {
    set({ isLoading: true });
    try {
      const board = await boardApi.create(templateId, name);
      // Re-fetch boards from server to avoid duplicates with WebSocket echo
      const boards = await boardApi.list();
      saveBoardId(board.id);
      const current = deriveCurrentBoard(boards, board.id);
      set({
        boards,
        currentBoardId: board.id,
        currentBoard: current,
        activeConfig: current,
        isLoading: false,
      });
      return board;
    } catch (error) {
      console.error('Error creating board:', error);
      set({ isLoading: false });
      throw error;
    }
  },

  deleteBoard: async (id: number) => {
    try {
      await boardApi.delete(id);
      const boards = get().boards.filter((b) => b.id !== id);
      let currentBoardId = get().currentBoardId;
      if (currentBoardId === id) {
        currentBoardId = boards[0]?.id ?? null;
        if (currentBoardId) saveBoardId(currentBoardId);
      }
      const current = deriveCurrentBoard(boards, currentBoardId);
      set({
        boards,
        currentBoardId: current?.id ?? null,
        currentBoard: current,
        activeConfig: current,
      });
    } catch (error) {
      console.error('Error deleting board:', error);
    }
  },

  setCurrentBoard: (id: number) => {
    saveBoardId(id);
    const current = deriveCurrentBoard(get().boards, id);
    set({
      currentBoardId: id,
      currentBoard: current,
      activeConfig: current,
    });
  },

  addBoard: (board: PipelineConfig) => {
    // Deduplicate - createBoard already adds it, WebSocket may echo it
    if (get().boards.some((b) => b.id === board.id)) return;
    const boards = [...get().boards, board];
    set({ boards });
  },

  removeBoard: (id: number) => {
    const boards = get().boards.filter((b) => b.id !== id);
    let currentBoardId = get().currentBoardId;
    if (currentBoardId === id) {
      currentBoardId = boards[0]?.id ?? null;
      if (currentBoardId) saveBoardId(currentBoardId);
    }
    const current = deriveCurrentBoard(boards, currentBoardId);
    set({
      boards,
      currentBoardId: current?.id ?? null,
      currentBoard: current,
      activeConfig: current,
    });
  },
}));
