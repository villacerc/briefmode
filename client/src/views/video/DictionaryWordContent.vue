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
        <button @click="playTTS" class="btn-circle inline-block">
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
import { base64ToBlob } from "../../utils/helpers";

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

const fetchTTS = async (text: string, sourceLangCode: string) => {
  try {
    const response = await fetch(
      `http://localhost:8000/api/tts/${text}?source_lang_code=${sourceLangCode}`
    );
    if (!response.ok) throw new Error("Network response was not ok");
    const data = await response.json();
    return data.audio;
  } catch (error) {
    console.error("Error fetching dictionary entry:", error);
    throw error;
  }
};

const playAudio = (audioBase64: string) => {
  // Create a Blob URL from Base64
  const audioBlob = base64ToBlob(audioBase64, "audio/mp3");
  const audioUrl = URL.createObjectURL(audioBlob);

  const audio = new Audio(audioUrl);
  audio.play();
};

const playTTS = async () => {
  const audioBase64 = await fetchTTS(
    props.entry.word,
    props.entry.source_lang_code
  );
  playAudio(audioBase64);
};
</script>
