<template>
  <div
    class="relative inline-block"
    @mouseenter="onTriggerEnter"
    @mouseleave="hidePopup"
  >
    <slot />

    <!-- Teleport popup to body -->
    <Teleport to="body">
      <div
        v-if="showPopup"
        class="fixed z-[10]"
        :style="popupStyle"
        @mouseenter="onPopupEnter"
        @mouseleave="hidePopup"
      >
        <div ref="popupEl" :style="popupContentStyle">
          <slot name="popup-content" />
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick } from "vue";

const popupEl = ref<HTMLElement | null>(null);
const popupAbove = ref(true);
const showPopup = ref(false);
const hideTimer = ref<number | null>(null);
const popupStyle = reactive({
  height: "auto",
  left: "0px",
  top: "0px",
  transform: "translate(-50%, 0)",
});
const popupContentStyle = reactive({
  marginTop: "0px",
  opacity: "1",
  transform: "scale(1)",
  transformOrigin: "center top",
  transition: "none",
});

const renderPopup = async (event: MouseEvent) => {
  const targetEl = event.currentTarget as HTMLElement;
  if (!targetEl) return;

  showPopup.value = true;

  await nextTick(); // wait for popup to render

  const popup = popupEl.value;
  if (!popup) return;

  const targetRect = targetEl.getBoundingClientRect();
  const popupRect = popup.getBoundingClientRect();
  const gap = 10; // gap between target and popup content

  const above = targetRect.top > popupRect.height + gap;
  popupAbove.value = above;

  popupStyle.height = `${popupRect.height + gap}px`;
  popupStyle.left = `${targetRect.left + targetRect.width / 2}px`;
  popupStyle.top = above
    ? `${targetRect.top - popupRect.height - gap}px`
    : `${targetRect.bottom}px`;
  popupContentStyle.marginTop = above ? "0" : `${gap}px`;
  popupContentStyle.transformOrigin = above ? "center bottom" : "center top";

  animatePopup();
};

function animatePopup() {
  popupContentStyle.opacity = "0";
  popupContentStyle.transform = "scale(0.95)";
  popupContentStyle.transition = "none";

  requestAnimationFrame(() => {
    popupContentStyle.transition =
      "opacity 0.2s ease-out, transform 0.2s ease-out";

    requestAnimationFrame(() => {
      popupContentStyle.opacity = "1";
      popupContentStyle.transform = "scale(1)";
    });
  });
}

function onTriggerEnter(event: MouseEvent) {
  if (hideTimer.value) clearTimeout(hideTimer.value);
  renderPopup(event);
}

function onPopupEnter() {
  if (hideTimer.value) clearTimeout(hideTimer.value);
}

function hidePopup() {
  // delay hiding popup
  if (hideTimer.value) clearTimeout(hideTimer.value);
  hideTimer.value = window.setTimeout(() => {
    showPopup.value = false;
  }, 1);
}
</script>
