import { defineStore } from 'pinia';

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    targetLangCode: '',
  }),
  actions: {
    setTargetLangCode(lang: string) {
      this.targetLangCode = lang;
    },
  },
});