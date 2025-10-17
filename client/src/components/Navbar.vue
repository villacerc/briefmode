<template>
  <nav class="bg-base-200 fixed top-0 left-0 right-0 z-10">
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
        <li class="relative">
          <div class="btn-circle" @click="toggleMoreMenu">
            <MoreIcon class="w-6 h-6" />
          </div>
          <ul
            class="absolute top-full right-0 mt-2 w-48 bg-base-100 rounded shadow-md"
            v-if="uiStore.moreMenuOpen"
          >
            <li>
              <a
                href="#"
                class="block px-4 py-2 hover:bg-base-200 hover:brightness-98 filter"
                >Settings</a
              >
            </li>
            <li>
              <a
                href="#"
                class="block px-4 py-2 hover:bg-base-200 hover:brightness-98 filter"
                >Settings</a
              >
            </li>
          </ul>
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

function toggleMoreMenu() {
  uiStore.toggleMoreMenu();
}
</script>
