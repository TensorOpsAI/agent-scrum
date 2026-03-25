import { create } from 'zustand';

interface UIStore {
  isPRDModalOpen: boolean;
  openPRDModal: () => void;
  closePRDModal: () => void;
}

export const useUIStore = create<UIStore>((set) => ({
  isPRDModalOpen: false,
  openPRDModal: () => set({ isPRDModalOpen: true }),
  closePRDModal: () => set({ isPRDModalOpen: false }),
}));
