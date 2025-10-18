<template>
  <div v-for="n in 10" :key="n">
    <div
      v-for="(snippet, index) in snippets"
      :key="index"
      class="grid grid-cols-[1.5fr_1fr] gap-2 rounded-md items-start mb-5"
      :class="[index === activeIndex ? 'bg-accent' : 'bg-base-100']"
    >
      <div class="flex p-2 gap-4 items-center rounded-md">
        <div class="ml-2 px-2 rounded-md bg-warning h-fit">
          <p>0:01</p>
        </div>
        <div>
          <Tooltip
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
            <template #tooltip-content>
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
          </Tooltip>
        </div>
      </div>
      <div class="p-2">
        <p>{{ snippet.translation }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from "vue";
import type { TranslatedSnippet } from "../../types";
import Tooltip from "../../components/Tooltip.vue";

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
