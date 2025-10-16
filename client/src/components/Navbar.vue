<template>
  <nav class="bg-base-200">
    <div class="flex py-1 px-2">
      <h1 class="font-bold text-lg self-center">
        Easy Japanese 1 - Typical Japanese
      </h1>
      <ul class="flex ml-auto space-x-2">
        <li
          class="bg-base-100 rounded-full w-10 h-10 flex items-center justify-center hover:cursor-pointer hover:bg-base-300 hover:text-white"
          @click="toggleTranscriptSidebar"
        >
          <div><TranscriptIcon /></div>
        </li>
        <li
          class="bg-base-100 rounded-full w-10 h-10 flex items-center justify-center hover:cursor-pointer hover:bg-base-300"
          @click="toggleDictionarySidebar"
        >
          <div><DictionaryIcon /></div>
        </li>
      </ul>
    </div>
  </nav>
</template>

<script setup>
import { useUiStore } from "../stores/uiStore.js";
import TranscriptIcon from "../icons/Transcript.vue";
import DictionaryIcon from "../icons/Dictionary.vue";
const uiStore = useUiStore();

function toggleTranscriptSidebar() {
  uiStore.toggleTranscriptSidebar();
}

function toggleDictionarySidebar() {
  uiStore.toggleDictionarySidebar();
}
</script>
