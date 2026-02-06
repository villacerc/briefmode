<template>
  <div
    v-if="visibleSnippets.length > 0"
    class="shadow-sm border border-slate-300 text-center relative group text-2xl px-5 py-3 bg-base-100 rounded-xl"
  >
    <span
      v-for="(snippet, i) in visibleSnippets"
      :key="i"
      class="inline-block rounded-sm"
      :class="[
        snippet.snippet_id === snippets[activeIndex].snippet_id &&
        !isAnnotation(snippet.text)
          ? 'bg-accent'
          : 'text-base-content/45',
        languageUsesSpaces(snippet.target_lang_code) ? 'mr-1' : '',
      ]"
    >
      <SnippetWords
        :words="snippet.snippet_words"
        :sourceLangCode="snippet.source_lang_code"
      />
    </span>
  </div>
  <div
    v-if="visibleSnippets.length > 0"
    class="shadow-sm text-center bg-base-100 relative group text-2xl mt-2 px-5 py-3 rounded-xl"
  >
    <span
      v-for="(snippet, i) in visibleSnippets"
      :key="i"
      class="inline-block rounded-sm"
      :class="[
        snippet.snippet_id === snippets[activeIndex].snippet_id &&
        !isAnnotation(snippet.text)
          ? 'bg-base-accent'
          : 'text-base-content/45',
        languageUsesSpaces(snippet.target_lang_code) ? 'mr-1' : '',
      ]"
    >
      {{ snippet.translation }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { TranslatedSnippet } from "../../types";
import SnippetWords from "../../components/SnippetWords.vue";
import { languageUsesSpaces, isAnnotation } from "../../utils/helpers.js";

const VISIBLE_LINES_SIZE = 3;

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

const visibleSnippets = computed<TranslatedSnippet[]>(() => {
  if (props.activeIndex === -1) return [];

  const snippet = props.snippets[props.activeIndex];

  if (isAnnotation(snippet.text)) {
    // Show annotation by itself
    return [snippet];
  }

  const groupStart =
    Math.floor(props.activeIndex / VISIBLE_LINES_SIZE) * VISIBLE_LINES_SIZE;
  const groupEnd = Math.min(
    groupStart + VISIBLE_LINES_SIZE,
    props.snippets.length
  );

  let group: TranslatedSnippet[] = [];
  for (let i = groupEnd - 1; i >= groupStart && i >= 0; i--) {
    const s = props.snippets[i];
    if (isAnnotation(s.text) && i < props.activeIndex) {
      // stop when hitting annotation after normal text
      break;
    } else if (isAnnotation(s.text)) {
      group = [];
      continue;
    }
    group.unshift(s);
  }

  return group;
});
</script>
