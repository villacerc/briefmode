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

    <div class="mb-6" v-if="transcriptExamples.length > 0">
      <h1 class="mb-3">Transcript Examples</h1>
      <div class="border-t border-gray-400 w-full mb-3"></div>
      <div class="mb-2" v-for="(example, idx) in transcriptExamples" :key="idx">
        <p class="bg-base-100 p-3 rounded-lg">
          <SnippetWords :words="example.snippet_words" />
        </p>
        <p class="px-5 py-2">
          {{ example.translation }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DictionaryWordEntry, TranslatedSnippet } from "../../types";
import SnippetWords from "../../components/SnippetWords.vue";
import { onMounted, ref } from "vue";

const transcriptExamples = ref<TranslatedSnippet[]>([]);

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
  findTranscriptExamples();
});

const findTranscriptExamples = () => {
  transcriptExamples.value = props.snippets.filter((snippet) =>
    snippet.text.toLowerCase().includes(props.entry.word.toLowerCase())
  );
};
</script>
