<template>
  <div class="h-screen bg-base-300">
    <Navbar />
    <router-view></router-view>
  </div>
</template>

<script setup>
import Navbar from "./components/Navbar.vue";
document.body.classList.add("hide-scrollbar");
</script>
