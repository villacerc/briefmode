import { defineStore } from 'pinia'
import type { TranslatedSnippet } from '../types';

export const useEventStore = defineStore('event', {
  state: () => ({
    wordToLookup: '',
    snippetToSeek: null as TranslatedSnippet | null,
  }),
  actions: {
    lookupWord(word: string) {
      this.wordToLookup = word.trim();
    },
    seekSnippet(snippet: TranslatedSnippet) {
      this.snippetToSeek = snippet;
    }
  },
});