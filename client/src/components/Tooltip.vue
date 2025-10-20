<template>
  <div
    class="relative inline-block"
    @mouseenter="onTriggerEnter"
    @mouseleave="onTriggerLeave"
  >
    <slot />

    <!-- Teleport popup to body -->
    <Teleport to="body">
      <div
        v-if="showPopup"
        class="fixed z-[10]"
        :style="popupStyle"
        @mouseenter="onPopupEnter"
        @mouseleave="onPopupLeave"
      >
        <div ref="popupEl" :style="popupContentStyle">
          <slot name="tooltip-content" />
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";

const popupEl = ref<HTMLElement | null>(null);
const popupAbove = ref(true);
const showPopup = ref(false);
const triggerHovered = ref(false);
const popupHovered = ref(false);
const hideTimer = ref<number | null>(null);
const popupStyle = reactive({
  height: "auto",
  left: "0px",
  top: "0px",
  transform: "translate(-50%, 0)",
});
const popupContentStyle = reactive({
  marginTop: "0px",
});

// --- POSITIONING ---
const checkPopupPosition = (event: MouseEvent) => {
  const targetEl = event.currentTarget as HTMLElement;
  if (!targetEl) return;

  showPopup.value = true;

  requestAnimationFrame(() => {
    const popup = popupEl.value;
    if (!popup) return;

    const targetRect = targetEl.getBoundingClientRect();
    const popupRect = popup.getBoundingClientRect();

    const above = targetRect.top > popupRect.height + 10;
    popupAbove.value = above;

    popupStyle.height = `${popupRect.height + 10}px`;
    popupStyle.left = `${targetRect.left + targetRect.width / 2}px`;
    popupStyle.top = above
      ? `${targetRect.top - popupRect.height - 10}px`
      : `${targetRect.bottom}px`;
    popupContentStyle.marginTop = above ? "0" : "10px";
  });
};

// --- HOVER MANAGEMENT ---
function scheduleHide() {
  if (hideTimer.value) clearTimeout(hideTimer.value);
  hideTimer.value = window.setTimeout(() => {
    if (!triggerHovered.value && !popupHovered.value) {
      showPopup.value = false;
    }
  }, 1); // delay makes it smoother when moving between target and popup
}

function onTriggerEnter(event: MouseEvent) {
  triggerHovered.value = true;
  checkPopupPosition(event);
}

function onTriggerLeave() {
  triggerHovered.value = false;
  scheduleHide();
}

function onPopupEnter() {
  popupHovered.value = true;
  if (hideTimer.value) clearTimeout(hideTimer.value);
}

function onPopupLeave() {
  popupHovered.value = false;
  scheduleHide();
}
</script>
