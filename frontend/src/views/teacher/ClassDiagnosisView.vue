<template>
  <div class="class-diagnosis">
    <div class="class-diagnosis__header">
      <h2>班级诊断</h2>
      <el-select v-model="selectedClass" placeholder="选择班级" style="width: 180px" @change="loadDiagnosis">
        <el-option label="数学2301班" value="math-2301" />
        <el-option label="数学2302班" value="math-2302" />
        <el-option label="物理2301班" value="physics-2301" />
      </el-select>
    </div>

    <el-row :gutter="16">
      <!-- 知识点掌握度热力图 -->
      <el-col :xs="24" :lg="14">
        <el-card shadow="never" class="class-diagnosis__card">
          <template #header>
            <h3>知识点掌握度热力图</h3>
          </template>
          <div class="class-diagnosis__heatmap">
            <div class="class-diagnosis__heatmap-grid">
              <div
                v-for="(cell, idx) in heatmapData"
                :key="idx"
                class="class-diagnosis__heatmap-cell"
                :style="{ backgroundColor: getHeatColor(cell.value) }"
                :title="`${cell.name}: ${cell.value}%`"
              >
                <span class="class-diagnosis__heatmap-label">{{ cell.name }}</span>
                <span class="class-diagnosis__heatmap-value">{{ cell.value }}%</span>
              </div>
            </div>
            <div class="class-diagnosis__heatmap-legend">
              <span>低掌握</span>
              <div class="class-diagnosis__heatmap-bar"></div>
              <span>高掌握</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 弱点知识点排行 -->
      <el-col :xs="24" :lg="10">
        <el-card shadow="never" class="class-diagnosis__card">
          <template #header>
            <h3>薄弱知识点排行</h3>
          </template>
          <div class="class-diagnosis__weak-list">
            <div
              v-for="(item, idx) in weakPoints"
              :key="idx"
              class="class-diagnosis__weak-item"
            >
              <div class="class-diagnosis__weak-rank">
                <span :class="['class-diagnosis__rank-badge', `class-diagnosis__rank-badge--${idx < 3 ? 'danger' : 'warn'}`]">
                  {{ idx + 1 }}
                </span>
              </div>
              <div class="class-diagnosis__weak-info">
                <span class="class-diagnosis__weak-name">{{ item.name }}</span>
                <el-progress
                  :percentage="item.mastery"
                  :stroke-width="6"
                  :color="getProgressColor(item.mastery)"
                  :show-text="false"
                  class="class-diagnosis__weak-progress"
                />
              </div>
              <span class="class-diagnosis__weak-score">{{ item.mastery }}%</span>
            </div>
          </div>
        </el-card>

        <!-- 学生学习建议 -->
        <el-card shadow="never" class="class-diagnosis__card" style="margin-top: 16px">
          <template #header>
            <div class="class-diagnosis__card-header">
              <h3>学习建议</h3>
              <el-button type="primary" link size="small">生成报告</el-button>
            </div>
          </template>
          <div class="class-diagnosis__suggestions">
            <div
              v-for="(suggestion, idx) in suggestions"
              :key="idx"
              class="class-diagnosis__suggestion-item"
            >
              <el-icon :color="suggestion.iconColor"><component :is="suggestion.icon" /></el-icon>
              <div class="class-diagnosis__suggestion-content">
                <span class="class-diagnosis__suggestion-title">{{ suggestion.title }}</span>
                <p class="class-diagnosis__suggestion-desc">{{ suggestion.description }}</p>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
/**
 * AI4Edu 班级诊断页
 * 知识点热力图 + 弱点排行 + 学习建议
 */
import { ref, onMounted } from 'vue'
import { Warning, Reading, Timer, TrendCharts } from '@element-plus/icons-vue'

const selectedClass = ref<string>('math-2301')

// 热力图数据
const heatmapData = ref([
  { name: '极限', value: 85 },
  { name: '连续', value: 72 },
  { name: '导数', value: 68 },
  { name: '微分', value: 55 },
  { name: '积分', value: 42 },
  { name: '级数', value: 38 },
  { name: '多元函数', value: 61 },
  { name: '偏导数', value: 53 },
  { name: '重积分', value: 35 },
  { name: '曲线积分', value: 28 },
  { name: '曲面积分', value: 31 },
  { name: '常微分', value: 58 },
])

// 弱点知识点
const weakPoints = ref([
  { name: '曲面积分', mastery: 28 },
  { name: '曲线积分', mastery: 31 },
  { name: '重积分', mastery: 35 },
  { name: '级数', mastery: 38 },
  { name: '积分', mastery: 42 },
  { name: '偏导数', mastery: 53 },
])

// 学习建议
const suggestions = ref([
  { title: '加强积分基础练习', description: '全班积分相关知识点掌握率偏低，建议增加练习题量和讲解时间', icon: 'Warning', iconColor: '#e6a23c' },
  { title: '推荐分层教学', description: '曲面积分和曲线积分差异较大，建议按水平分组教学', icon: 'Reading', iconColor: '#1976D2' },
  { title: '调整教学进度', description: '当前进度可能过快，建议在积分章节增加2课时', icon: 'Timer', iconColor: '#F57C00' },
  { title: '引入可视化工具', description: '多元函数和积分概念抽象，建议使用图形化教学工具辅助理解', icon: 'TrendCharts', iconColor: '#388E3C' },
])

/** 热力图颜色 */
function getHeatColor(value: number): string {
  if (value >= 80) return '#4caf50'
  if (value >= 60) return '#8bc34a'
  if (value >= 40) return '#ffc107'
  if (value >= 20) return '#ff9800'
  return '#f44336'
}

/** 进度条颜色 */
function getProgressColor(percentage: number): string {
  if (percentage >= 70) return '#67c23a'
  if (percentage >= 50) return '#e6a23c'
  return '#f56c6c'
}

async function loadDiagnosis(): Promise<void> {
  // 根据班级加载诊断数据
}

onMounted(() => {
  loadDiagnosis()
})
</script>

<style lang="scss" scoped>
.class-diagnosis {
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      font-size: 22px;
      font-weight: 700;
      color: #303133;
      margin: 0;
    }
  }

  &__card {
    margin-bottom: 16px;

    :deep(.el-card__header) {
      padding: 14px 20px;
    }

    h3 {
      font-size: 16px;
      font-weight: 600;
      margin: 0;
    }
  }

  &__card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  &__heatmap {
    padding: 8px 0;
  }

  &__heatmap-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
  }

  &__heatmap-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 14px 8px;
    border-radius: 8px;
    color: #fff;
    min-height: 64px;
    transition: transform 0.2s;
    cursor: default;

    &:hover {
      transform: scale(1.05);
    }
  }

  &__heatmap-label {
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 2px;
  }

  &__heatmap-value {
    font-size: 16px;
    font-weight: 700;
  }

  &__heatmap-legend {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-top: 16px;
    font-size: 12px;
    color: #909399;
  }

  &__heatmap-bar {
    width: 120px;
    height: 8px;
    border-radius: 4px;
    background: linear-gradient(90deg, #f44336, #ff9800, #ffc107, #8bc34a, #4caf50);
  }

  &__weak-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  &__weak-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0;
  }

  &__weak-rank {
    flex-shrink: 0;
  }

  &__rank-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    font-size: 12px;
    font-weight: 700;
    color: #fff;

    &--danger { background: #f56c6c; }
    &--warn { background: #e6a23c; }
  }

  &__weak-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  &__weak-name {
    font-size: 14px;
    font-weight: 500;
    color: #303133;
  }

  &__weak-progress {
    margin: 0;
  }

  &__weak-score {
    font-size: 14px;
    font-weight: 600;
    color: #f56c6c;
    min-width: 40px;
    text-align: right;
  }

  &__suggestions {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  &__suggestion-item {
    display: flex;
    gap: 12px;
    padding: 12px;
    background: #fafafa;
    border-radius: 8px;
  }

  &__suggestion-content {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  &__suggestion-title {
    font-size: 14px;
    font-weight: 600;
    color: #303133;
  }

  &__suggestion-desc {
    font-size: 13px;
    color: #909399;
    margin: 0;
    line-height: 1.5;
  }
}

@media (max-width: 768px) {
  .class-diagnosis {
    &__heatmap-grid {
      grid-template-columns: repeat(3, 1fr);
    }
  }
}
</style>
