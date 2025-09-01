<template>
  <div class="gap-4 p-4">
    <!-- Video -->
    <div>
      <youtube
        src="https://www.youtube.com/watch?v=oLIkRpKLH1Y" 
        width="100%"
        height="390"
        @ready="onReady"
      />
    </div>

    <!-- Transcript -->
    <div class="max-h-[390px] overflow-y-auto border rounded-lg p-4 bg-gray-50">
      <p class="p-1 transition-colors text-center">
        <span
          v-for="(line, idx) in visibleLines"
          :key="idx"
        >
          <span
            :class="activeIndex !== -1 && idx === activeIndex % 3
              ? 'bg-yellow-200 font-semibold'
              : ''"
          >
            {{ line.translation }}
          </span>
          {{" "}}
        </span>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from "vue";
import YouTube from "vue3-youtube";

type TranslatedSnippet = {
  text: string;
  translation: string;
  start: number;
  end: number;
  duration: number;
};

// Register YouTube component
const youtube = YouTube;

// A ref in Vue 3 is reactive (good for primitives). Whenever its .value changes, 
// Vue automatically re-renders any part of the template or computed properties that depend on it.
const player = ref<any>(null);
const activeIndex = ref<number>(-1);
const snippets = reactive<TranslatedSnippet[]>([]);

let animationFrame: number;

const tick = () => {
  if (player.value) {
    const time = player.value.getCurrentTime();

    const idx = snippets.findIndex(
      (line) => time >= line.start && time < line.end
    );
    activeIndex.value = idx;
  }
  animationFrame = requestAnimationFrame(tick);
};

const onReady = (event: any) => {
  player.value = event.target;
  tick();
};

const getVideoStream = async (source_id: string, to_lang: string) => {
  try {
    const res = await fetch(`http://localhost:8000/api/video/${source_id}?to_lang=${to_lang}`);
    // res.body is a ReadableStream, representing the body of the response.
    // getReader() returns a stream reader that allows you to read the data chunk by chunk.
    const reader = res.body?.getReader();
    if (!reader) {
      throw new Error("Failed to get reader from response body.");
    }
    // decoder to decode the stream of raw bytes into text
    const decoder = new TextDecoder("utf-8");

    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      if (value) {
        // collect the stream (as text) into the buffer
        buffer += decoder.decode(value, { stream: true });
        // split the buffer into lines
        const lines = buffer.split("\n");
        // last line might be incomplete, use it as starting point for the buffer
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (line) {
            const chunk = JSON.parse(line);
            if(chunk.data) snippets.push(...chunk.data);
          }
        }
      }
    }
  } catch (error) {
    throw new Error("Failed to fetch video stream. " + error);
  }
};


onMounted(async () => {
  try {
    await getVideoStream("oLIkRpKLH1Y", "tl");
  } catch (err) {
    console.error(err);
  }
});

onUnmounted(() => {
  cancelAnimationFrame(animationFrame);
});

const visibleLines = computed(() => {
  if (activeIndex.value !== -1) {
    return snippets.slice(
      activeIndex.value - (activeIndex.value % 3),
      activeIndex.value + (3 - activeIndex.value % 3)
    );
  }
  return [];
});
</script>
