<template>
  <div class="min-h-screen flex items-center justify-center bg-base-200 p-4">
    <div class="card bg-base-100 card-border border-base-300 w-full max-w-xl">
      <div class="card-body">
        <!-- Input + Button -->
        <div class="flex flex-col sm:flex-row gap-3">
          <input
            id="youtubeLink"
            v-model="youtubeLink"
            type="text"
            placeholder="Paste YouTube Link"
            class="w-full input input-neutral input-lg"
          />

          <div class="relative w-full sm:w-auto">
            <!-- Toggle dropdown on click -->
            <button
              @click="open = !open"
              class="btn btn-neutral sm:w-auto w-full btn-lg flex items-center justify-between"
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
              class="absolute z-10 bg-base-100 border rounded-lg w-full mt-1 shadow-lg sm:w-[200px]"
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

const youtubeLink = ref("");
const search = ref("");
const selectedLanguage = ref(null);
const open = ref(false);
const highlighted = ref(0);

const languages = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "zh", label: "Chinese" },
  { value: "ja", label: "Japanese" },
];

const filteredLanguages = computed(() => {
  if (!search.value) return languages;
  return languages.filter((l) =>
    l.label.toLowerCase().includes(search.value.toLowerCase())
  );
});

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

<style scoped>
/* Optional: smooth scroll on highlighted */
ul::-webkit-scrollbar {
  width: 6px;
}
ul::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}
</style>
