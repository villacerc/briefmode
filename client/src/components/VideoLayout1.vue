<template>
  <div class="my-10 mx-15">
    <h1 class="text-xl font-medium mb-5 text-accent-content text-center">
      How I Went From Broke To Millionaire in 24 Months
    </h1>
    <div class="youtube-layout">
      <div class="youtube-primary">
        <div
          ref="videoContainer"
          class="youtube-player-container rounded-lg overflow-hidden"
        >
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

      <div class="youtube-sidebar border border-base-300 rounded-lg">
        <div class="h-[500px]">
          <div class="flex p-2 space-x-2">
            <button class="btn btn-neutral btn-sm">Transcript</button>
            <button class="btn btn-sm">Translation</button>
          </div>
          <!-- Content for selected tab -->
          Content goes here
        </div>
      </div>
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
