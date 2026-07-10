<template>
  <div class="review-reminder card">
    <h3 class="review-reminder__title">
      <el-icon><Bell /></el-icon>
      课后复习
    </h3>
    <div v-if="reminders.length === 0" class="review-reminder__empty">
      <p class="review-reminder__empty-text">暂无复习提醒</p>
    </div>
    <div v-else class="review-reminder__list">
      <div
        v-for="item in reminders"
        :key="item.courseId"
        class="review-reminder__item"
      >
        <el-icon class="review-reminder__item-icon" :size="20" color="#1976D2"><Document /></el-icon>
        <div class="review-reminder__item-info">
          <span class="review-reminder__item-name">{{ item.courseName }}</span>
          <span class="review-reminder__item-desc">{{ item.description }}</span>
        </div>
        <el-button
          type="primary"
          size="small"
          plain
          @click="emit('action', item)"
        >
          {{ item.actionLabel }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 课后复习提醒
 * 展示课后复习任务列表，每项含课程名 + 描述 + 操作按钮
 */
import type { ReviewReminderItem } from '../../types'

interface Props {
  /** 复习提醒列表 */
  reminders: ReviewReminderItem[]
}

interface Emits {
  /** 点击操作按钮，emit 对应的提醒项 */
  (e: 'action', item: ReviewReminderItem): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()
</script>

<style lang="scss" scoped>
.review-reminder {
  min-height: 280px;

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary, #303133);
    margin: 0 0 16px 0;
  }

  &__list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  &__item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px;
    border-radius: 8px;
    background: var(--scene-primary-bg, #E3F2FD);
    transition: transform 0.2s ease;

    &:hover {
      transform: translateX(4px);
    }

    &-icon {
      flex-shrink: 0;
    }

    &-info {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    &-name {
      font-size: 14px;
      font-weight: 600;
      color: var(--color-text-primary, #303133);
    }

    &-desc {
      font-size: 12px;
      color: var(--color-text-secondary, #606266);
    }
  }

  &__empty {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 180px;

    &-text {
      color: var(--color-text-secondary, #909399);
      font-size: 14px;
    }
  }
}
</style>
