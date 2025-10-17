import { defineStore } from 'pinia';

export const useUiStore = defineStore('ui', {
  state: () => ({
    transcriptSidebarOpen: true,
    dictionarySidebarOpen: true,
    moreMenuOpen: false,
  }),
  actions: {
    toggleTranscriptSidebar() {
      this.transcriptSidebarOpen = !this.transcriptSidebarOpen;
    },
    toggleDictionarySidebar() {
      this.dictionarySidebarOpen = !this.dictionarySidebarOpen;
    },
    toggleMoreMenu() {
      this.moreMenuOpen = !this.moreMenuOpen;
    },
  },
});