<template>
  <div class="h-screen">
    <div
      class="w-full p-4 grid grid-cols-1 [@media(min-width:1016px)]:grid-cols-[2fr_1fr] [@media(min-width:1016px)]:max-w-[1200px] gap-4 m-auto"
    >
      <!-- First column -->
      <div class="border">
        <div class="border aspect-[21/9]">Column 1 content (16:9)</div>
      </div>

      <!-- Second column -->
      <div class="border">
        <div class="border h-[500px]">Column 2 content</div>
      </div>
    </div>
  </div>
</template>
