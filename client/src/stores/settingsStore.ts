import { defineStore } from 'pinia';
import type { VideoInfo } from '../types';

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    videoInfo: null as VideoInfo | null,
    targetLangCode: 'en',
  }),
  actions: {
    setVideo(videoInfo: VideoInfo | null) {
      this.videoInfo = videoInfo;
    },
    setTargetLangCode(langCode: string) {
      this.targetLangCode = langCode;
    },
  },
});