<template>
  <div class="wrong-book-summary card">
    <h3 class="wrong-book-summary__title">
      <el-icon><Warning /></el-icon>
      错题本概览
    </h3>

    <div class="wrong-book-summary__stats">
      <!-- 待复习 -->
      <div class="wrong-book-summary__stat wrong-book-summary__stat--pending">
        <span class="wrong-book-summary__stat-value">{{ stats.pendingReview }}</span>
        <span class="wrong-book-summary__stat-label">待复习</span>
      </div>
      <!-- 已掌握 -->
      <div class="wrong-book-summary__stat wrong-book-summary__stat--mastered">
        <span class="wrong-book-summary__stat-value">{{ stats.mastered }}</span>
        <span class="wrong-book-summary__stat-label">已掌握</span>
      </div>
      <!-- 正确率 -->
      <div class="wrong-book-summary__stat wrong-book-summary__stat--rate">
        <span class="wrong-book-summary__stat-value">{{ stats.correctRate }}%</span>
        <span class="wrong-book-summary__stat-label">正确率</span>
      </div>
    </div>

    <el-button
      type="primary"
      class="wrong-book-summary__btn"
      :disabled="stats.pendingReview === 0"
      @click="emit('retry')"
    >
      <el-icon><EditPen /></el-icon>
      错题重练
    </el-button>
  </div>
</template>

<script setup lang="ts">
/**
 * 错题本概览
 * 三列数字展示（待复习/已掌握/正确率）+ "错题重练"按钮
 */
import type { WrongBookStats } from '../../types'

interface Props {
  /** 错题本统计数据 */
  stats: WrongBookStats
}

interface Emits {
  /** 错题重练按钮点击 */
  (e: 'retry'): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()
</script>

<style lang="scss" scoped>
.wrong-book-summary {
  min-height: 340px;
  display: flex;
  flex-direction: column;

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary, #303133);
    margin: 0 0 20px 0;
  }

  &__stats {
    display: flex;
    justify-content: space-around;
    gap: 12px;
    margin-bottom: 20px;
    flex: 1;
    align-items: center;
  }

  &__stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding: 16px;
    border-radius: 10px;
    flex: 1;

    &--pending {
      background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);

      .wrong-book-summary__stat-value {
        color: #F57C00;
      }
    }

    &--mastered {
      background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);

      .wrong-book-summary__stat-value {
        color: #388E3C;
      }
    }

    &--rate {
      background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);

      .wrong-book-summary__stat-value {
        color: #1976D2;
      }
    }
  }

  &__stat-value {
    font-size: 36px;
    font-weight: 800;
    line-height: 1;
  }

  &__stat-label {
    font-size: 13px;
    color: var(--color-text-secondary, #606266);
    font-weight: 500;
  }

  &__btn {
    width: 100%;
    margin-top: auto;
  }
}
</style>
