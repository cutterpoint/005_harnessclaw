<script setup lang="ts">
import Sidebar from './Sidebar.vue'
import TopBar from './TopBar.vue'
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-base-950">
    <Sidebar />
    <div class="flex flex-1 flex-col overflow-hidden">
      <TopBar />
      <main class="flex-1 overflow-auto">
        <router-view />
      </main>
    </div>
  </div>
</template>
