import { defineStore } from 'pinia'
import { removePunctuation } from '../utils/helpers';

export const useEventStore = defineStore('event', {
  state: () => ({
    wordToLookup: '',
  }),
  actions: {
    lookupWord(word: string) {
      this.wordToLookup = removePunctuation(word).trim();
    },
  },
});