<template>
  <div class="flex relative">
    <div class="flex w-full">
      <div class="yt-ts-container w-1/2 px-5 flex flex-col gap-3 items-center">
        <div ref="videoContainer" class="yt-player-container w-full">
          <youtube
            ref="youtubePlayer"
            :src="`https://www.youtube.com/watch?v=${route.params.id}`"
            @ready="onReady"
            width="100%"
            height="100%"
            :style="{
              aspectRatio: '16 / 9',
              borderRadius: '0.75rem',
              overflow: 'hidden',
            }"
          />
        </div>
        <div
          class="ts-primary-container h-full overflow-y-scroll overflow-x-hidden pb-3"
        >
          <TranscriptPrimary
            :activeIndex="activeIndex"
            :isAnnotation="isAnnotation"
            :removeAnnotations="removeAnnotations"
            :snippets="snippets"
            :languageUsesSpaces="languageUsesSpaces"
          />
        </div>
      </div>
      <div
        v-if="uiStore.transcriptSidebarOpen"
        class="hidden lg:flex ts-secondary-container w-1/2 rounded-xl flex-col"
      >
        <div class="flex-1 overflow-y-scroll overflow-x-hidden">
          <TranscriptSecondary
            :activeIndex="activeIndex"
            :snippets="snippets"
            :languageUsesSpaces="languageUsesSpaces"
            :isAnnotation="isAnnotation"
            :removeAnnotations="removeAnnotations"
          />
        </div>
      </div>
    </div>
    <div
      v-if="uiStore.dictionarySidebarOpen"
      class="absolute right-0 dictionary-container lg:relative max-w-[350px] flex flex-col bg-base-200"
    >
      <div class="flex-1 overflow-y-auto">
        <Dictionary />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router";
import { ref, reactive, onMounted, onUnmounted } from "vue";
import type { TranslatedSnippet } from "../../types";
import YouTube from "vue3-youtube";
import TranscriptPrimary from "./TranscriptPrimary.vue";
import TranscriptSecondary from "./TranscriptSecondary.vue";
import Dictionary from "./Dictionary.vue";
import { useUiStore } from "../../stores/uiStore.js";

const route = useRoute();
// A ref in Vue 3 is reactive (good for primitives). Whenever its .value changes,
// Vue automatically re-renders any part of the template or computed properties that depend on it.
const player = ref<any>(null);
const activeIndex = ref<number>(-1);
const snippets = reactive<TranslatedSnippet[]>([]);
const uiStore = useUiStore();
const NO_SPACE_LANGUAGES = ["ja", "zh", "th", "lo", "km", "my", "bo", "mn"];
const languageUsesSpaces = (langCode: string) => {
  return !NO_SPACE_LANGUAGES.includes(langCode);
};

const youtube = YouTube;
let animationFrame: number;

const isAnnotation = (text: string) => /^\s*[\[\(].+[\]\)]\s*$/u.test(text);

const removeAnnotations = (text: string) => {
  return text.replace(/[\[\(].+?[\]\)]/gu, "").trim();
};

onMounted(async () => {
  try {
    await fetchVideoStream(
      route.params.id as string,
      route.query.lang as string
    );
  } catch (err) {
    // TODO: redirect to error page
    console.error(err);
  }
});

onUnmounted(() => {
  cancelAnimationFrame(animationFrame);
});

const tick = () => {
  if (player.value) {
    const time = player.value.getCurrentTime();

    const idx = snippets.findIndex(
      (line) => time >= line.start && time < line.end
    );
    activeIndex.value = idx;
  }
  animationFrame = requestAnimationFrame(tick);
};

const onReady = (event: any) => {
  player.value = event.target;
  tick();
};

const fetchVideoStream = async (source_id: string, lang: string) => {
  try {
    const res = await fetch(
      `http://localhost:8000/api/video/${source_id}?lang=${lang}`
    );
    // res.body is a ReadableStream, representing the body of the response.
    // getReader() returns a stream reader that allows you to read the data chunk by chunk.
    const reader = res.body?.getReader();
    if (!reader) {
      throw new Error("Failed to get reader from response body.");
    }
    // decoder to decode the stream of raw bytes into text
    const decoder = new TextDecoder("utf-8");

    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      if (value) {
        // collect the stream (as text) into the buffer
        buffer += decoder.decode(value, { stream: true });
        // split the buffer into lines
        const lines = buffer.split("\n");
        // last line might be incomplete, use it as starting point for the buffer
        // lines.pop() mutates the array
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (line) {
            const chunk = JSON.parse(line);
            if (chunk.data) snippets.push(...chunk.data);
          }
        }
      }
    }
  } catch (error) {
    throw new Error("Failed to fetch video stream. " + error);
  }
};
</script>
