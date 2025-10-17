<template>
  <div class="h-full">
    <div class="p-2">
      <label className="input p-2">
        <input type="search" required placeholder="Search" />
      </label>
    </div>

    <div class="px-5 pb-4">
      <p class="text-warning">東北 touhoku</p>
      <p>North, Northeast, Northeastern</p>
    </div>

    <div v-for="n in 5">
      <h1 class="pl-5 bg-base-100">Noun</h1>
      <div class="px-5 py-2">
        <p>A region in the northeastern part of Japan's main island, Honshu.</p>
        <p class="mt-2">Example:</p>
        <p>東北は自然が豊かです。</p>
        <p>Tohoku is rich in nature.</p>
      </div>
    </div>

    <br />
    <br />
  </div>
</template>

<script setup></script>
