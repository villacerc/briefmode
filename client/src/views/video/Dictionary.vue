<template>
  <div class="px-5 py-2">
    <h1 class="[font-family:'Inria',serif] text-2xl mb-1">Dictionary</h1>
    <div class="mb-4">
      <label
        class="input p-2 flex items-center gap-2 rounded-md transition focus-within:border-neutral focus-within:outline-none"
      >
        <input type="search" required class="flex-1 bg-transparent" />
        <i class="mui-icon text-2xl text-base-content/65">search</i>
      </label>
    </div>

    <!-- Dictionary Entry Section -->
    <div v-if="dictionaryWordEntry">
      <div class="mb-7">
        <h1 class="[font-family:'Inria',serif] text-neutral text-3xl">
          {{ dictionaryWordEntry.word }}
          {{ " " }}
          <span class="capitalize">{{ dictionaryWordEntry.romanized }}</span>
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
          {{ dictionaryWordEntry.translations.join("; ") }}
        </span>
      </div>

      <div
        class="mb-6"
        v-for="(pos, index) in dictionaryWordEntry.parts_of_speech"
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
            Tohoku is rich in nature. Tohoku is rich in nature. Tohoku is rich
            in nature. Tohoku is rich in nature.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { DictionaryWordEntry } from "../../types";
import SnippetWords from "../../components/SnippetWords.vue";

const dictionaryWordEntry = ref<DictionaryWordEntry | null>(null);

const props = defineProps({
  to_lang: {
    type: String,
    required: false,
  },
});

onMounted(async () => {
  try {
    dictionaryWordEntry.value = await fetchDictionaryEntry("tohoku");
  } catch (err) {
    // TODO: redirect to error page
    console.error(err);
  }
});

const fetchDictionaryEntry = async (word: string) => {
  try {
    const response = await fetch(
      `http://localhost:8000/api/dictionary/${word}?lang=en`
    );
    if (!response.ok) throw new Error("Network response was not ok");
    const data = await response.json();
    return data.data;
  } catch (error) {
    console.error("Error fetching dictionary entry:", error);
    throw error;
  }
};
</script>
