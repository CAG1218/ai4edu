<template>
  <div class="current-course-card card" :class="{ 'current-course-card--active': course }">
    <div v-if="course" class="current-course-card__content">
      <div class="current-course-card__header">
        <el-tag type="success" effect="dark" size="small" class="current-course-card__status">
          <el-icon class="current-course-card__status-icon"><VideoPlay /></el-icon>
          进行中
        </el-tag>
        <h3 class="current-course-card__name">{{ course.name }}</h3>
      </div>
      <div class="current-course-card__meta">
        <span class="current-course-card__time">
          <el-icon><Clock /></el-icon>
          {{ course.startTime }} - {{ course.endTime }}
        </span>
        <span class="current-course-card__location">
          <el-icon><Location /></el-icon>
          {{ course.location }}
        </span>
        <span class="current-course-card__teacher">
          <el-icon><User /></el-icon>
          {{ course.teacher }}
        </span>
      </div>
      <div class="current-course-card__actions">
        <el-button type="primary" @click="emit('action', 'notes')">
          <el-icon><EditPen /></el-icon>
          做笔记
        </el-button>
        <el-button type="success" @click="emit('action', 'agent')">
          <el-icon><ChatLineSquare /></el-icon>
          课堂互动
        </el-button>
        <el-button type="info" @click="emit('action', 'resources')">
          <el-icon><Folder /></el-icon>
          资料
        </el-button>
      </div>
    </div>

    <!-- 无进行中课程时的空状态 -->
    <div v-else class="current-course-card__empty">
      <el-icon :size="40" color="#c0c4cc"><Coffee /></el-icon>
      <p class="current-course-card__empty-text">当前没有进行中的课程</p>
      <p class="current-course-card__empty-hint">可在课间休息或查看下一节课</p>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 当前课程高亮卡
 * 显示正在进行中的课程信息 + 3 个操作按钮（做笔记/课堂互动/资料）
 * 无进行中课程时显示空状态
 */
import type { CourseScheduleItem } from '../../types'

interface Props {
  /** 当前进行中的课程，无则为 null */
  course: CourseScheduleItem | null
}

interface Emits {
  /** 操作按钮点击，emit 对应子路径 */
  (e: 'action', route: string): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()
</script>

<style lang="scss" scoped>
.current-course-card {
  min-height: 140px;
  border-radius: var(--scene-card-radius, 10px);
  transition: box-shadow 0.3s ease;

  &--active {
    box-shadow: 0 4px 20px rgba(25, 118, 210, 0.15);
    border: 2px solid var(--scene-primary-color, #1976D2);
  }

  &__content {
    padding: 20px;
  }

  &__header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
  }

  &__status {
    display: flex;
    align-items: center;
    gap: 4px;

    &-icon {
      margin-right: 2px;
    }
  }

  &__name {
    font-size: 20px;
    font-weight: 700;
    color: var(--color-text-primary, #303133);
    margin: 0;
  }

  &__meta {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin-bottom: 16px;
    font-size: 13px;
    color: var(--color-text-secondary, #606266);

    span {
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }

  &__actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }

  &__empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 140px;
    gap: 8px;

    &-text {
      font-size: 15px;
      color: var(--color-text-primary, #606266);
      font-weight: 500;
      margin: 0;
    }

    &-hint {
      font-size: 12px;
      color: var(--color-text-secondary, #909399);
      margin: 0;
    }
  }
}
</style>
