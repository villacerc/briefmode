<template>
  <div>
    <div class="mb-7">
      <h1 class="[font-family:'Inria',serif] text-neutral text-3xl">
        {{ entry.word }}
        {{ " " }}
        <span class="capitalize">{{ entry.romanized }}</span>
      </h1>
      <div class="flex items-center mb-1">
        <p class="mr-5">con - gru - ity</p>
        <p class="mr-3">con - gru - ity</p>
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
          <SnippetWords :words="pos.example_words" :to_lang="props.to_lang" />
        </div>
        <p class="px-4 py-2">
          {{ pos.example_translation }}
        </p>
      </div>
    </div>

    <div class="mb-6">
      <h1 class="mb-3">Transcript Examples</h1>
      <div class="border-t border-gray-400 w-full mb-3"></div>
      <div class="mb-2">
        <p class="bg-base-100 p-3 rounded-lg mb-2">
          東北は自然が豊かです。 東北は自然が豊かです。 東北は自然が豊かです。
          東北は自然が豊かです。
        </p>
        <p class="p-3">
          Tohoku is rich in nature. Tohoku is rich in nature. Tohoku is rich in
          nature. Tohoku is rich in nature.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DictionaryWordEntry } from "../../types";
import SnippetWords from "../../components/SnippetWords.vue";

const props = defineProps({
  entry: {
    type: Object as () => DictionaryWordEntry,
    required: true,
  },
});
</script>
