<template>
  <div class="flex flex-col gap-4 items-center">
    <div v-for="n in 10" :key="n">
      <div
        v-for="(snippet, index) in snippets"
        :key="index"
        class="cursor-pointer text-base-content/45 hover:text-base-content border hover:border-slate-300 transition max-w-[820px] grid grid-cols-[1.5fr_1fr] gap-2 rounded-2xl items-start shadow-sm"
        :class="[
          index === activeIndex
            ? 'bg-accent text-base-content/100 border-slate-300'
            : 'bg-base-100 border-transparent',
        ]"
        @click="emit('snippetClick', snippet)"
      >
        <div class="flex p-2 gap-4 items-center rounded-md">
          <div class="ml-2 px-2 rounded-2xl bg-warning h-fit">
            <p>{{ formatTime(snippet.start) }}</p>
          </div>
          <div class="p-4 rounded-2xl bg-base-100 shadow-sm">
            <SnippetWords :words="snippet.snippet_words" />
          </div>
        </div>
        <div class="p-2">
          <div class="p-4">
            <p>{{ snippet.translation }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TranslatedSnippet } from "../../types";
import SnippetWords from "../../components/SnippetWords.vue";

const formatTime = (seconds: number) => {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  }
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

const props = defineProps({
  activeIndex: {
    type: Number,
    required: true,
  },
  snippets: {
    type: Array as () => TranslatedSnippet[],
    required: true,
  },
});
const emit = defineEmits(["snippetClick"]);
</script>
