<template>
  <div>
    <component
      :is="VideoLayout1"
      :visible-lines="visibleLines"
      :active-index="activeIndex"
      :is-dragging="isDragging"
      @ready="onReady"
      @update:active-index="activeIndex = $event"
    />
  </div>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router";
import { ref, reactive, onMounted, onUnmounted, computed } from "vue";
import VideoLayout1 from "../components/VideoLayout1.vue";

const route = useRoute();

type TranslatedSnippet = {
  text: string;
  translation: string;
  start: number;
  end: number;
  duration: number;
};

// A ref in Vue 3 is reactive (good for primitives). Whenever its .value changes,
// Vue automatically re-renders any part of the template or computed properties that depend on it.
const player = ref<any>(null);
const activeIndex = ref<number>(-1);
const snippets = reactive<TranslatedSnippet[]>([]);
const isDragging = ref(false);
const draggableBox = ref<HTMLElement | null>(null);

let animationFrame: number;

onMounted(async () => {
  const el = draggableBox.value;
  let offsetX = 0,
    offsetY = 0;

  if (el) {
    el.addEventListener("mousedown", (e) => {
      isDragging.value = true;
      offsetX = e.clientX - el.offsetLeft;
      offsetY = e.clientY - el.offsetTop;
      document.body.style.userSelect = "none";
    });

    document.addEventListener("mousemove", (e) => {
      if (!isDragging.value) return;
      el.style.left = e.clientX - offsetX + "px";
      el.style.top = e.clientY - offsetY + "px";
    });

    document.addEventListener("mouseup", () => {
      isDragging.value = false;
      document.body.style.userSelect = "";
    });
  }

  try {
    await fetchVideoStream(
      route.params.id as string,
      route.query.lang as string
    );
  } catch (err) {
    // TODO: redirect to error page
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
      activeIndex.value + (3 - (activeIndex.value % 3))
    );
  }
  return [];
});

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

const fetchVideoStream = async (source_id: string, lang: string) => {
  try {
    const res = await fetch(
      `http://localhost:8000/api/video/${source_id}?lang=${lang}`
    );
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
        // lines.pop() mutates the array
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (line) {
            const chunk = JSON.parse(line);
            if (chunk.data) snippets.push(...chunk.data);
          }
        }
      }
    }
  } catch (error) {
    throw new Error("Failed to fetch video stream. " + error);
  }
};
</script>
