<template>
  <div class="flashcard-review card">
    <h3 class="flashcard-review__title">
      <el-icon><Postcard /></el-icon>
      闪卡复习
    </h3>

    <div class="flashcard-review__pending">
      <span class="flashcard-review__pending-icon">⚡</span>
      <span class="flashcard-review__pending-label">今日待复习</span>
      <span class="flashcard-review__pending-count">{{ stats.pendingReview }}</span>
      <span class="flashcard-review__pending-unit">张</span>
    </div>

    <div class="flashcard-review__mastery">
      <div class="flashcard-review__mastery-header">
        <span class="flashcard-review__mastery-label">📊 掌握度</span>
        <span class="flashcard-review__mastery-value">{{ stats.masteryRate }}%</span>
      </div>
      <el-progress
        :percentage="stats.masteryRate"
        :color="masteryColor"
        :stroke-width="8"
        :show-text="false"
      />
    </div>

    <div class="flashcard-review__next">
      <el-icon><AlarmClock /></el-icon>
      <span>下次复习: {{ stats.nextReviewTopic }}</span>
    </div>

    <el-button
      type="primary"
      class="flashcard-review__btn"
      :disabled="stats.pendingReview === 0"
      @click="emit('start')"
    >
      <el-icon><VideoPlay /></el-icon>
      开始复习
    </el-button>
  </div>
</template>

<script setup lang="ts">
/**
 * 闪卡复习提醒
 * 展示待复习卡片数 + 掌握度进度 + 下次复习主题 + 开始复习按钮
 */
import { computed } from 'vue'
import type { FlashcardStats } from '../../types'

interface Props {
  /** 闪卡统计数据 */
  stats: FlashcardStats
}

interface Emits {
  /** 开始复习 */
  (e: 'start'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

/** 掌握度进度条颜色（随掌握率变化） */
const masteryColor = computed(() => {
  if (props.stats.masteryRate < 50) return '#F57C00'
  if (props.stats.masteryRate < 80) return '#1976D2'
  return '#388E3C'
})
</script>

<style lang="scss" scoped>
.flashcard-review {
  min-height: 320px;
  display: flex;
  flex-direction: column;

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary, #303133);
    margin: 0 0 16px 0;
  }

  &__pending {
    display: flex;
    align-items: baseline;
    gap: 6px;
    padding: 16px;
    border-radius: 10px;
    background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
    margin-bottom: 16px;

    &-icon {
      font-size: 20px;
    }

    &-label {
      font-size: 14px;
      color: var(--color-text-secondary, #606266);
    }

    &-count {
      font-size: 32px;
      font-weight: 800;
      color: #F57C00;
      line-height: 1;
    }

    &-unit {
      font-size: 14px;
      color: var(--color-text-secondary, #909399);
    }
  }

  &__mastery {
    margin-bottom: 16px;

    &-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }

    &-label {
      font-size: 13px;
      color: var(--color-text-secondary, #606266);
    }

    &-value {
      font-size: 16px;
      font-weight: 700;
      color: var(--color-text-primary, #303133);
    }
  }

  &__next {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: var(--color-text-secondary, #606266);
    margin-bottom: 16px;
    padding: 8px 12px;
    background: #f5f7fa;
    border-radius: 6px;
  }

  &__btn {
    width: 100%;
    margin-top: auto;
  }
}
</style>
