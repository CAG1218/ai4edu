<template>
  <div class="teacher-dashboard" v-loading="loading">
    <div class="teacher-dashboard__header">
      <h1>教师工作台</h1>
      <p>欢迎回来，{{ teacherName }}！</p>
    </div>

    <el-row :gutter="16" class="teacher-dashboard__overview">
      <el-col v-for="stat in classStats" :key="stat.label" :xs="12" :sm="6">
        <div class="teacher-dashboard__stat-card">
          <div class="teacher-dashboard__stat-icon" :style="{ background: stat.bgColor }">
            <el-icon :size="24" :color="stat.color"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="teacher-dashboard__stat-info">
            <strong>{{ stat.value }}</strong><span>{{ stat.label }}</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="14">
        <el-card shadow="never">
          <template #header><div class="card-header"><h3>我的课程</h3><el-button link type="primary" @click="goToLessonPlan">查看教案</el-button></div></template>
          <div class="course-list">
            <div v-for="course in courses" :key="course.id" class="course-item" @click="goToCourse(course)">
              <div class="course-icon"><el-icon><Reading /></el-icon></div>
              <div class="course-info"><strong>{{ course.name }}</strong><span>{{ course.grade }} · {{ course.semester }}</span></div>
              <el-tag type="success" size="small">进入备课</el-tag>
            </div>
            <el-empty v-if="courses.length === 0" description="暂无课程；保存第一份教案后会自动建立课程" :image-size="72" />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card shadow="never">
          <template #header><h3>AI 备课助手</h3></template>
          <div class="ai-actions">
            <button @click="goToLessonPlan"><el-icon color="#1976D2"><Document /></el-icon><span>生成教案</span></button>
            <button @click="goToDiagnosis"><el-icon color="#388E3C"><DataAnalysis /></el-icon><span>班级诊断</span></button>
            <button @click="goToAIChat"><el-icon color="#7B1FA2"><ChatDotRound /></el-icon><span>AI 对话</span></button>
            <button @click="goToResources"><el-icon color="#F57C00"><Folder /></el-icon><span>资源库</span></button>
          </div>
        </el-card>

        <el-card shadow="never" class="diagnosis-card">
          <template #header><div class="card-header"><h3>学习诊断概览</h3><el-button link type="primary" @click="goToDiagnosis">详细分析</el-button></div></template>
          <div class="diagnosis-summary">
            <div><span>已完成诊断</span><strong>{{ analytics.total_diagnoses }}</strong></div>
            <div><span>平均得分</span><strong>{{ analytics.average_score || '--' }}</strong></div>
            <div><span>已识别薄弱知识点</span><strong class="warn">{{ analytics.weak_points.length }}</strong></div>
          </div>
        </el-card>

        <TeacherEvaluationPanel :courses="courses" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Document, DataAnalysis, ChatDotRound, Folder, Reading } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import TeacherEvaluationPanel from './components/TeacherEvaluationPanel.vue'

interface Course { id: number; name: string; grade: string; semester: string }
interface Dashboard { student_count: number; course_count: number; lesson_plan_count: number; resource_count: number }
interface Analytics { total_diagnoses: number; average_score: number; weak_points: Array<{ name: string; mastery: number }> }

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const courses = ref<Course[]>([])
const dashboard = ref<Dashboard>({ student_count: 0, course_count: 0, lesson_plan_count: 0, resource_count: 0 })
const analytics = ref<Analytics>({ total_diagnoses: 0, average_score: 0, weak_points: [] })
const teacherName = computed(() => authStore.user?.nickname || '老师')
const classStats = computed(() => [
  { label: '学生总数', value: dashboard.value.student_count, icon: 'User', color: '#1976D2', bgColor: '#e3f2fd' },
  { label: '课程数', value: dashboard.value.course_count, icon: 'Reading', color: '#388E3C', bgColor: '#e8f5e9' },
  { label: '教案数', value: dashboard.value.lesson_plan_count, icon: 'Document', color: '#F57C00', bgColor: '#fff3e0' },
  { label: '资源数', value: dashboard.value.resource_count, icon: 'Folder', color: '#7B1FA2', bgColor: '#f3e5f5' },
])

async function loadDashboard(): Promise<void> {
  loading.value = true
  try {
    const [dashboardResponse, coursesResponse, analyticsResponse] = await Promise.all([
      api.get('/teachers/dashboard'), api.get('/teachers/courses'), api.get('/teachers/analytics'),
    ])
    dashboard.value = { ...dashboard.value, ...(dashboardResponse.data as Dashboard) }
    courses.value = coursesResponse.data as Course[]
    analytics.value = { ...analytics.value, ...(analyticsResponse.data as Analytics) }
  } finally { loading.value = false }
}

function goToCourse(course: Course): void { router.push({ name: 'TeacherCourseDetail', params: { id: course.id }, query: { name: course.name } }) }
function goToLessonPlan(): void { router.push({ name: 'TeacherLessonPlans' }) }
function goToDiagnosis(): void { router.push({ name: 'ClassDiagnosis' }) }
function goToAIChat(): void { router.push({ name: 'TeacherAIChat' }) }
function goToResources(): void { router.push({ name: 'TeacherResources' }) }
onMounted(loadDashboard)
</script>

<style lang="scss" scoped>
.teacher-dashboard {
  &__header { margin-bottom: 24px; h1 { margin: 0 0 4px; font-size: 24px; } p { margin: 0; color: #909399; } }
  &__overview { margin-bottom: 20px; }
  &__stat-card { display: flex; align-items: center; gap: 14px; padding: 16px; margin-bottom: 12px; background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.06); }
  &__stat-icon { width: 48px; height: 48px; display: grid; place-items: center; border-radius: 12px; }
  &__stat-info { display: flex; flex-direction: column; strong { font-size: 24px; } span { font-size: 13px; color: #909399; } }
}
.card-header { display: flex; align-items: center; justify-content: space-between; h3 { margin: 0; } }
.course-list { display: flex; flex-direction: column; gap: 10px; }
.course-item { display: flex; align-items: center; gap: 12px; padding: 12px; border-radius: 8px; cursor: pointer; &:hover { background: #f5f7fa; } }
.course-icon { width: 40px; height: 40px; display: grid; place-items: center; color: #1976d2; background: #e3f2fd; border-radius: 10px; }
.course-info { flex: 1; display: flex; flex-direction: column; span { margin-top: 3px; font-size: 12px; color: #909399; } }
.ai-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; button { border: 0; padding: 20px 12px; border-radius: 10px; background: #fafafa; cursor: pointer; display: flex; flex-direction: column; align-items: center; gap: 8px; font: inherit; &:hover { background: #f0f0f0; } .el-icon { font-size: 28px; } } }
.diagnosis-card { margin-top: 16px; }
.diagnosis-summary { display: flex; flex-direction: column; gap: 16px; div { display: flex; justify-content: space-between; } strong { font-size: 18px; } .warn { color: #e6a23c; } }
</style>
