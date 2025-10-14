<template>
  <nav class="bg-base-100">
    <div class="flex flex-1 pt-1">
      <ul class="menu menu-horizontal m-auto text-base p-0">
        <li @click="toggleTranscriptSidebar"><a>Home</a></li>
        <li @click="toggleDictionarySidebar"><a>Support Us</a></li>
        <li><a>Feedback</a></li>
      </ul>
    </div>
  </nav>
</template>

<script setup>
import { useUiStore } from "../stores/uiStore.js";
const uiStore = useUiStore();

function toggleTranscriptSidebar() {
  uiStore.toggleTranscriptSidebar();
}

function toggleDictionarySidebar() {
  uiStore.toggleDictionarySidebar();
}
</script>
