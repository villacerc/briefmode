<template>
  <div class="min-h-screen flex justify-center bg-base-100">
    <div class="w-full mt-30">
      <h1 class="text-accent-content text-4xl mb-2 text-center">
        YouTube Video Translator
      </h1>
      <h2 class="text-accent-content text-md mb-6 text-center">
        Understand YouTube videos from around the world!
      </h2>
      <div class="m-auto max-w-3xl p-2">
        <!-- Input + Button -->
        <div class="flex flex-col sm:flex-row gap-2 h-[70px] p-2">
          <div class="w-full">
            <input
              id="youtubeLink"
              v-model="youtubeLink"
              type="text"
              placeholder="Paste YouTube Link"
              class="w-full input input-neutral input-lg bg-gray-50"
            />
            <p v-if="showError" class="text-error text-xs mt-1">
              Please enter a valid URL
            </p>
          </div>
          <div class="relative w-full sm:w-auto">
            <!-- Toggle dropdown on click -->
            <button
              @click="toggleDropdown"
              :class="[
                'btn btn-neutral sm:w-auto w-full btn-lg flex items-center justify-between',
              ]"
            >
              Translate
              <!-- Solid triangle SVG -->
              <svg
                class="w-2 h-2 ml-2 transition-transform duration-200"
                viewBox="0 0 10 6"
                xmlns="http://www.w3.org/2000/svg"
              >
                <polygon points="0,0 10,0 5,6" fill="currentColor" />
              </svg>
            </button>
            <!-- Searchable dropdown -->
            <div
              v-if="open"
              class="absolute z-10 bg-base-100 border rounded-lg w-full mt-1 shadow-lg sm:w-[200px] overflow-hidden"
            >
              <div class="p-2">
                <input
                  type="text"
                  v-model="search"
                  placeholder="Search language"
                  class="w-full input input-xs"
                  @keydown.enter.prevent="selectHighlighted"
                />
              </div>

              <ul
                class="overflow-auto max-h-48"
                v-if="open && filteredLanguages.length"
              >
                <li
                  v-for="(lang, index) in filteredLanguages"
                  :key="lang.value"
                  :class="[
                    'px-4 py-2 cursor-pointer',
                    { 'bg-secondary text-base-content': index === highlighted },
                  ]"
                  @mousedown.prevent="selectLanguage(lang)"
                  @mouseover="highlighted = index"
                >
                  {{ lang.label }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const youtubeLink = ref("");
const search = ref("");
const selectedLanguage = ref(null);
const open = ref(false);
const showError = ref(false);
const highlighted = ref(0);

const languages = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "zh", label: "Chinese" },
  { value: "ja", label: "Japanese" },
];

watch(youtubeLink, () => {
  if (isValidYouTubeUrl()) showError.value = false;
});

const filteredLanguages = computed(() => {
  if (!search.value) return languages;
  return languages.filter((l) =>
    l.label.toLowerCase().includes(search.value.toLowerCase())
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
    open.value = !open.value;
    showError.value = false;
  } else {
    open.value = false;
    showError.value = true;
  }
}

function goToVideo(lang) {
  if (youtubeLink.value && lang) {
    const videoId = youtubeLink.value.split("v=")[1];
    const to_lang = lang.value;
    // Navigate to the video page with the selected language
    router.push({
      name: "Video",
      params: { id: videoId },
      query: { lang: to_lang },
    });
  }
}

function selectLanguage(lang) {
  selectedLanguage.value = lang;
  search.value = lang.label;
  open.value = false;
  highlighted.value = 0;
  goToVideo(lang);
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
