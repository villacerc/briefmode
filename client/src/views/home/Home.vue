<template>
  <div class="min-h-screen flex justify-center bg-base-100">
    <div class="w-full mt-30">
      <h1 class="text-accent-content text-5xl mb-2 text-center">
        YouTube Video AI Translator
      </h1>
      <h2 class="text-accent-content text-center mb-10 text-slate-400">
        Watch YouTube videos with accurate, context-aware translations.
      </h2>

      <!-- Main Form -->
      <div class="m-auto max-w-4xl p-8 shadow-sm rounded-xl bg-dictionary">
        <div class="flex gap-5 flex-wrap">
          <div class="flex-1 relative w-full md:flex-[3]">
            <span
              class="mui-icon text-xl absolute left-4 top-1/2 -translate-y-1/2 text-outline"
              data-icon="link"
              >link</span
            >
            <input
              type="text"
              v-model="youtubeLink"
              placeholder="Paste YouTube video URL here..."
              class="w-full p-5 pl-11 rounded-md border bg-base-100 border-gray-300 focus:outline-none focus-within:border-neutral"
            />
          </div>
          <!-- Custom Dropdown for Language Selection -->
          <div
            class="flex items-center w-full md:flex-[1] p-3 relative rounded-md border bg-base-100 border-gray-300 focus-within:border-neutral cursor-pointer"
            @click="open = true"
          >
            <span
              class="mui-icon text-xl absolute left-4 top-1/2 -translate-y-1/2"
            >
              translate
            </span>
            <div class="pl-8 pr-8">
              {{ selectedLanguage?.name || "Target Language" }}
            </div>
            <span
              class="mui-icon text-xl absolute right-4 pointer-events-none text-outline"
            >
              expand_more
            </span>
            <!-- Custom dropdown -->
            <div
              v-if="open"
              @click.stop
              class="absolute top-full mt-1 left-0 z-10 bg-base-100 border border-neutral rounded-md w-full shadow-lg overflow-hidden"
            >
              <div class="p-2">
                <input
                  type="text"
                  v-model="search"
                  placeholder="Search language"
                  ref="searchLanguageInput"
                  class="w-full p-2 rounded-md border border-neutral focus:outline-none focus-within:border-neutral"
                  @keydown.enter.prevent="selectHighlighted"
                />
              </div>
              <ul
                class="overflow-auto max-h-48"
                v-if="filteredLanguages.length"
              >
                <li
                  v-for="(lang, index) in filteredLanguages"
                  :key="lang.id"
                  :class="[
                    'px-4 py-2 cursor-pointer',
                    { 'bg-secondary text-base-content': index === highlighted },
                  ]"
                  @mousedown.prevent="selectLanguage(lang)"
                  @mouseover="highlighted = index"
                >
                  {{ lang.name }}
                </li>
              </ul>
            </div>
          </div>
        </div>
        <button
          @click="goToVideo"
          class="mt-5 cursor-pointer w-full bg-warning text-on-primary py-4 rounded-xl font-title-sm text-title-sm hover:bg-on-primary-container transition-all flex items-center justify-center gap-2 group"
        >
          Translate Video
          <span
            class="mui-icon group-hover:translate-x-1 transition-transform"
            data-icon="arrow_forward"
            >arrow_forward</span
          >
        </button>
        <div class="relative">
          <p
            :class="errorMessage ? 'visible' : 'invisible'"
            class="absolute left-1/2 -translate-x-1/2 mt-2 text-center text-error text-xs"
          >
            {{ errorMessage }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const youtubeLink = ref("");
const search = ref("");
const selectedLanguage = ref(null);
const searchLanguageInput = ref(null);
const open = ref(false);
const errorMessage = ref("");
const highlighted = ref(0);
const languages = ref([]);

onMounted(async () => {
  try {
    await fetchLanguages();
  } catch (err) {
    console.error(err);
  }
});

async function fetchLanguages() {
  try {
    const res = await fetch("http://localhost:8000/api/languages");
    const body = await res.json();
    if (body.data) {
      languages.value = body.data;
    }
  } catch (err) {
    console.error(err);
  }
}

watch(youtubeLink, () => {
  if (isValidYouTubeUrl()) errorMessage.value = "";
});

watch(open, async (newVal) => {
  if (newVal) {
    await nextTick();
    searchLanguageInput.value?.focus();
  }
});

const filteredLanguages = computed(() => {
  if (!search.value) return languages.value;
  return languages.value.filter((lang) =>
    lang.name.toLowerCase().startsWith(search.value.toLowerCase())
  );
});

function isValidYouTubeUrl() {
  if (!youtubeLink.value) return false;
  const regex =
    /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]{11}(&.*)?$/;
  return regex.test(youtubeLink.value);
}

function toggleDropdown() {
  if (youtubeLink.value && isValidYouTubeUrl()) {
    open.value = true;
    errorMessage.value = "";
  } else {
    open.value = false;
    errorMessage.value = "Please enter a valid URL";
  }
}

function goToVideo() {
  if (!selectedLanguage.value)
    return (errorMessage.value = "Please select a target language");
  if (!isValidYouTubeUrl())
    return (errorMessage.value = "Please enter a valid URL");

  const videoId = getYouTubeVideoId(youtubeLink.value);
  const lang_code = selectedLanguage.value.code;
  router.push({
    name: "Video",
    params: { id: videoId },
    query: { target_lang_code: lang_code },
  });
}

function getYouTubeVideoId(url) {
  const parsed = new URL(url);

  // Case 1: https://www.youtube.com/watch?v=ID
  if (parsed.hostname.includes("youtube.com")) {
    return parsed.searchParams.get("v");
  }

  // Case 2: https://youtu.be/ID
  if (parsed.hostname === "youtu.be") {
    return parsed.pathname.slice(1);
  }

  return null;
}

function selectLanguage(lang) {
  selectedLanguage.value = lang;
  search.value = lang.label;
  open.value = false;
  highlighted.value = 0;
}

function selectHighlighted() {
  const lang = filteredLanguages.value[highlighted.value];
  if (lang) selectLanguage(lang);
}

// Close dropdown when clicking outside
const clickOutsideHandler = (event) => {
  if (!event.target.closest(".relative")) open.value = false;
};
document.addEventListener("click", clickOutsideHandler);
</script>
