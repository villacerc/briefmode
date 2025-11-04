<template>
  <nav>
    <div class="flex py-1 px-2">
      <h1 class="font-medium text-lg self-center">
        Easy Japanese 1 - Typical Japanese
      </h1>
      <ul class="flex ml-auto space-x-2">
        <li
          class="btn-circle text-base-content/70"
          :class="[uiStore.transcriptPanelOpen ? 'btn-toggled' : '']"
          @click="toggleTranscriptPanel"
        >
          <i class="mui-icon text-2xl">subtitles</i>
        </li>
        <li
          class="btn-circle text-base-content/70"
          :class="[uiStore.dictionaryPanelOpen ? 'btn-toggled' : '']"
          @click="toggleDictionaryPanel"
        >
          <i class="mui-icon text-2xl">translate</i>
        </li>
        <li class="relative">
          <div
            class="btn-circle text-base-content/70"
            :class="[uiStore.moreMenuOpen ? 'btn-active' : '']"
            @click="toggleMoreMenu"
            v-click-outside="closeMenu"
          >
            <i class="mui-icon text-2xl">more_vert</i>
          </div>
          <transition
            enter-active-class="transition duration-150 ease-out"
            enter-from-class="opacity-0 transform -translate-y-2 scale-95"
            enter-to-class="opacity-100 transform translate-y-0 scale-100"
          >
            <ul
              class="overflow-hidden absolute top-full z-1 right-[-8px] mt-1 w-40 bg-base-100 rounded-md shadow-md"
              v-if="uiStore.moreMenuOpen"
            >
              <li>
                <a href="#" class="menu-item">
                  <i class="mui-icon text-lg mt-[2px]">home</i>
                  <span class="ml-3">Home</span>
                </a>
              </li>
              <li>
                <a href="#" class="menu-item">
                  <i class="mui-icon text-lg">volunteer_activism</i>
                  <span class="ml-3">Support Us</span>
                </a>
              </li>
              <li>
                <a href="#" class="menu-item">
                  <i class="mui-icon text-lg mt-1">feedback</i>
                  <span class="ml-3">Feedback</span>
                </a>
              </li>
            </ul>
          </transition>
        </li>
      </ul>
    </div>
  </nav>
</template>

<script setup>
import { useUiStore } from "../stores/uiStore";
const uiStore = useUiStore();

function toggleTranscriptPanel() {
  uiStore.toggleTranscriptPanel();
}

function toggleDictionaryPanel() {
  uiStore.toggleDictionaryPanel();
}

function toggleMoreMenu() {
  uiStore.toggleMoreMenu();
}

function closeMenu() {
  uiStore.moreMenuOpen = false;
}
</script>
