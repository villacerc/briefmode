<template>
  <div v-for="n in 10" :key="n">
    <div
      v-for="(snippet, index) in snippets"
      :key="index"
      class="text-base-content/45 hover:text-base-content border border-transparent hover:border-slate-300 transition max-w-[820px] grid grid-cols-[1.5fr_1fr] gap-2 rounded-2xl items-start mb-5 shadow-sm"
      :class="[
        index === activeIndex
          ? 'bg-accent text-base-content/100'
          : 'bg-base-100',
      ]"
    >
      <div class="flex p-2 gap-4 items-center rounded-md">
        <div class="ml-2 px-2 rounded-2xl bg-warning h-fit">
          <p>0:01</p>
        </div>
        <div class="p-4 rounded-2xl bg-base-100 shadow-sm">
          <Popup
            v-for="(part, j) in snippet.snippet_words"
            :key="j"
            class="cursor-pointer hover:bg-info rounded-sm"
          >
            <p>
              {{ removeAnnotations(part.romanized) }}
            </p>
            <p>
              {{ part.text }}
            </p>
            <template #popup-content>
              <div
                class="bg-info shadow-sm text-center rounded-lg p-3 pt-2 w-fit whitespace-nowrap"
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
        </div>
      </div>
      <div class="p-2">
        <div class="p-4">
          <p>{{ snippet.translation }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TranslatedSnippet } from "../../types";
import Popup from "../../components/Popup.vue";

const props = defineProps({
  activeIndex: {
    type: Number,
    required: true,
  },
  snippets: {
    type: Array as () => TranslatedSnippet[],
    required: true,
  },
  languageUsesSpaces: {
    type: Function,
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
});
</script>
