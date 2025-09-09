<template>
  <div class="youtube-layout">
    <div class="youtube-primary">
      <h1 class="text-xl font-bold mb-[7px]">
        How I Went From Broke To Millionaire in 24 Months
      </h1>

      <div ref="videoContainer" class="youtube-player-container">
        <youtube
          ref="youtubePlayer"
          src="https://www.youtube.com/watch?v=oLIkRpKLH1Y"
          width="100%"
          height="100%"
          :style="{ width: '100%', height: '100%' }"
          @ready="onReady"
        />
      </div>

      <div class="mt-[10px] p-[10px]">Transcript</div>
      <div class="mt-[10px] p-[10px]">More Content</div>
    </div>

    <div class="youtube-sidebar">
      <div class="h-[500px]">Column 2 content</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import YouTube from "vue3-youtube";
const youtube = YouTube;

defineProps({
  visibleLines: Array,
  activeIndex: Number,
  isDragging: Boolean,
});

defineEmits(["ready", "update:active-index"]);
</script>
