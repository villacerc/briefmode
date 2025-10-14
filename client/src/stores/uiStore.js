import { defineStore } from 'pinia';

export const useUiStore = defineStore('ui', {
  state: () => ({
    transcriptSidebarOpen: true,
    dictionarySidebarOpen: true,
  }),
  actions: {
    toggleTranscriptSidebar() {
      this.transcriptSidebarOpen = !this.transcriptSidebarOpen;
    },
    toggleDictionarySidebar() {
      this.dictionarySidebarOpen = !this.dictionarySidebarOpen;
    },
  },
});