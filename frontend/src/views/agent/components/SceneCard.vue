<template>
  <div class="scene-card" @click="$emit('select', scene)">
    <div class="scene-card__icon">
      <el-icon :size="32">
        <component :is="iconComponent" />
      </el-icon>
    </div>
    <div class="scene-card__body">
      <h3 class="scene-card__title">{{ scene.name }}</h3>
      <p class="scene-card__description">{{ scene.description }}</p>
    </div>
    <div class="scene-card__footer">
      <el-button
        type="primary"
        size="small"
        :loading="loading"
        @click.stop="$emit('select', scene)"
      >
        开始对话
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 场景卡片组件
 * 展示场景图标、标题、描述和 CTA 按钮
 */
import { computed } from 'vue'
import { Reading, Search, Edit, Trophy } from '@element-plus/icons-vue'
import type { ScenePreset } from '@/services/agent'

const props = defineProps<{
  scene: ScenePreset
  loading?: boolean
}>()

defineEmits<{
  (e: 'select', scene: ScenePreset): void
}>()

/** 图标组件映射 */
const iconComponent = computed(() => {
  const iconMap: Record<string, unknown> = {
    Reading,
    Search,
    Edit,
    Trophy,
  }
  return iconMap[props.scene.icon] || Reading
})
</script>

<style lang="scss" scoped>
.scene-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 28px 20px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid #eee;
  cursor: pointer;
  transition: all 0.3s ease;
  height: 100%;

  &:hover {
    border-color: #1976d2;
    box-shadow: 0 4px 20px rgba(25, 118, 210, 0.12);
    transform: translateY(-2px);
  }

  &__icon {
    width: 64px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: linear-gradient(135deg, #e3f2fd, #bbdefb);
    color: #1976d2;
    margin-bottom: 16px;
  }

  &__body {
    margin-bottom: 20px;
  }

  &__title {
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 8px 0;
    color: #1a1a2e;
  }

  &__description {
    font-size: 13px;
    color: #888;
    line-height: 1.5;
    margin: 0;
  }

  &__footer {
    margin-top: auto;
  }
}
</style>
