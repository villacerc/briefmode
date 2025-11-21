<template>
  <div class="px-5 py-2">
    <h1 class="[font-family:'Inria',serif] text-2xl mb-1">Dictionary</h1>
    <div class="mb-4">
      <label
        class="input w-full p-2 flex items-center gap-2 rounded-md transition focus-within:border-neutral focus-within:outline-none"
      >
        <input
          type="search"
          v-model="search"
          @input="handleSearch"
          required
          class="flex-1 bg-transparent"
        />
        <i class="mui-icon text-2xl text-base-content/65">search</i>
      </label>
    </div>

    <!-- Dictionary Word Entry Section -->
    <div v-if="fetchingEntry === false && dictionaryWordEntry !== null">
      <DictionaryWordContent
        :entry="dictionaryWordEntry"
        :snippets="snippets"
      />
    </div>

    <!-- Dictionary Snippet Entry Section -->
    <div v-else-if="fetchingEntry === false && dictionarySnippetEntry !== null">
      <div class="bg-base-100 p-3 rounded-lg">
        <SnippetWords :words="dictionarySnippetEntry.snippet_words" />
      </div>
      <p class="px-4 py-2">
        {{ dictionarySnippetEntry.translation }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import type {
  DictionaryWordEntry,
  DictionarySnippetEntry,
  TranslatedSnippet,
} from "../../types";
import DictionaryWordContent from "./DictionaryWordContent.vue";
import SnippetWords from "../../components/SnippetWords.vue";
import { useEventStore } from "../../stores/eventStore";
import { useSettingsStore } from "../../stores/settingsStore";

const eventStore = useEventStore();
const settingsStore = useSettingsStore();

const dictionaryWordEntry = ref<DictionaryWordEntry | null>(null);
const dictionarySnippetEntry = ref<DictionarySnippetEntry | null>(null);
const fetchingEntry = ref(false);
const search = ref("");
let inputTimeout: number = 0;

const props = defineProps({
  snippets: {
    type: Array as () => TranslatedSnippet[],
    required: true,
  },
});

onMounted(() => {
  if (eventStore.wordToLookup) {
    search.value = eventStore.wordToLookup;
    handleSearch();
  }
});

watch(
  () => eventStore.wordToLookup,
  (newWord) => {
    search.value = newWord;
    handleSearch();
  }
);

const handleSearch = async () => {
  fetchingEntry.value = true;
  clearTimeout(inputTimeout);
  inputTimeout = setTimeout(async () => {
    try {
      dictionaryWordEntry.value = null;
      dictionarySnippetEntry.value = null;

      const searchValue = search.value.trim();
      if (searchValue === "") {
        return;
      }

      const entry = await fetchDictionaryEntry(searchValue);
      if (entry.is_interpretable && entry.is_word) {
        dictionaryWordEntry.value = entry.data as DictionaryWordEntry;
      } else if (entry.is_interpretable) {
        dictionarySnippetEntry.value = entry.data as DictionarySnippetEntry;
      }
    } catch (err) {
      console.error(err);
    } finally {
      fetchingEntry.value = false;
    }
  }, 2000);
};

const fetchDictionaryEntry = async (word: string) => {
  try {
    const response = await fetch(
      `http://localhost:8000/api/dictionary/${word}?source_lang_code=${settingsStore.videoInfo?.source_lang_code}&target_lang_code=${settingsStore.targetLangCode}`
    );
    if (!response.ok) throw new Error("Network response was not ok");
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching dictionary entry:", error);
    throw error;
  }
};
</script>
