<template>
  <div class="study-time-stats card">
    <h3 class="study-time-stats__title">
      <el-icon><Timer /></el-icon>
      学习统计
    </h3>
    <div class="study-time-stats__bars">
      <!-- 本周学习时长 -->
      <div class="study-time-stats__bar">
        <div class="study-time-stats__bar-label">
          <el-icon color="#1976D2"><Calendar /></el-icon>
          <span>本周学习</span>
        </div>
        <div class="study-time-stats__bar-track">
          <div class="study-time-stats__bar-fill study-time-stats__bar-fill--week">
            <span class="study-time-stats__bar-value">{{ data.weekHours }}</span>
          </div>
        </div>
      </div>

      <!-- 今日学习时长 -->
      <div class="study-time-stats__bar">
        <div class="study-time-stats__bar-label">
          <el-icon color="#388E3C"><Sunny /></el-icon>
          <span>今日学习</span>
        </div>
        <div class="study-time-stats__bar-track">
          <div class="study-time-stats__bar-fill study-time-stats__bar-fill--today">
            <span class="study-time-stats__bar-value">{{ data.todayHours }}</span>
          </div>
        </div>
      </div>

      <!-- 连续打卡天数 -->
      <div class="study-time-stats__bar">
        <div class="study-time-stats__bar-label">
          <el-icon color="#D32F2F"><Medal /></el-icon>
          <span>连续打卡</span>
        </div>
        <div class="study-time-stats__bar-track">
          <div class="study-time-stats__bar-fill study-time-stats__bar-fill--streak">
            <span class="study-time-stats__bar-value">{{ data.streakDays }} 天 🔥</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 学习时长统计
 * 横条展示本周学习时长 / 今日时长 / 连续打卡天数
 */
import type { StudyTimeData } from '../../types'

interface Props {
  /** 学习时长数据 */
  data: StudyTimeData
}

defineProps<Props>()
</script>

<style lang="scss" scoped>
.study-time-stats {
  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary, #303133);
    margin: 0 0 16px 0;
  }

  &__bars {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  &__bar {
    &-label {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      color: var(--color-text-secondary, #606266);
      margin-bottom: 4px;
    }

    &-track {
      width: 100%;
      height: 36px;
      background: #f0f2f5;
      border-radius: 18px;
      overflow: hidden;
      display: flex;
      align-items: center;
    }

    &-fill {
      height: 100%;
      border-radius: 18px;
      display: flex;
      align-items: center;
      padding: 0 16px;
      transition: width 0.6s ease;
      min-width: 80px;

      &--week {
        width: 80%;
        background: linear-gradient(90deg, #1976D2 0%, #64B5F6 100%);
      }

      &--today {
        width: 35%;
        background: linear-gradient(90deg, #388E3C 0%, #81C784 100%);
      }

      &--streak {
        width: 60%;
        background: linear-gradient(90deg, #D32F2F 0%, #FF8A80 100%);
      }
    }

    &-value {
      font-size: 14px;
      font-weight: 700;
      color: #fff;
      white-space: nowrap;
    }
  }
}
</style>
