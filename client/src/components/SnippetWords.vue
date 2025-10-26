<template>
  <Popup
    v-for="(part, j) in snippet.snippet_words"
    :key="j"
    class="cursor-pointer hover:bg-info hover:text-base-content rounded-sm"
  >
    <p class="text-sm">
      {{ removeAnnotations(part.romanized) }}
    </p>
    <p class="">
      {{ part.text }}
    </p>
    <span v-if="languageUsesSpaces(snippet.transcript_language)">
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
</template>

<script setup lang="ts">
import { defineProps } from "vue";
import type { TranslatedSnippet } from "../types.js";
import Popup from "./Popup.vue";
import { languageUsesSpaces, removeAnnotations } from "../utils/helpers.js";

const props = defineProps({
  snippet: {
    type: Object as () => TranslatedSnippet,
    required: true,
  },
});
</script>
