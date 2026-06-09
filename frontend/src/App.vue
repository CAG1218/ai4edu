<template>
  <OfflineAlert />
  <router-view />
</template>

<script setup lang="ts">
/**
 * AI4Edu 根组件
 * 包含离线提示和路由视图，所有页面通过 router-view 渲染
 */
import OfflineAlert from '@/components/common/OfflineAlert.vue'
</script>

<style lang="scss">
#app {
  width: 100%;
  height: 100%;
}
</style>
