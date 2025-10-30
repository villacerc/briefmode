import { defineStore } from 'pinia';

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    to_lang: '',
  }),
  actions: {
    setToLang(lang: string) {
      this.to_lang = lang;
    },
  },
});