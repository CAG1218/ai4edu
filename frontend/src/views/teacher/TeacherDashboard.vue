<template>
  <div class="teacher-dashboard">
    <div class="teacher-dashboard__header">
      <h1>教师工作台</h1>
      <p class="teacher-dashboard__welcome">欢迎回来，{{ teacherName }} 老师！</p>
    </div>

    <!-- 班级概览卡片 -->
    <el-row :gutter="16" class="teacher-dashboard__overview">
      <el-col :xs="12" :sm="6" v-for="stat in classStats" :key="stat.label">
        <div class="teacher-dashboard__stat-card">
          <div class="teacher-dashboard__stat-icon" :style="{ background: stat.bgColor }">
            <el-icon :size="24" :color="stat.color"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="teacher-dashboard__stat-info">
            <span class="teacher-dashboard__stat-value">{{ stat.value }}</span>
            <span class="teacher-dashboard__stat-label">{{ stat.label }}</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 主内容区 -->
    <el-row :gutter="16" class="teacher-dashboard__content">
      <!-- 今日课程 -->
      <el-col :xs="24" :lg="14">
        <el-card shadow="never" class="teacher-dashboard__card">
          <template #header>
            <div class="teacher-dashboard__card-header">
              <h3>今日课程</h3>
              <el-button type="primary" link>查看全部</el-button>
            </div>
          </template>
          <div class="teacher-dashboard__course-list">
            <div
              v-for="course in todayCourses"
              :key="course.id"
              class="teacher-dashboard__course-item"
              @click="goToCourse(course.id)"
            >
              <div class="teacher-dashboard__course-time">
                <span class="teacher-dashboard__course-hour">{{ course.time }}</span>
              </div>
              <div class="teacher-dashboard__course-info">
                <span class="teacher-dashboard__course-name">{{ course.name }}</span>
                <span class="teacher-dashboard__course-class">{{ course.className }}</span>
              </div>
              <el-tag :type="course.status === 'active' ? 'success' : course.status === 'upcoming' ? 'warning' : 'info'" size="small">
                {{ course.statusText }}
              </el-tag>
            </div>
            <el-empty v-if="todayCourses.length === 0" description="今日无课程" :image-size="60" />
          </div>
        </el-card>
      </el-col>

      <!-- AI备课快捷入口 -->
      <el-col :xs="24" :lg="10">
        <el-card shadow="never" class="teacher-dashboard__card">
          <template #header>
            <h3>AI 备课助手</h3>
          </template>
          <div class="teacher-dashboard__ai-actions">
            <div class="teacher-dashboard__ai-action" @click="goToLessonPlan">
              <el-icon :size="28" color="#1976D2"><Document /></el-icon>
              <span>生成教案</span>
            </div>
            <div class="teacher-dashboard__ai-action" @click="goToDiagnosis">
              <el-icon :size="28" color="#388E3C"><DataAnalysis /></el-icon>
              <span>班级诊断</span>
            </div>
            <div class="teacher-dashboard__ai-action" @click="goToAIChat">
              <el-icon :size="28" color="#7B1FA2"><ChatDotRound /></el-icon>
              <span>AI对话</span>
            </div>
            <div class="teacher-dashboard__ai-action" @click="goToResources">
              <el-icon :size="28" color="#F57C00"><Folder /></el-icon>
              <span>资源库</span>
            </div>
          </div>
        </el-card>

        <!-- 学习诊断概览 -->
        <el-card shadow="never" class="teacher-dashboard__card" style="margin-top: 16px">
          <template #header>
            <div class="teacher-dashboard__card-header">
              <h3>学习诊断概览</h3>
              <el-button type="primary" link @click="goToDiagnosis">详细分析</el-button>
            </div>
          </template>
          <div class="teacher-dashboard__diagnosis-summary">
            <div class="teacher-dashboard__diagnosis-item">
              <span class="teacher-dashboard__diagnosis-label">班级平均分</span>
              <span class="teacher-dashboard__diagnosis-value">78.5</span>
            </div>
            <div class="teacher-dashboard__diagnosis-item">
              <span class="teacher-dashboard__diagnosis-label">薄弱知识点</span>
              <span class="teacher-dashboard__diagnosis-value teacher-dashboard__diagnosis-value--warn">3个</span>
            </div>
            <div class="teacher-dashboard__diagnosis-item">
              <span class="teacher-dashboard__diagnosis-label">学生活跃度</span>
              <el-progress :percentage="82" :stroke-width="8" :color="'#1976D2'" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
/**
 * AI4Edu 教师工作台
 * 班级概览 + 今日课程 + AI备课入口 + 学习诊断概览
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Document, DataAnalysis, ChatDotRound, Folder } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const teacherName = computed(() => authStore.user?.nickname ?? '老师')

// 班级概览统计
const classStats = ref([
  { label: '学生总数', value: 48, icon: 'User', color: '#1976D2', bgColor: '#e3f2fd' },
  { label: '班级平均分', value: '78.5', icon: 'TrendCharts', color: '#388E3C', bgColor: '#e8f5e9' },
  { label: '活跃度', value: '82%', icon: 'Timer', color: '#F57C00', bgColor: '#fff3e0' },
  { label: '薄弱知识点', value: 3, icon: 'Warning', color: '#D32F2F', bgColor: '#ffebee' },
])

// 今日课程
const todayCourses = ref([
  { id: 1, name: '高等数学', className: '数学2301班', time: '08:00', status: 'finished', statusText: '已结束' },
  { id: 2, name: '线性代数', className: '数学2301班', time: '10:00', status: 'active', statusText: '进行中' },
  { id: 3, name: '概率论', className: '数学2302班', time: '14:00', status: 'upcoming', statusText: '待上课' },
  { id: 4, name: '数理统计', className: '数学2302班', time: '16:00', status: 'upcoming', statusText: '待上课' },
])

function goToCourse(courseId: number): void {
  router.push({ name: 'SceneClassroom', params: { courseId } })
}

function goToLessonPlan(): void {
  router.push({ name: 'TeacherLessonPlans' })
}

function goToDiagnosis(): void {
  router.push({ name: 'TeacherLessonPlans' })
}

function goToAIChat(): void {
  router.push({ name: 'SceneAIChat' })
}

function goToResources(): void {
  router.push({ name: 'MyResources' })
}
</script>

<style lang="scss" scoped>
.teacher-dashboard {
  &__header {
    margin-bottom: 24px;

    h1 {
      font-size: 24px;
      font-weight: 700;
      color: #303133;
      margin: 0 0 4px;
    }
  }

  &__welcome {
    font-size: 14px;
    color: #909399;
    margin: 0;
  }

  &__overview {
    margin-bottom: 24px;
  }

  &__stat-card {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
    margin-bottom: 12px;
  }

  &__stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  &__stat-info {
    display: flex;
    flex-direction: column;
  }

  &__stat-value {
    font-size: 24px;
    font-weight: 700;
    color: #303133;
    line-height: 1.2;
  }

  &__stat-label {
    font-size: 13px;
    color: #909399;
    margin-top: 2px;
  }

  &__card {
    margin-bottom: 0;

    :deep(.el-card__header) {
      padding: 14px 20px;
      border-bottom: 1px solid #f0f0f0;
    }
  }

  &__card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h3 {
      font-size: 16px;
      font-weight: 600;
      margin: 0;
    }
  }

  &__course-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  &__course-item {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 10px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s;

    &:hover {
      background: #f5f7fa;
    }
  }

  &__course-time {
    width: 52px;
    flex-shrink: 0;
  }

  &__course-hour {
    font-size: 14px;
    font-weight: 600;
    color: #303133;
  }

  &__course-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  &__course-name {
    font-size: 14px;
    font-weight: 500;
    color: #303133;
  }

  &__course-class {
    font-size: 12px;
    color: #909399;
  }

  &__ai-actions {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  &__ai-action {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 20px 12px;
    border-radius: 10px;
    background: #fafafa;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background: #f0f0f0;
      transform: translateY(-1px);
    }

    span {
      font-size: 13px;
      color: #606266;
      font-weight: 500;
    }
  }

  &__diagnosis-summary {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  &__diagnosis-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  &__diagnosis-label {
    font-size: 14px;
    color: #606266;
  }

  &__diagnosis-value {
    font-size: 18px;
    font-weight: 700;
    color: #303133;

    &--warn {
      color: #e6a23c;
    }
  }
}
</style>
