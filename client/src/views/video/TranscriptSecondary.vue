<template>
  <div class="flex flex-col gap-4 items-center">
    <!-- <div v-for="n in 10" :key="n"> -->
    <div
      v-for="(snippet, index) in snippets"
      :key="index"
      :ref="
        (el) => {
          if (el) snippetRefs[index] = el as HTMLElement;
        }
      "
      class="cursor-pointer w-full text-base-content/45 hover:text-base-content border hover:border-slate-300 transition max-w-[820px] grid grid-cols-[1.5fr_1fr] gap-2 rounded-2xl items-start shadow-sm"
      :class="[
        index === activeIndex
          ? 'bg-accent text-base-content/100 border-slate-300'
          : 'bg-base-100 border-transparent',
      ]"
      @click="eventStore.seekSnippet(snippet)"
    >
      <div class="flex p-2 gap-4 items-center rounded-md">
        <div class="ml-2 px-2 rounded-2xl bg-warning h-fit">
          <p>{{ formatSnippetTime(snippet.start) }}</p>
        </div>
        <div class="p-4 w-full rounded-2xl bg-base-100 shadow-sm">
          <SnippetWords
            :words="snippet.snippet_words"
            :sourceLangCode="snippet.source_lang_code"
          />
        </div>
      </div>
      <div class="p-2">
        <div class="p-4">
          <p>{{ snippet.translation }}</p>
        </div>
      </div>
    </div>
    <!-- </div> -->
    <div
      v-show="!eventStore.allSnippetsFetched"
      class="skeleton h-30 w-full mb-4 rounded-2xl"
    ></div>
  </div>

  <button
    v-if="!isActiveSnippetInView"
    @click="handleScrollToActiveSnippet"
    class="fixed bottom-6 right-6 z-50 btn-circle btn-toggled text-base-content/70"
  >
    <i class="mui-icon text-4xl">{{
      isActiveSnippetBelow ? "arrow_drop_down" : "arrow_drop_up"
    }}</i>
  </button>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import type { TranslatedSnippet } from "../../types";
import SnippetWords from "../../components/SnippetWords.vue";
import { useEventStore } from "../../stores/eventStore";
import { formatSnippetTime } from "../../utils/helpers";

const eventStore = useEventStore();
const snippetRefs = ref<HTMLElement[]>([]);
const isActiveSnippetInView = ref(true);
const isActiveSnippetBelow = ref(false);
const isAutoScrolled = ref(true);
let observer: IntersectionObserver | null = null;

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

function scrollToActiveSnippet() {
  isActiveSnippetInView.value = true;
  snippetRefs.value[props.activeIndex]?.scrollIntoView({
    behavior: "smooth",
    block: "center",
  });
}

function handleScrollToActiveSnippet() {
  isAutoScrolled.value = true;
  scrollToActiveSnippet();
}

function observeActiveSnippet(index: number) {
  observer?.disconnect();
  const el = snippetRefs.value[index];
  if (!el) return;

  observer = new IntersectionObserver(
    ([entry]) => {
      isActiveSnippetInView.value = entry.isIntersecting;
      if (!entry.isIntersecting) {
        isAutoScrolled.value = false;
        isActiveSnippetBelow.value = entry.boundingClientRect.top > 0;
      } else if (entry.isIntersecting && !isAutoScrolled.value) {
        isAutoScrolled.value = true;
      }
    },
    { threshold: 0.5 } // consider "in view" when 50% visible
  );
  observer.observe(el);
}

watch(
  () => props.activeIndex,
  (index) => {
    if (isAutoScrolled.value) {
      scrollToActiveSnippet();
    }
    observeActiveSnippet(index);
  },
  { immediate: true }
);
</script>
