import { defineStore } from 'pinia';

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    toLang: '',
  }),
  actions: {
    setToLang(lang: string) {
      this.toLang = lang;
    },
  },
});