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
      <el-descriptions-item v-if="link.is_cross !== undefined" label="关系范围">
        <el-tag v-if="link.is_cross" size="small" type="warning">跨学科</el-tag>
        <el-tag v-else size="small" type="success">同学科</el-tag>
      </el-descriptions-item>
      <el-descriptions-item v-if="link.strength !== undefined" label="关系强度">
        <div class="link-info__strength">
          <el-progress
            :percentage="Math.round(link.strength * 100)"
            :stroke-width="14"
            :color="strengthColor"
            :show-text="false"
            style="flex: 1"
          />
          <el-tag
            size="small"
            :type="strengthTagType"
            effect="dark"
            class="link-info__strength-label"
          >
            {{ link.strength_label }} ({{ link.strength.toFixed(2) }})
          </el-tag>
        </div>
      </el-descriptions-item>
    </el-descriptions>
  </div>
</template>

<script setup lang="ts">
/**
 * AI4EDU 关系信息组件
 * 支持关系强度展示和跨学科标记
 */
import { computed } from 'vue'
import { Connection } from '@element-plus/icons-vue'

interface GraphLink {
  source: string
  target: string
  type: string
  label?: string
  strength?: number
  strength_label?: '强' | '中' | '弱'
  is_cross?: boolean
}

const props = defineProps<{
  link: GraphLink
}>()

const strengthColor = computed(() => {
  if (!props.link.strength) return '#909399'
  if (props.link.strength >= 0.7) return '#67C23A'
  if (props.link.strength >= 0.4) return '#E6A23C'
  return '#F56C6C'
})

const strengthTagType = computed<'success' | 'warning' | 'danger'>(() => {
  if (!props.link.strength) return 'warning' as never
  if (props.link.strength >= 0.7) return 'success'
  if (props.link.strength >= 0.4) return 'warning'
  return 'danger'
})
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

  &__strength {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
  }

  &__strength-label {
    flex-shrink: 0;
    white-space: nowrap;
  }
}
</style>
