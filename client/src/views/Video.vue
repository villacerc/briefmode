<template>
  <div class="my-10 mx-15">
    <!-- Overlay -->
    <div v-if="isDragging" class="fixed inset-0 z-50 cursor-grabbing"></div>

    <h1 class="text-xl font-medium mb-5 text-accent-content text-center">
      How I Went From Broke To Millionaire in 24 Months
    </h1>
    <div class="youtube-layout">
      <div class="youtube-primary">
        <div
          ref="videoContainer"
          :class="[
            'overflow-hidden',
            isFullscreen
              ? 'fixed inset-0 w-screen h-screen'
              : 'youtube-player-container rounded-xl',
          ]"
        >
          <youtube
            ref="youtubePlayer"
            src="https://www.youtube.com/watch?v=qzzweIQoIOU"
            width="100%"
            height="100%"
            :style="{ width: '100%', height: '100%' }"
            @ready="onReady"
          />
        </div>

        <div
          v-if="!isFullscreen"
          class="text-center relative group text-xl mt-2 px-5 py-2 bg-base-200 border border-base-300 rounded-xl hover:pt-8"
        >
          <div class="absolute top-2 right-2 hidden group-hover:block">
            <button
              @click="isFullscreen = true"
              class="cursor-pointer text-neutral transition-scale transform hover:scale-110 duration-200"
            >
              <FullScreenIcon />
            </button>
          </div>
          <span v-for="(line, i) in visibleLines" :key="i">
            <span v-for="(part, j) in line.snippet_words" :key="j">
              {{ part.text }}
              <span v-if="languageUsesSpaces(line.transcript_language)">
                {{ " " }}
              </span>
            </span>
          </span>
        </div>
        <div
          v-if="!isFullscreen"
          class="text-center relative group text-xl mt-2 px-5 py-2 border border-base-300 rounded-xl hover:pt-8"
        >
          <div class="absolute top-2 right-2 hidden group-hover:block">
            <button
              @click="isFullscreen = true"
              class="cursor-pointer text-neutral transition-scale transform hover:scale-110 duration-200"
            >
              <FullScreenIcon />
            </button>
          </div>
          <span v-for="(line, i) in visibleLines" :key="i">
            {{ line.translation }}
            <span v-if="languageUsesSpaces(line.translation_language)">
              {{ " " }}
            </span>
          </span>
        </div>
        <div class="mt-[10px] p-[10px]">More Content</div>
      </div>

      <!-- Floating Transcript -->
      <div
        ref="draggableBox"
        v-show="isFullscreen"
        class="group p-2 bg-black/70 min-h-[2rem] max-h-fit mx-5 fixed rounded-xl bottom-4 w-[calc(100vw-2rem)] text-2xl hover:pt-5 hover:outline hover:outline-white active:outline active:outline-white cursor-grab"
        :class="[isDragging ? 'pt-5' : '']"
      >
        <button
          class="absolute right-2 top-2 text-white cursor-pointer transition-scale transform hover:scale-90 duration-200"
          :class="[isDragging ? 'block' : 'hidden group-hover:block']"
          @click="isFullscreen = false"
          @mousedown.stop
        >
          <DefaultScreenIcon />
        </button>

        <div>
          <span
            v-if="isFullscreen"
            class="text-white"
            v-for="(line, idx) in visibleLines"
            :key="idx"
          >
            <span
              :class="
                activeIndex !== -1 && idx === activeIndex % 3
                  ? 'text-secondary'
                  : ''
              "
            >
              {{ line.translation }}
            </span>
            {{ " " }}
          </span>
        </div>
      </div>

      <div
        v-if="!isFullscreen"
        class="youtube-sidebar border border-base-300 rounded-xl"
      >
        <div class="h-[500px]">
          <div class="flex p-2 space-x-2">
            <button class="btn btn-neutral btn-sm rounded-lg">
              Transcript
            </button>
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
import { useRoute } from "vue-router";
import { ref, reactive, onMounted, onUnmounted, computed } from "vue";
import type { TranslatedSnippet } from "../types";
import FullScreenIcon from "../icons/FullScreen.vue";
import DefaultScreenIcon from "../icons/DefaultScreen.vue";
import YouTube from "vue3-youtube";

const route = useRoute();

// A ref in Vue 3 is reactive (good for primitives). Whenever its .value changes,
// Vue automatically re-renders any part of the template or computed properties that depend on it.
const player = ref<any>(null);
const activeIndex = ref<number>(-1);
const snippets = reactive<TranslatedSnippet[]>([]);
const isDragging = ref(false);
const draggableBox = ref<HTMLElement | null>(null);
const isFullscreen = ref(false);

const youtube = YouTube;
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

      // Calculate new position
      let newLeft = e.clientX - offsetX;
      let newTop = e.clientY - offsetY;

      // Clamp so it stays in viewport
      const maxLeft = window.innerWidth - el.offsetWidth;
      const maxTop = window.innerHeight - el.offsetHeight;

      newLeft = Math.max(0, Math.min(newLeft, maxLeft));
      newTop = Math.max(0, Math.min(newTop, maxTop));

      el.style.left = newLeft + "px";
      el.style.top = newTop + "px";
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

const isAnnotation = (text: string) => /^\s*[\[\(].+[\]\)]\s*$/u.test(text);

const visibleLines = computed<TranslatedSnippet[]>(() => {
  if (activeIndex.value === -1) return [];

  const snippet = snippets[activeIndex.value];

  if (isAnnotation(snippet.text)) {
    // Show annotation by itself
    return [snippet];
  }

  const groupSize = 3;
  const groupStart = Math.floor(activeIndex.value / groupSize) * groupSize;
  const groupEnd = groupStart + groupSize;

  let group: TranslatedSnippet[] = [];
  for (let i = groupEnd - 1; i >= groupStart && i >= 0; i--) {
    const s = snippets[i];
    if (isAnnotation(s.text) && i < activeIndex.value) {
      // stop when hitting annotation after normal text
      break;
    } else if (isAnnotation(s.text)) {
      group = [];
      continue;
    }
    group.unshift(s);
  }

  return group;
});

const tick = () => {
  if (player.value) {
    const time = player.value.getCurrentTime();

    const idx = snippets.findIndex(
      (line) => time >= line.start && time < line.end
    );
    activeIndex.value = idx;
    console.log(activeIndex.value);
  }
  animationFrame = requestAnimationFrame(tick);
};

// List of languages that do not use spaces between words
const noSpaceLanguages = ["ja", "zh", "th", "lo", "km", "my", "bo", "mn"];

const languageUsesSpaces = (langCode: string) => {
  return !noSpaceLanguages.includes(langCode);
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
