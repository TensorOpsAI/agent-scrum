import { create } from 'zustand';

interface UIStore {
  isPRDModalOpen: boolean;
  openPRDModal: () => void;
  closePRDModal: () => void;
  // Callback for "Generate" action on publisher boards — set by Layout
  onGenerate: (() => void) | null;
  setOnGenerate: (fn: (() => void) | null) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  isPRDModalOpen: false,
  openPRDModal: () => set({ isPRDModalOpen: true }),
  closePRDModal: () => set({ isPRDModalOpen: false }),
  onGenerate: null,
  setOnGenerate: (fn) => set({ onGenerate: fn }),
}));
