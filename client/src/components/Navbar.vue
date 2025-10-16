<template>
  <nav class="bg-base-200">
    <div class="flex py-1 px-2">
      <h1 class="font-medium text-lg self-center">
        Easy Japanese 1 - Typical Japanese
      </h1>
      <ul class="flex ml-auto space-x-2">
        <li
          :class="[
            uiStore.transcriptSidebarOpen ? 'btn-circle-active' : 'btn-circle',
          ]"
          @click="toggleTranscriptSidebar"
        >
          <div><TranscriptIcon class="w-6 h-6" /></div>
        </li>
        <li
          :class="[
            uiStore.dictionarySidebarOpen ? 'btn-circle-active' : 'btn-circle',
          ]"
          @click="toggleDictionarySidebar"
        >
          <div><DictionaryIcon /></div>
        </li>
        <li class="btn-circle">
          <div><MoreIcon class="w-6 h-6" /></div>
        </li>
      </ul>
    </div>
  </nav>
</template>

<script setup>
import { useUiStore } from "../stores/uiStore.js";
import TranscriptIcon from "../icons/Transcript.vue";
import DictionaryIcon from "../icons/Dictionary.vue";
import MoreIcon from "../icons/More.vue";
const uiStore = useUiStore();

function toggleTranscriptSidebar() {
  uiStore.toggleTranscriptSidebar();
}

function toggleDictionarySidebar() {
  uiStore.toggleDictionarySidebar();
}
</script>
