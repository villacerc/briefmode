import { defineStore } from 'pinia';

export const useUiStore = defineStore('ui', {
  state: () => ({
    transcriptPanelOpen: true,
    dictionaryPanelOpen: true,
    moreMenuOpen: false,
  }),
  actions: {
    showDictionaryPanel() {
      this.dictionaryPanelOpen = true;
    },
    toggleTranscriptPanel() {
      this.transcriptPanelOpen = !this.transcriptPanelOpen;
    },
    toggleDictionaryPanel() {
      this.dictionaryPanelOpen = !this.dictionaryPanelOpen;
    },
    toggleMoreMenu() {
      this.moreMenuOpen = !this.moreMenuOpen;
    },
  },
});