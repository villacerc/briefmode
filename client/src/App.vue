<template>
  <div class="min-h-screen flex items-center justify-center bg-base-200 p-4">
    <div class="card bg-base-100 card-border border-base-300 w-full max-w-lg">
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
          <button class="btn btn-dash btn-neutral sm:w-auto w-full btn-lg">
            Translate
          </button>
        </div>
        
        <!-- Dropdown -->
         <div class="w-full form-control flex flex-col sm:flex-row sm:w-[200px] gap-2">
    <label class="label">
      <span class="label-text text-xs">Translate to</span>
    </label>

    <!-- Search input -->
    <div class="relative">
        <input
      type="text"
      v-model="search"
      placeholder="Select language"
      @focus="open = true"
      class="w-full input input-primary input-xs"
      @keydown.down.prevent="highlightNext"
      @keydown.up.prevent="highlightPrev"
      @keydown.enter.prevent="selectHighlighted"
    />

    <!-- Dropdown -->
    <ul
      v-if="open && filteredLanguages.length"
      class="absolute z-10 bg-base-100 border rounded-lg w-full t-5 max-h-48 overflow-auto shadow-lg"
    >
      <li
        v-for="(lang, index) in filteredLanguages"
        :key="lang.value"
        :class="['px-4 py-2 cursor-pointer', { 'bg-secondary text-base-content': index === highlighted }]"
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
</template>


<script setup>
import { ref, computed, watch } from "vue";

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

// Show all languages if empty or filter if typing
const filteredLanguages = computed(() => {
  if (!search.value) return languages; // show all when input empty
  return languages.filter((l) =>
    l.label.toLowerCase().includes(search.value.toLowerCase())
  );
});

// Watch input changes
watch(search, (newValue) => {
  open.value = true; // always open on input change
  highlighted.value = 0;
});

function selectLanguage(lang) {
  selectedLanguage.value = lang;
  search.value = lang.label;
  open.value = false;
  highlighted.value = 0;
}

function highlightNext() {
  if (highlighted.value < filteredLanguages.value.length - 1) highlighted.value++;
}

function highlightPrev() {
  if (highlighted.value > 0) highlighted.value--;
}

function selectHighlighted() {
  const lang = filteredLanguages.value[highlighted.value];
  if (lang) selectLanguage(lang);
}

// Close dropdown when clicking outside
const clickOutsideHandler = (event) => {
  if (!event.target.closest(".form-control")) open.value = false;
};
document.addEventListener("click", clickOutsideHandler);
</script>

<style scoped>
/* Optional: smooth scroll on highlighted */
ul::-webkit-scrollbar {
  width: 6px;
}
ul::-webkit-scrollbar-thumb {
  background-color: rgba(0,0,0,0.2);
  border-radius: 3px;
}
</style>
