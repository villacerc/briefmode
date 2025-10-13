<template>
  <svg
    className="h-[1em] opacity-50"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    :class="svgClass"
  >
    <g
      strokeLinejoin="round"
      strokeLinecap="round"
      strokeWidth="2.5"
      fill="none"
      stroke="currentColor"
    >
      <circle cx="11" cy="11" r="8"></circle>
      <path d="m21 21-4.3-4.3"></path>
    </g>
  </svg>
</template>

<script setup lang="ts">
import { computed } from "vue";
interface Props {
  class?: string | string[];
}
const props = defineProps<Props>();
const svgClass = computed(() => ["w-5 h-5", props.class]);
</script>
