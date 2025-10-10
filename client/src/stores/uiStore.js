import { defineStore } from 'pinia';

export const useUiStore = defineStore('ui', {
  state: () => ({
    transcriptSidebarOpen: true,
  }),
  actions: {
    toggleTranscriptSidebar() {
      this.transcriptSidebarOpen = !this.transcriptSidebarOpen;
    },
  },
});
