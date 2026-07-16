<template>
  <div class="growth-dashboard">
    <!-- 统计卡片 -->
    <el-skeleton :loading="loading" :rows="3" animated>
      <template #default>
        <el-row :gutter="16" class="stat-cards">
          <el-col
            v-for="card in data?.stat_cards"
            :key="card.key"
            :xs="12"
            :sm="8"
            :md="6"
          >
            <el-card
              shadow="hover"
              class="stat-card"
              role="button"
              tabindex="0"
              :aria-label="`查看${card.label}`"
              @click="$emit('select', card.key)"
              @keydown.enter.prevent="$emit('select', card.key)"
              @keydown.space.prevent="$emit('select', card.key)"
            >
              <div class="stat-card__inner">
                <el-icon class="stat-card__icon" :size="28">
                  <component :is="getIconComponent(card.icon)" />
                </el-icon>
                <div class="stat-card__body">
                  <div class="stat-card__value">{{ card.value }}</div>
                  <div class="stat-card__label">{{ card.label }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 图表区域 -->
        <el-row :gutter="16" class="chart-section">
          <el-col :xs="24" :md="14">
            <el-card shadow="hover">
              <template #header>
                <span class="chart-title">近7天活跃度</span>
              </template>
              <v-chart
                v-if="weeklyChartOption"
                class="chart-canvas"
                :option="weeklyChartOption"
                autoresize
              />
              <el-empty v-else description="暂无活跃度数据" :image-size="60" />
            </el-card>
          </el-col>
          <el-col :xs="24" :md="10">
            <el-card shadow="hover">
              <template #header>
                <span class="chart-title">学科分布</span>
              </template>
              <v-chart
                v-if="subjectChartOption"
                class="chart-canvas"
                :option="subjectChartOption"
                autoresize
              />
              <el-empty v-else description="暂无学科数据" :image-size="60" />
            </el-card>
          </el-col>
        </el-row>
      </template>
    </el-skeleton>
  </div>
</template>

<script setup lang="ts">
/**
 * 成长仪表盘组件
 * 展示统计卡片、活跃度柱状图、学科分布饼图
 */
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import {
  TrendCharts,
  Reading,
  EditPen,
  ChatDotRound,
  DataAnalysis,
  Trophy,
  Notebook,
  School,
  Clock,
  Document,
} from '@element-plus/icons-vue'
import type { GrowthDashboardData } from '@/services/growth'

use([CanvasRenderer, BarChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const props = defineProps<{
  data: GrowthDashboardData | null
  loading: boolean
}>()

defineEmits<{
  select: [key: string]
}>()

/** 图标名称到组件的映射 */
const iconMap: Record<string, any> = {
  TrendCharts,
  Reading,
  EditPen,
  ChatDotRound,
  DataAnalysis,
  Trophy,
  Notebook,
  School,
  Clock,
  Document,
  chat: ChatDotRound,
  clipboard: DataAnalysis,
  note: EditPen,
  card: Notebook,
  star: Trophy,
  book: Reading,
  bookmark: Document,
  users: School,
}

function getIconComponent(iconName: string | null): any {
  if (!iconName) return TrendCharts
  return iconMap[iconName] || TrendCharts
}

/** 活跃度柱状图配置 */
const weeklyChartOption = computed(() => {
  const data = props.data?.weekly_activity
  if (!data || data.length === 0) return null
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.date.slice(5)),
      axisTick: { alignWithLabel: true },
    },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      {
        type: 'bar',
        data: data.map((d) => d.count),
        barWidth: '60%',
        itemStyle: {
          color: '#409eff',
          borderRadius: [4, 4, 0, 0],
        },
      },
    ],
  }
})

/** 学科分布饼图配置 */
const subjectChartOption = computed(() => {
  const data = props.data?.subject_distribution
  if (!data || data.length === 0) return null
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: '5%', left: 'center' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
        data: data.map((d) => ({ name: d.subject, value: d.count })),
      },
    ],
  }
})
</script>

<style lang="scss" scoped>
.growth-dashboard {
  .stat-cards {
    margin-bottom: 16px;
  }

  .stat-card {
    margin-bottom: 16px;
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease;

    &:hover,
    &:focus-visible {
      transform: translateY(-2px);
      box-shadow: 0 6px 18px rgba(64, 158, 255, 0.18);
      outline: 2px solid rgba(64, 158, 255, 0.35);
      outline-offset: 2px;
    }

    &__inner {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    &__icon {
      color: #409eff;
      flex-shrink: 0;
    }

    &__value {
      font-size: 24px;
      font-weight: 700;
      color: #303133;
      line-height: 1.2;
    }

    &__label {
      font-size: 13px;
      color: #909399;
      margin-top: 4px;
    }
  }

  .chart-section {
    margin-top: 8px;
  }

  .chart-title {
    font-weight: 600;
    font-size: 15px;
  }

  .chart-canvas {
    height: 280px;
    width: 100%;
  }
}
</style>
