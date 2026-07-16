<template>
  <div class="growth-profile">
    <!-- 学生信息卡 -->
    <el-card shadow="never" class="profile-header">
      <div class="profile-header__inner">
        <el-avatar :size="64" :src="studentInfo.avatar_url || undefined" class="profile-header__avatar">
          {{ studentInfo.nickname?.charAt(0) || '?' }}
        </el-avatar>
        <div class="profile-header__info">
          <h2 class="profile-header__name">{{ studentInfo.nickname || '学生' }}</h2>
          <div class="profile-header__meta">
            <el-tag v-if="studentInfo.grade" size="small" effect="plain">
              {{ studentInfo.grade }}
            </el-tag>
            <span v-if="studentInfo.school" class="profile-header__school">
              <el-icon><School /></el-icon>
              {{ studentInfo.school }}
            </span>
            <span class="profile-header__join">
              注册于 {{ formatDate(studentInfo.created_at) }}
            </span>
          </div>
        </div>
        <div v-if="isTeacherView" class="profile-header__action">
          <el-button type="primary" @click="openEvaluationForm">
            <el-icon><EditPen /></el-icon>
            写评价
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 仪表盘 -->
    <section class="growth-section">
      <h3 class="growth-section__title">
        <el-icon><DataAnalysis /></el-icon>
        成长概览
      </h3>
      <GrowthDashboard :data="growthStore.dashboard" :loading="dashboardLoading" />
    </section>

    <!-- 时间线 -->
    <section class="growth-section">
      <h3 class="growth-section__title">
        <el-icon><Clock /></el-icon>
        成长时间线
      </h3>
      <el-card shadow="never">
        <GrowthTimeline
          :items="growthStore.timeline"
          :loading="growthStore.isLoading"
          :has-more="growthStore.timelineHasMore"
          @load-more="handleLoadMore"
          @filter="handleFilter"
        />
      </el-card>
    </section>

    <!-- 教师评价 -->
    <section class="growth-section">
      <div class="growth-section__header">
        <h3 class="growth-section__title">
          <el-icon><TrendCharts /></el-icon>
          教师评价
        </h3>
        <el-button v-if="isTeacherView" type="primary" size="small" @click="openEvaluationForm">
          <el-icon><Plus /></el-icon>
          写评价
        </el-button>
      </div>
      <div v-if="growthStore.evaluations.length > 0" class="evaluation-list">
        <TeacherEvaluationCard
          v-for="ev in growthStore.evaluations"
          :key="ev.id"
          :evaluation="ev"
          :editable="isTeacherView"
          @edit="handleEditEvaluation"
          @delete="handleDeleteEvaluation"
        />
      </div>
      <el-empty v-else description="暂无教师评价" />
    </section>

    <!-- 评价表单弹窗 -->
    <EvaluationForm
      v-model:visible="evaluationFormVisible"
      :evaluation="editingEvaluation"
      :student-id="studentId"
      @success="handleEvaluationSuccess"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * 学生成长档案主页面
 * 支持学生端和教师端两种视角
 */
import { computed, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  School,
  EditPen,
  DataAnalysis,
  Clock,
  TrendCharts,
  Plus,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useGrowthStore } from '@/stores/growth'
import GrowthDashboard from './components/GrowthDashboard.vue'
import GrowthTimeline from './components/GrowthTimeline.vue'
import TeacherEvaluationCard from './components/TeacherEvaluationCard.vue'
import EvaluationForm from './components/EvaluationForm.vue'
import type { EvaluationItem } from '@/services/growth'

const route = useRoute()
const authStore = useAuthStore()
const growthStore = useGrowthStore()

// ============ 视角判断 ============

const isTeacherView = computed(() => route.path.startsWith('/teacher/'))
const studentId = computed(() => {
  if (isTeacherView.value) {
    return Number(route.params.studentId)
  }
  return authStore.user?.id ?? 0
})

/** 学生信息（教师端使用 auth store 中基本信息，实际场景可按需扩展） */
const studentInfo = computed(() => {
  if (isTeacherView.value) {
    return {
      nickname: route.query.name as string || '学生',
      grade: route.query.grade as string || '',
      school: route.query.school as string || '',
      avatar_url: null,
      created_at: '',
    }
  }
  return {
    nickname: authStore.user?.nickname || '',
    grade: authStore.user?.grade || '',
    school: authStore.user?.school || '',
    avatar_url: authStore.user?.avatar_url,
    created_at: authStore.user?.created_at || '',
  }
})

// ============ 加载状态 ============

const dashboardLoading = ref(false)

// ============ 评价表单 ============

const evaluationFormVisible = ref(false)
const editingEvaluation = ref<EvaluationItem | null>(null)

function openEvaluationForm(): void {
  editingEvaluation.value = null
  evaluationFormVisible.value = true
}

function handleEditEvaluation(evaluation: EvaluationItem): void {
  editingEvaluation.value = evaluation
  evaluationFormVisible.value = true
}

async function handleDeleteEvaluation(evaluationId: number): Promise<void> {
  await growthStore.deleteEvaluation(evaluationId)
}

function handleEvaluationSuccess(): void {
  // 评价成功后刷新仪表盘
  growthStore.fetchDashboard(studentId.value)
}

// ============ 时间线操作 ============

function handleLoadMore(): void {
  growthStore.loadMoreTimeline(studentId.value)
}

function handleFilter(source: string): void {
  growthStore.fetchTimeline(studentId.value, source)
}

// ============ 工具函数 ============

function formatDate(dateStr: string): string {
  if (!dateStr) return '未知'
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
  })
}

// ============ 初始化 ============

onMounted(async () => {
  if (!studentId.value) {
    ElMessage.warning('无法获取学生信息')
    return
  }

  // 并行获取仪表盘、时间线、评价
  dashboardLoading.value = true
  await Promise.all([
    growthStore.fetchDashboard(studentId.value),
    growthStore.fetchTimeline(studentId.value),
    growthStore.fetchEvaluations(studentId.value),
  ])
  dashboardLoading.value = false
})
</script>

<style lang="scss" scoped>
.growth-profile {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.profile-header {
  margin-bottom: 24px;

  &__inner {
    display: flex;
    align-items: center;
    gap: 20px;
  }

  &__avatar {
    background-color: #409eff;
    color: #fff;
    font-size: 24px;
    font-weight: 700;
    flex-shrink: 0;
  }

  &__info {
    flex: 1;
  }

  &__name {
    margin: 0 0 8px;
    font-size: 20px;
    font-weight: 700;
    color: #303133;
  }

  &__meta {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  &__school {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    color: #606266;
  }

  &__join {
    font-size: 12px;
    color: #909399;
  }

  &__action {
    flex-shrink: 0;
  }
}

.growth-section {
  margin-bottom: 32px;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    margin: 0 0 16px;

    .el-icon {
      color: #409eff;
    }
  }

  &__header &__title {
    margin-bottom: 0;
  }
}

.evaluation-list {
  display: grid;
  gap: 12px;
}
</style>
