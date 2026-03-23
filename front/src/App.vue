<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue';

import { useAuth } from '@/composables/useAuth';

const { initAuth } = useAuth();

onMounted(() => {
  initAuth();
});
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
</style>
