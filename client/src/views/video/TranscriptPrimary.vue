<template>
  <div
    class="text-center relative group text-2xl mt-5 px-5 py-3 bg-base-100 rounded-xl"
  >
    <span
      v-for="(line, i) in visibleLines"
      :key="i"
      class="inline-block rounded-sm"
      :class="[
        line.snippet_id === snippets[activeIndex].snippet_id &&
        !isAnnotation(line.text)
          ? 'bg-accent'
          : 'text-base-content/45',
        languageUsesSpaces(line.translation_language) ? 'mr-1' : '',
      ]"
    >
      <Popup
        v-for="(part, j) in line.snippet_words"
        :key="j"
        class="cursor-pointer hover:bg-info hover:text-base-content rounded-sm"
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
        <template #popup-content>
          <div
            class="bg-info text-center rounded-xl p-3 pt-2 w-fit whitespace-nowrap"
          >
            <ul>
              <li class="font-bold mb-1">
                {{
                  part.part_of_speech.charAt(0).toUpperCase() +
                  part.part_of_speech.slice(1) +
                  ":"
                }}
              </li>
              <li v-for="(t, i) in part.translations" :key="i">
                {{ t.text }}
              </li>
            </ul>
          </div>
        </template>
      </Popup>
    </span>
  </div>
  <div
    class="text-center bg-base-100 relative group text-2xl mt-2 px-5 py-3 rounded-xl"
  >
    <span
      v-for="(line, i) in visibleLines"
      :key="i"
      class="inline-block rounded-sm"
      :class="[
        line.snippet_id === snippets[activeIndex].snippet_id &&
        !isAnnotation(line.text)
          ? 'bg-base-accent'
          : 'text-base-content/45',
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
import Popup from "../../components/Popup.vue";

const VISIBLE_LINES_SIZE = 3;

const props = defineProps({
  languageUsesSpaces: {
    type: Function,
    required: true,
  },
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
