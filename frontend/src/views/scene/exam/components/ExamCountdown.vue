<template>
  <div class="exam-countdown card exam-countdown--warning-border">
    <div class="exam-countdown__content">
      <div class="exam-countdown__number-wrapper">
        <span class="exam-countdown__number">{{ countdown.daysLeft }}</span>
        <span class="exam-countdown__unit">天</span>
      </div>
      <p class="exam-countdown__label">距 {{ countdown.examName }} 还有 {{ countdown.daysLeft }} 天</p>
      <p class="exam-countdown__date">考试日期: {{ countdown.examDate }}</p>
      <el-button type="warning" plain size="small" @click="handleSetExamDate">
        <el-icon><Calendar /></el-icon>
        设置考试日期
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 考试倒计时大字报
 * 居中大字显示倒计时天数，P0 固定 14 天
 * "设置考试日期"按钮点击后提示"P1 版本支持"
 */
import { ElMessage } from 'element-plus'
import type { ExamCountdownData } from '../../types'

interface Props {
  /** 倒计时数据 */
  countdown: ExamCountdownData
}

defineProps<Props>()

/** P0 点击设置考试日期提示 P1 版本支持 */
function handleSetExamDate(): void {
  ElMessage.info('P1 版本支持自定义考试日期设置')
}
</script>

<style lang="scss" scoped>
.exam-countdown {
  text-align: center;
  padding: 32px 24px;

  &--warning-border {
    border: var(--scene-warning-border, 2px solid rgba(245, 124, 0, 0.3));
  }

  &__content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }

  &__number-wrapper {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  &__number {
    font-size: 80px;
    font-weight: 900;
    color: #F57C00;
    line-height: 1;
    animation: exam-countdown-blink 2s ease-in-out infinite;
    text-shadow: 0 4px 12px rgba(245, 124, 0, 0.3);
  }

  &__unit {
    font-size: 28px;
    font-weight: 700;
    color: #F57C00;
  }

  &__label {
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary, #303133);
    margin: 8px 0 0 0;
  }

  &__date {
    font-size: 13px;
    color: var(--color-text-secondary, #909399);
    margin: 0 0 16px 0;
  }
}
</style>
