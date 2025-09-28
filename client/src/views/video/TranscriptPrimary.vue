<template>
  <div
    class="text-center relative group text-xl mt-2 px-5 py-2 bg-base-200 border border-base-300 rounded-xl"
  >
    <span
      v-for="(line, i) in visibleLines"
      :key="i"
      class="inline-block rounded-sm"
      :class="[
        line.snippet_id === snippets[activeIndex].snippet_id &&
        !isAnnotation(line.text)
          ? 'bg-neutral text-neutral-content'
          : '',
        languageUsesSpaces(line.translation_language) ? 'mr-1' : '',
      ]"
    >
      <span
        v-for="(part, j) in line.snippet_words"
        :key="j"
        class="relative cursor-pointer inline-block group/word hover:bg-secondary hover:text-base-content rounded-sm"
      >
        <p class="text-sm">
          {{ removeAnnotations(part.romanized) }}
        </p>
        <p class="">
          {{ part.text }}
        </p>
        <span v-if="languageUsesSpaces(line.transcript_language)">
          {{ " " }}
        </span>

        <!-- Hover popup -->
        <div
          class="absolute bottom-full left-1/2 -translate-x-1/2 opacity-0 scale-90 invisible origin-bottom group-hover/word:visible group-hover/word:opacity-100 group-hover/word:scale-100 transition-opacity transition-transform duration-250 ease-out z-50"
        >
          <div class="mb-2">
            <div class="card shadow-lg bg-base-100 rounded-xl p-3 pt-2">
              <ul class="text-md text-base-content w-fit whitespace-nowrap">
                <p class="font-bold mb-1">
                  {{
                    part.part_of_speech.charAt(0).toUpperCase() +
                    part.part_of_speech.slice(1) +
                    ":"
                  }}
                </p>
                <li v-for="(t, i) in part.translations" :key="i">
                  {{ t.text }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </span>
    </span>
  </div>
  <div
    class="text-center relative group text-xl mt-2 px-5 py-2 border border-base-300 rounded-xl"
  >
    <span
      v-for="(line, i) in visibleLines"
      :key="i"
      class="inline-block rounded-sm"
      :class="[
        line.snippet_id === snippets[activeIndex].snippet_id &&
        !isAnnotation(line.text)
          ? 'bg-neutral text-neutral-content'
          : '',
        languageUsesSpaces(line.translation_language) ? 'mr-1' : '',
      ]"
    >
      {{ line.translation }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { TranslatedSnippet } from "../../types";

const VISIBLE_LINES_SIZE = 3;
const NO_SPACE_LANGUAGES = ["ja", "zh", "th", "lo", "km", "my", "bo", "mn"];

const languageUsesSpaces = (langCode: string) => {
  return !NO_SPACE_LANGUAGES.includes(langCode);
};

const props = defineProps({
  activeIndex: {
    type: Number,
    required: true,
  },
  isAnnotation: {
    type: Function,
    required: true,
  },
  removeAnnotations: {
    type: Function,
    required: true,
  },
  snippets: {
    type: Array as () => TranslatedSnippet[],
    required: true,
  },
});

const visibleLines = computed<TranslatedSnippet[]>(() => {
  if (props.activeIndex === -1) return [];

  const snippet = props.snippets[props.activeIndex];

  if (props.isAnnotation(snippet.text)) {
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
    if (props.isAnnotation(s.text) && i < props.activeIndex) {
      // stop when hitting annotation after normal text
      break;
    } else if (props.isAnnotation(s.text)) {
      group = [];
      continue;
    }
    group.unshift(s);
  }

  return group;
});
</script>
