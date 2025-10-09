<template>
  <div>
    <div
      class="p-2 grid grid-cols-[1.5fr_1fr] gap-3 rounded-md items-start"
      v-for="(snippet, index) in snippets"
      :key="index"
    >
      <div
        :class="[index === activeIndex ? 'bg-base-100' : 'bg-base-200']"
        class="flex p-2 gap-3 items-start rounded-md"
      >
        <div class="ml-2 px-2 rounded-md bg-warning text-neutral-content h-fit">
          <p>0:01</p>
        </div>
        <div>
          <span
            v-for="(part, j) in snippet.snippet_words"
            :key="j"
            class="relative cursor-pointer inline-block group/word hover:bg-secondary hover:text-base-content rounded-sm"
            @mouseenter="checkPopupPosition(j, $event)"
          >
            <p class="text-sm">
              {{ removeAnnotations(part.romanized) }}
            </p>
            <p class="">
              {{ part.text }}
            </p>
            <!-- Hover popup -->
            <div
              :ref="(el) => setPopupRef(el, j)"
              class="absolute left-1/2 -translate-x-1/2 opacity-0 scale-90 invisible group-hover/word:visible group-hover/word:opacity-100 group-hover/word:scale-100 transition-opacity transition-transform duration-250 ease-out z-50"
              :class="
                shouldShowBelow(j)
                  ? 'top-full mt-2 origin-top'
                  : 'bottom-full mb-2 origin-bottom'
              "
            >
              <div class="text-center">
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
        </div>
      </div>
      <div class="p-2">
        <p class="text-lg">{{ snippet.translation }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from "vue";
import type { TranslatedSnippet } from "../../types";

const popupRefs = reactive<any>({});
const popupPositions = reactive<any>({});

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

const setPopupRef = (el: any, index: number) => {
  if (el) {
    popupRefs[index] = el;
  }
};

const shouldShowBelow = (index: number) => {
  return popupPositions[index] === "below";
};

const checkPopupPosition = (index: number, event: MouseEvent) => {
  const span = event.currentTarget as HTMLElement;
  const popupElement = popupRefs[index];

  if (!span || !popupElement) return;

  const spanRect = span.getBoundingClientRect();
  const popupRect = popupElement.getBoundingClientRect();
  const popupHeight = popupRect.height;

  // Check if there's enough space above
  if (spanRect.top < popupHeight + 20) {
    // +20 for margin
    popupPositions[index] = "below";
  } else {
    popupPositions[index] = "above";
  }
};
</script>
