<template>
  <div class="review-progress card">
    <h3 class="review-progress__title">
      <el-icon><TrendCharts /></el-icon>
      复习进度
    </h3>

    <!-- 环形进度图（vue-echarts gauge 类型） -->
    <div class="review-progress__chart">
      <v-chart :option="chartOption" autoresize class="review-progress__echarts" />
    </div>

    <!-- 各科目进度条 -->
    <div class="review-progress__subjects">
      <div
        v-for="subject in reviewProgress.subjects"
        :key="subject.subject"
        class="review-progress__subject"
      >
        <div class="review-progress__subject-header">
          <span class="review-progress__subject-name">{{ subject.subject }}</span>
          <span class="review-progress__subject-value">{{ subject.progress }}%</span>
        </div>
        <el-progress
          :percentage="subject.progress"
          :color="getSubjectColor(subject.progress)"
          :stroke-width="8"
          :show-text="false"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 复习进度环形图
 * 使用 vue-echarts 渲染 gauge 类型环形进度图 + 下方各科目进度条
 */
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { GaugeChart } from 'echarts/charts'
import VChart from 'vue-echarts'
import type { ReviewProgressData } from '../../types'

// 注册 ECharts 所需模块
use([CanvasRenderer, GaugeChart])

interface Props {
  /** 复习进度数据 */
  reviewProgress: ReviewProgressData
}

const props = defineProps<Props>()

/** ECharts gauge 环形图配置 */
const chartOption = computed(() => ({
  series: [
    {
      type: 'gauge',
      startAngle: 90,
      endAngle: -270,
      radius: '85%',
      pointer: { show: false },
      progress: {
        show: true,
        overlap: false,
        roundCap: true,
        clip: false,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 1,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#FFB74D' },
              { offset: 1, color: '#F57C00' },
            ],
          },
        },
      },
      axisLine: {
        lineStyle: {
          width: 16,
          color: [[1, '#f0f0f0']],
        },
      },
      splitLine: { show: false },
      axisTick: { show: false },
      axisLabel: { show: false },
      detail: {
        valueAnimation: true,
        formatter: '{value}%',
        fontSize: 32,
        fontWeight: 'bold' as const,
        color: '#F57C00',
        offsetCenter: ['0%', '0%'],
      },
      title: {
        show: true,
        offsetCenter: ['0%', '40%'],
        fontSize: 12,
        color: '#909399',
      },
      data: [
        { value: props.reviewProgress.overallProgress, name: '总复习进度' },
      ],
    },
  ],
}))

/** 根据进度获取科目进度条颜色 */
function getSubjectColor(progress: number): string {
  if (progress < 50) return '#EF5350'
  if (progress < 75) return '#FFB74D'
  return '#66BB6A'
}
</script>

<style lang="scss" scoped>
.review-progress {
  min-height: 340px;

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary, #303133);
    margin: 0 0 12px 0;
  }

  &__chart {
    display: flex;
    justify-content: center;
    margin-bottom: 16px;
  }

  &__echarts {
    width: 100%;
    height: 200px;
  }

  &__subjects {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  &__subject {
    &-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 4px;
    }

    &-name {
      font-size: 13px;
      font-weight: 500;
      color: var(--color-text-primary, #303133);
    }

    &-value {
      font-size: 13px;
      font-weight: 600;
      color: var(--color-text-secondary, #606266);
    }
  }
}
</style>
