<template>
  <el-card shadow="hover" class="node-card" @click="$emit('click', node)">
    <div class="node-card__header">
      <span class="node-card__dot" :style="{ background: subjectColor }" />
      <span class="node-card__name">{{ node.name || node.id }}</span>
    </div>
    <p v-if="node.description" class="node-card__desc">{{ node.description }}</p>
    <div class="node-card__footer">
      <el-tag v-if="node.subject" size="small" type="info">{{ node.subject }}</el-tag>
    </div>
  </el-card>
</template>

<script setup lang="ts">
/**
 * AI4Edu 知识点卡片组件
 */
import { computed } from 'vue'

interface KnowledgeNode {
  id: string
  name?: string
  subject?: string
  description?: string
  [key: string]: unknown
}

const props = defineProps<{
  node: KnowledgeNode
}>()

defineEmits<{
  (e: 'click', node: KnowledgeNode): void
}>()

const subjectColorMap: Record<string, string> = {
  math: '#1976D2',
  physics: '#F57C00',
  chemistry: '#4CAF50',
  biology: '#388E3C',
  cs: '#7B1FA2',
  chinese: '#D32F2F',
  english: '#00796B',
  history: '#5D4037',
  geography: '#0288D1',
  politics: '#C62828',
  pe: '#FF6F00',
  art: '#AD1457',
}

const subjectColor = computed(() => subjectColorMap[props.node.subject || ''] || '#5B8FF9')
</script>

<style lang="scss" scoped>
.node-card {
  cursor: pointer;
  transition: transform 0.15s ease;

  &:hover {
    transform: translateY(-2px);
  }

  &__header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }

  &__dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  &__name {
    font-weight: 600;
    font-size: 15px;
    color: var(--color-text-primary);
  }

  &__desc {
    font-size: 13px;
    color: var(--color-text-secondary);
    margin: 4px 0 8px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  &__footer {
    display: flex;
    gap: 6px;
  }
}
</style>
