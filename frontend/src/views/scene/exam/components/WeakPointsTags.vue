<template>
  <div class="weak-points-tags card exam-weak-points--warning-border">
    <h3 class="weak-points-tags__title">
      <el-icon><Aim /></el-icon>
      薄弱知识点
    </h3>

    <div class="weak-points-tags__cloud">
      <el-tooltip
        v-for="point in weakPoints"
        :key="point.id"
        :content="getTooltipContent(point.level)"
        placement="top"
      >
        <el-tag
          :type="tagType(point.level)"
          effect="dark"
          size="large"
          class="weak-points-tags__tag"
          :class="[`weak-points-tags__tag--${point.level}`]"
        >
          {{ levelIcon(point.level) }} {{ point.name }}
        </el-tag>
      </el-tooltip>
    </div>

    <!-- 图例 -->
    <div class="weak-points-tags__legend">
      <span class="weak-points-tags__legend-item">
        <span class="weak-points-tags__legend-dot weak-points-tags__legend-dot--critical"></span>
        严重薄弱
      </span>
      <span class="weak-points-tags__legend-item">
        <span class="weak-points-tags__legend-dot weak-points-tags__legend-dot--warning"></span>
        需要加强
      </span>
      <span class="weak-points-tags__legend-item">
        <span class="weak-points-tags__legend-dot weak-points-tags__legend-dot--caution"></span>
        基本掌握
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 薄弱知识点标签
 * 标签云布局，按 WeaknessLevel 着色（红/橙/黄）
 * 悬停展开详情（el-tooltip 显示严重程度说明）
 */
import { WeaknessLevel } from '../../types'
import type { WeakPoint } from '../../types'

interface Props {
  /** 薄弱知识点列表 */
  weakPoints: WeakPoint[]
}

defineProps<Props>()

/** 级别对应图标 */
function levelIcon(level: WeaknessLevel): string {
  const map: Record<WeaknessLevel, string> = {
    [WeaknessLevel.CRITICAL]: '🔴',
    [WeaknessLevel.WARNING]: '🟠',
    [WeaknessLevel.CAUTION]: '🟡',
  }
  return map[level] || ''
}

/** 级别对应 el-tag 类型 */
function tagType(level: WeaknessLevel): 'danger' | 'warning' | 'info' {
  const map: Record<WeaknessLevel, 'danger' | 'warning' | 'info'> = {
    [WeaknessLevel.CRITICAL]: 'danger',
    [WeaknessLevel.WARNING]: 'warning',
    [WeaknessLevel.CAUTION]: 'info',
  }
  return map[level] || 'info'
}

/** Tooltip 内容 */
function getTooltipContent(level: WeaknessLevel): string {
  const map: Record<WeaknessLevel, string> = {
    [WeaknessLevel.CRITICAL]: '严重薄弱：建议优先复习',
    [WeaknessLevel.WARNING]: '需要加强：建议针对性练习',
    [WeaknessLevel.CAUTION]: '基本掌握：建议定期回顾',
  }
  return map[level] || ''
}
</script>

<style lang="scss" scoped>
.exam-weak-points--warning-border {
  border: var(--scene-warning-border, 2px solid rgba(245, 124, 0, 0.3));
}

.weak-points-tags {
  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary, #303133);
    margin: 0 0 16px 0;
  }

  &__cloud {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 16px;
  }

  &__tag {
    cursor: default;
    transition: transform 0.2s ease, box-shadow 0.2s ease;

    &:hover {
      transform: scale(1.08);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }
  }

  &__legend {
    display: flex;
    gap: 20px;
    justify-content: center;
    font-size: 12px;
    color: var(--color-text-secondary, #909399);

    &-item {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    &-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      display: inline-block;

      &--critical {
        background: #F56C6C;
      }
      &--warning {
        background: #E6A23C;
      }
      &--caution {
        background: #909399;
      }
    }
  }
}
</style>
