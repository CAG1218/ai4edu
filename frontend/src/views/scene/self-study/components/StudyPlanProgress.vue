<template>
  <div class="study-plan-progress card">
    <div class="study-plan-progress__header">
      <h3 class="study-plan-progress__title">
        <el-icon><List /></el-icon>
        今日学习计划
      </h3>
      <span class="study-plan-progress__count">已完成 {{ completedCount }}/{{ tasks.length }}</span>
    </div>

    <!-- 进度条 -->
    <el-progress
      :percentage="progressPercentage"
      :color="progressColor"
      :stroke-width="10"
      class="study-plan-progress__bar"
    />

    <!-- 任务列表 -->
    <div class="study-plan-progress__tasks">
      <div
        v-for="task in tasks"
        :key="task.id"
        class="study-plan-progress__task"
        :class="{ 'study-plan-progress__task--done': task.completed }"
        @click="emit('toggle', task)"
      >
        <el-icon class="study-plan-progress__task-check" :color="task.completed ? '#388E3C' : '#c0c4cc'">
          <CircleCheck v-if="task.completed" />
          <Sugar v-else />
        </el-icon>
        <span class="study-plan-progress__task-title">{{ task.title }}</span>
        <el-tag :type="priorityTagType(task.priority)" size="small" effect="plain">
          {{ priorityLabel(task.priority) }}
        </el-tag>
        <span class="study-plan-progress__task-subject">{{ task.subject }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 学习计划进度
 * 进度条 + 任务列表，点击任务可切换完成状态
 */
import { computed } from 'vue'
import type { StudyTask } from '../../types'

interface Props {
  /** 学习任务列表 */
  tasks: StudyTask[]
}

interface Emits {
  /** 点击任务切换完成状态 */
  (e: 'toggle', task: StudyTask): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

/** 已完成任务数 */
const completedCount = computed(() => props.tasks.filter(t => t.completed).length)

/** 进度百分比 */
const progressPercentage = computed(() => {
  if (props.tasks.length === 0) return 0
  return Math.round((completedCount.value / props.tasks.length) * 100)
})

/** 进度条颜色（随进度变化） */
const progressColor = computed(() => {
  if (progressPercentage.value < 34) return '#F57C00'
  if (progressPercentage.value < 67) return '#1976D2'
  return '#388E3C'
})

/** 优先级标签文字 */
function priorityLabel(priority: StudyTask['priority']): string {
  const map = { high: '高', medium: '中', low: '低' }
  return map[priority] || '中'
}

/** 优先级标签类型 */
function priorityTagType(priority: StudyTask['priority']): 'danger' | 'warning' | 'info' {
  const map = { high: 'danger', medium: 'warning', low: 'info' } as const
  return map[priority] || 'info'
}
</script>

<style lang="scss" scoped>
.study-plan-progress {
  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary, #303133);
    margin: 0;
  }

  &__count {
    font-size: 13px;
    color: var(--color-text-secondary, #606266);
    font-weight: 500;
  }

  &__bar {
    margin-bottom: 16px;
  }

  &__tasks {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  &__task {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 8px;
    background: #f5f7fa;
    cursor: pointer;
    transition: background 0.2s ease;

    &:hover {
      background: #ecf5ff;
    }

    &--done {
      opacity: 0.6;

      .study-plan-progress__task-title {
        text-decoration: line-through;
      }
    }

    &-check {
      font-size: 18px;
      flex-shrink: 0;
    }

    &-title {
      flex: 1;
      font-size: 14px;
      color: var(--color-text-primary, #303133);
    }

    &-subject {
      font-size: 12px;
      color: var(--color-text-secondary, #909399);
      white-space: nowrap;
    }
  }
}
</style>
