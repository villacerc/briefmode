<template>
  <div>
    <div class="mb-7">
      <h1 class="[font-family:'Inria',serif] text-neutral text-3xl">
        {{ entry.word }}
        {{ " " }}
        <span class="capitalize">{{ entry.romanized }}</span>
      </h1>
      <div class="flex items-center mb-1">
        <p class="mr-5">{{ entry.phonetic_spelling }}</p>
        <button class="btn-circle inline-block">
          <i class="mui-icon-fill text-2xl text-neutral">volume_up</i>
        </button>
      </div>
      <div class="border-t border-gray-400 w-full mb-2"></div>
      <span>
        {{ entry.translations.join("; ") }}
      </span>
    </div>

    <div
      class="mb-6"
      v-for="(pos, index) in entry.parts_of_speech"
      :key="index"
    >
      <h1 class="mb-3 capitalize">{{ pos.name }}</h1>
      <div class="border-t border-gray-400 w-full mb-2"></div>
      <div class="mb-2">
        <p class="mb-5">{{ pos.definition }}</p>
        <p class="mb-2 text-sm">EXAMPLE</p>
        <div class="bg-base-100 p-3 rounded-lg">
          <SnippetWords :words="pos.example_words" />
        </div>
        <p class="px-5 py-2">
          {{ pos.example_translation }}
        </p>
      </div>
    </div>

    <div class="mb-6" v-if="snippetExamples.length > 0">
      <h1 class="mb-3">Transcript Examples</h1>
      <div class="border-t border-gray-400 w-full mb-3"></div>
      <div class="mb-2" v-for="(snippet, idx) in snippetExamples" :key="idx">
        <div
          @click="eventStore.seekSnippet(snippet)"
          class="cursor-pointer relative group"
        >
          <p class="bg-base-100 p-3 rounded-lg">
            <SnippetWords :words="snippet.snippet_words" />
          </p>
          <div class="absolute -left-3.5 top-1/2 translate-y-[-50%]">
            <i
              class="mui-icon-fill text-2xl transition text-warning/70 group-hover:text-warning/100"
              >play_circle</i
            >
          </div>
        </div>

        <p class="px-5 py-2">
          {{ snippet.translation }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DictionaryWordEntry, TranslatedSnippet } from "../../types";
import SnippetWords from "../../components/SnippetWords.vue";
import { onMounted, ref } from "vue";
import { useEventStore } from "../../stores/eventStore.ts";

const eventStore = useEventStore();

const snippetExamples = ref<TranslatedSnippet[]>([]);

const props = defineProps({
  entry: {
    type: Object as () => DictionaryWordEntry,
    required: true,
  },
  snippets: {
    type: Array as () => TranslatedSnippet[],
    required: true,
  },
});

onMounted(() => {
  findSnippetExamples();
});

const findSnippetExamples = () => {
  snippetExamples.value = props.snippets.filter((snippet) =>
    snippet.text.toLowerCase().includes(props.entry.word.toLowerCase())
  );
};
</script>
