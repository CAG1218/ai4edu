<template>
  <div class="link-info">
    <div class="link-info__header">
      <el-icon :size="16"><Connection /></el-icon>
      <span>关系详情</span>
    </div>
    <el-descriptions :column="1" border size="small">
      <el-descriptions-item label="起始节点">{{ link.source }}</el-descriptions-item>
      <el-descriptions-item label="目标节点">{{ link.target }}</el-descriptions-item>
      <el-descriptions-item label="关系类型">
        <el-tag size="small">{{ link.type }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item v-if="link.label" label="关系标签">{{ link.label }}</el-descriptions-item>
    </el-descriptions>
  </div>
</template>

<script setup lang="ts">
/**
 * AI4Edu 关系信息组件
 */
import { Connection } from '@element-plus/icons-vue'

interface GraphLink {
  source: string
  target: string
  type: string
  label?: string
}

defineProps<{
  link: GraphLink
}>()
</script>

<style lang="scss" scoped>
.link-info {
  &__header {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 10px;
    font-weight: 600;
    color: var(--color-text-primary);
  }
}
</style>
