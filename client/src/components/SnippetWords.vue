<template>
  <Popup
    v-for="(word, j) in snippet.snippet_words"
    :key="j"
    @click.stop="wordClicked(word.text)"
    class="cursor-pointer hover:bg-info hover:text-base-content rounded-sm px-1"
  >
    <p class="text-sm">
      {{ removeAnnotations(word.romanized) }}
    </p>
    <p>
      {{ word.text }}
    </p>
    <span v-if="languageUsesSpaces(settingsStore.toLang)">
      {{ " " }}
    </span>
    <template #popup-content>
      <div
        class="bg-info text-center rounded-xl p-3 pt-2 w-fit whitespace-nowrap"
      >
        <ul>
          <li class="font-bold mb-1">
            {{
              word.part_of_speech.charAt(0).toUpperCase() +
              word.part_of_speech.slice(1)
            }}
          </li>
          <li
            v-if="snippet.source_lang_code != snippet.target_lang_code"
            v-for="(t, i) in word.translations"
            :key="i"
          >
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
import { useSettingsStore } from "../stores/settingsStore.ts";
import { useEventStore } from "../stores/eventStore.ts";
import { useUiStore } from "../stores/uiStore.ts";
const settingsStore = useSettingsStore();
const eventStore = useEventStore();
const uiStore = useUiStore();

const wordClicked = (wordText: string) => {
  eventStore.lookupWord(wordText);
  uiStore.showDictionaryPanel();
};

const props = defineProps({
  snippet: {
    type: Object as () => TranslatedSnippet,
    required: true,
  },
});
</script>
