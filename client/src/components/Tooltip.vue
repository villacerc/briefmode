<template>
  <div
    class="relative inline-block group/tooltip"
    @mouseenter="checkPopupPosition"
  >
    <slot />

    <!-- Popup slot -->
    <div
      ref="popupEl"
      class="absolute z-1 left-1/2 -translate-x-1/2 opacity-0 scale-90 invisible group-hover/tooltip:visible group-hover/tooltip:opacity-100 group-hover/tooltip:scale-100 transition-opacity transition-transform duration-250 ease-out"
      :class="
        popupPosition === 'below'
          ? 'top-full origin-top'
          : 'bottom-full origin-bottom'
      "
    >
      <div :class="popupPosition === 'below' ? 'mt-2' : 'mb-2'">
        <slot name="tooltip-content" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const popupEl = ref<HTMLElement | null>(null);
const popupPosition = ref<"above" | "below">("below");

const checkPopupPosition = (event: MouseEvent) => {
  const span = event.currentTarget as HTMLElement;
  const popup = popupEl.value;
  if (!span || !popup) return;

  const spanRect = span.getBoundingClientRect();
  const popupRect = popup.getBoundingClientRect();
  const popupHeight = popupRect.height;

  popupPosition.value = spanRect.top < popupHeight + 70 ? "below" : "above";
};
</script>
