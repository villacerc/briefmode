<template>
  <div class="px-5 py-2 bg-dictionary">
    <h1 class="[font-family:'Inria',serif] text-2xl mb-1">Dictionary</h1>
    <div class="mb-4">
      <label
        class="input p-2 flex items-center gap-2 rounded-md transition focus-within:border-neutral focus-within:outline-none"
      >
        <input type="search" required class="flex-1 bg-transparent" />
        <i class="mui-icon text-2xl text-base-content/65">search</i>
      </label>
    </div>

    <div class="mb-4">
      <p class="[font-family:'Inria',serif] text-neutral text-3xl">Congruity</p>
      <div class="flex items-center">
        <p class="mr-5">con - gru - ity</p>
        <p class="mr-3">con - gru - ity</p>
        <button class="btn-circle inline-block">
          <i class="mui-icon-fill text-2xl text-neutral">volume_up</i>
        </button>
      </div>
    </div>

    <div class="mb-6">
      <h1 class="mb-3">Noun</h1>
      <div class="border-t border-gray-400 w-full mb-2"></div>
      <div class="mb-2">
        <p class="mb-5">The quality of being agreeable</p>
        <p class="mb-2 text-sm">EXAMPLE</p>
        <p class="bg-base-100 p-3 rounded-lg mb-2">
          東北は自然が豊かです。 東北は自然が豊かです。 東北は自然が豊かです。
          東北は自然が豊かです。
        </p>
        <p class="p-3">
          Tohoku is rich in nature. Tohoku is rich in nature. Tohoku is rich in
          nature. Tohoku is rich in nature.
        </p>
      </div>
    </div>

    <div class="mb-6">
      <h1 class="mb-3">Transcript Examples</h1>
      <div class="border-t border-gray-400 w-full mb-3"></div>
      <div class="mb-2">
        <p class="bg-base-100 p-3 rounded-lg mb-2">
          東北は自然が豊かです。 東北は自然が豊かです。 東北は自然が豊かです。
          東北は自然が豊かです。
        </p>
        <p class="p-3">
          Tohoku is rich in nature. Tohoku is rich in nature. Tohoku is rich in
          nature. Tohoku is rich in nature.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup></script>
