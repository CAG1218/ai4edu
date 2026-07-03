<template>
  <div v-if="visibleBadges.length > 0" class="context-badges">
    <span class="context-badges__label">附加上下文:</span>
    <el-tag
      v-for="badge in visibleBadges"
      :key="badge.key"
      :type="badge.type"
      size="small"
      effect="light"
    >
      {{ badge.icon }} {{ badge.label }}({{ badge.count }})
    </el-tag>
  </div>
</template>

<script setup lang="ts">
/**
 * 上下文标签组件
 * 展示已注入的学习资源上下文数量（笔记/资源/图谱/方法）
 * N=0 时不显示该标签
 */
import { computed } from 'vue'
import type { ContextSummary } from '@/services/agent'

const props = defineProps<{
  summary: ContextSummary | null
}>()

interface Badge {
  key: string
  label: string
  icon: string
  count: number
  type: 'primary' | 'success' | 'warning' | 'info' | 'danger'
}

/** 可见的标签列表（count > 0 才显示） */
const visibleBadges = computed<Badge[]>(() => {
  const summary = props.summary
  if (!summary) return []
  const badges: Badge[] = [
    {
      key: 'notes',
      label: '笔记',
      icon: '📎',
      count: summary.notes_count || 0,
      type: 'info',
    },
    {
      key: 'resources',
      label: '资源',
      icon: '📄',
      count: summary.resources_count || 0,
      type: 'primary',
    },
    {
      key: 'graph',
      label: '图谱',
      icon: '🕸️',
      count: summary.graph_nodes_count || 0,
      type: 'success',
    },
    {
      key: 'methods',
      label: '方法',
      icon: '👨‍🏫',
      count: summary.teacher_methods_count || 0,
      type: 'warning',
    },
  ]
  return badges.filter((b) => b.count > 0)
})
</script>

<style lang="scss" scoped>
.context-badges {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 8px;

  &__label {
    font-size: 12px;
    color: #888;
  }
}
</style>
