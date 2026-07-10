<template>
  <el-row :gutter="16" class="scene-stat-card">
    <el-col
      v-for="stat in stats"
      :key="stat.label"
      :xs="12"
      :sm="6"
    >
      <div class="scene-stat-card__item">
        <el-icon :size="28" :style="{ color: stat.color }" class="scene-stat-card__icon">
          <component :is="stat.icon" />
        </el-icon>
        <div class="scene-stat-card__info">
          <span class="scene-stat-card__value">{{ stat.value }}</span>
          <span class="scene-stat-card__label">{{ stat.label }}</span>
        </div>
      </div>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
/**
 * 统计卡片（跨场景共享组件）
 * 接收 StatItem[] 数组，响应式布局渲染统计项
 * 各场景仪表盘通过传入不同的 stats 数据实现差异化统计展示
 */
import type { StatItem } from '../types'

interface Props {
  /** 统计项数组，最多 4 个 */
  stats: StatItem[]
}

defineProps<Props>()
</script>

<style lang="scss" scoped>
.scene-stat-card {
  margin-bottom: var(--spacing-lg, 16px);

  &__item {
    display: flex;
    align-items: center;
    gap: var(--spacing-md, 12px);
    padding: 16px;
    background: var(--el-bg-color, #fff);
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    margin-bottom: var(--spacing-md, 12px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }
  }

  &__icon {
    flex-shrink: 0;
  }

  &__info {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  &__value {
    font-size: 24px;
    font-weight: 700;
    color: var(--color-text-primary, #303133);
    line-height: 1.2;
  }

  &__label {
    font-size: 12px;
    color: var(--color-text-secondary, #909399);
    margin-top: 2px;
  }
}
</style>
