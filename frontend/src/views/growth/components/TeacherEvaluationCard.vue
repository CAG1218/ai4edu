<template>
  <el-card shadow="hover" class="evaluation-card">
    <div class="evaluation-card__header">
      <div class="evaluation-card__teacher">
        <el-avatar :size="36" class="evaluation-card__avatar">
          {{ evaluation.teacher_name?.charAt(0) || '?' }}
        </el-avatar>
        <div class="evaluation-card__info">
          <span class="evaluation-card__name">{{ evaluation.teacher_name }}</span>
          <span class="evaluation-card__time">{{ formatTime(evaluation.created_at) }}</span>
        </div>
      </div>
      <el-tag :type="evaluationTypeTag" size="small" effect="light">
        {{ evaluationTypeLabel }}
      </el-tag>
    </div>

    <div class="evaluation-card__rating">
      <el-rate v-model="evaluation.rating" disabled show-score :max="5" />
      <span v-if="evaluation.course_name" class="evaluation-card__course">
        <el-icon><Reading /></el-icon>
        {{ evaluation.course_name }}
      </span>
    </div>

    <p class="evaluation-card__content">{{ evaluation.content }}</p>

    <div v-if="evaluation.suggestion" class="evaluation-card__suggestion">
      <el-icon><ChatLineSquare /></el-icon>
      <span>{{ evaluation.suggestion }}</span>
    </div>

    <div v-if="editable" class="evaluation-card__actions">
      <el-button size="small" text type="primary" @click="$emit('edit', evaluation)">
        <el-icon><Edit /></el-icon>
        编辑
      </el-button>
      <el-popconfirm
        title="确定删除该评价吗？"
        confirm-button-text="删除"
        cancel-button-text="取消"
        @confirm="$emit('delete', evaluation.id)"
      >
        <template #reference>
          <el-button size="small" text type="danger">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </template>
      </el-popconfirm>
    </div>
  </el-card>
</template>

<script setup lang="ts">
/**
 * 教师评价卡片组件
 * 展示单条教师评价，支持编辑和删除操作
 */
import { computed } from 'vue'
import { Reading, ChatLineSquare, Edit, Delete } from '@element-plus/icons-vue'
import type { EvaluationItem } from '@/services/growth'

const props = defineProps<{
  evaluation: EvaluationItem
  editable: boolean
}>()

defineEmits<{
  edit: [evaluation: EvaluationItem]
  delete: [evaluationId: number]
}>()

/** 评价类型标签文字 */
const evaluationTypeLabel = computed(() => {
  const map: Record<string, string> = {
    overall: '综合评价',
    academic: '学业表现',
    attitude: '学习态度',
    improvement: '进步评价',
  }
  return map[props.evaluation.evaluation_type] || props.evaluation.evaluation_type
})

/** 评价类型 tag 样式 */
const evaluationTypeTag = computed<'' | 'success' | 'warning' | 'danger' | 'info'>(() => {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    overall: '',
    academic: 'success',
    attitude: 'warning',
    improvement: 'danger',
  }
  return map[props.evaluation.evaluation_type] || 'info'
})

/** 格式化时间 */
function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style lang="scss" scoped>
.evaluation-card {
  margin-bottom: 16px;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  &__teacher {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  &__avatar {
    background-color: #409eff;
    color: #fff;
    font-weight: 600;
  }

  &__info {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  &__name {
    font-weight: 600;
    font-size: 14px;
    color: #303133;
  }

  &__time {
    font-size: 12px;
    color: #909399;
  }

  &__rating {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 12px;
  }

  &__course {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    color: #606266;
  }

  &__content {
    margin: 0 0 12px;
    font-size: 14px;
    color: #303133;
    line-height: 1.7;
  }

  &__suggestion {
    display: flex;
    gap: 6px;
    padding: 10px 12px;
    background-color: #f5f7fa;
    border-radius: 6px;
    font-size: 13px;
    color: #606266;
    line-height: 1.6;

    .el-icon {
      color: #e6a23c;
      flex-shrink: 0;
      margin-top: 2px;
    }
  }

  &__actions {
    display: flex;
    gap: 4px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #f0f0f0;
  }
}
</style>
