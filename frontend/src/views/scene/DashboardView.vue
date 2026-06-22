<template>
  <div :class="['dashboard-view', sceneClass]">
    <!-- 场景推荐提示 -->
    <el-alert
      v-if="sceneRecommendation && sceneRecommendation.confidence >= 0.7"
      :title="sceneRecommendation.reason"
      type="info"
      show-icon
      closable
      class="dashboard-view__recommendation"
    >
      <template #default>
        <span>当前场景: {{ sceneName }}</span>
        <el-button
          v-if="sceneRecommendation.recommended_scene !== currentSceneType"
          type="primary"
          link
          @click="switchToRecommended"
        >
          切换到{{ getSceneName(sceneRecommendation.recommended_scene) }}
        </el-button>
      </template>
    </el-alert>

    <div class="dashboard-view__header">
      <h1 class="dashboard-view__title">{{ sceneName }} 仪表盘</h1>
      <p class="dashboard-view__subtitle">欢迎回来，{{ userName }}！</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="dashboard-view__stats">
      <el-col :xs="12" :sm="6" v-for="stat in sceneStats" :key="stat.label">
        <div class="dashboard-view__stat-card card">
          <el-icon :size="24" :style="{ color: stat.color }">
            <component :is="stat.icon" />
          </el-icon>
          <div class="dashboard-view__stat-info">
            <span class="dashboard-view__stat-value">{{ stat.value }}</span>
            <span class="dashboard-view__stat-label">{{ stat.label }}</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 按场景显示不同内容 -->
    <el-row :gutter="16" class="dashboard-view__content">
      <!-- 课堂模式 -->
      <template v-if="currentSceneType === 'classroom'">
        <el-col :xs="24" :lg="16">
          <div class="card">
            <h3>今日课程</h3>
            <div class="dashboard-view__course-list">
              <div v-for="course in todayCourses" :key="course.name" class="dashboard-view__course-item">
                <el-tag :type="course.status === '进行中' ? 'success' : 'info'" size="small">
                  {{ course.status }}
                </el-tag>
                <span class="dashboard-view__course-name">{{ course.name }}</span>
                <span class="dashboard-view__course-time">{{ course.time }}</span>
              </div>
              <p v-if="todayCourses.length === 0" class="text-secondary">今日暂无课程</p>
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :lg="8">
          <div class="card">
            <h3>课堂互动</h3>
            <div class="dashboard-view__quick-actions">
              <el-button type="primary" plain @click="goTo('/ai-chat')">举手提问</el-button>
              <el-button type="success" plain @click="goTo('/classroom/1')">参与投票</el-button>
              <el-button type="warning" plain @click="goTo('/diagnosis')">随堂测验</el-button>
            </div>
          </div>
        </el-col>
      </template>

      <!-- 自习模式 -->
      <template v-else-if="currentSceneType === 'self_study'">
        <el-col :xs="24" :lg="16">
          <div class="card">
            <h3>知识图谱</h3>
            <div class="dashboard-view__graph-placeholder">
              <el-icon :size="48" color="#388E3C"><Connection /></el-icon>
              <p>选择一个知识点开始学习</p>
              <el-button type="success" @click="goTo('/graphs')">浏览知识图谱</el-button>
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :lg="8">
          <div class="card">
            <h3>学习工具</h3>
            <div class="dashboard-view__quick-actions">
              <el-button type="success" plain @click="goTo('/buddy')">AI 学伴</el-button>
              <el-button type="primary" plain @click="goTo('/graphs')">闪卡记忆</el-button>
              <el-button type="warning" plain @click="goTo('/graphs')">思维导图</el-button>
            </div>
          </div>
        </el-col>
      </template>

      <!-- 考前模式 -->
      <template v-else-if="currentSceneType === 'exam'">
        <el-col :xs="24" :lg="16">
          <div class="card">
            <h3>错题本</h3>
            <div class="dashboard-view__exam-stats">
              <div class="dashboard-view__exam-stat">
                <span class="dashboard-view__exam-stat-value">24</span>
                <span class="dashboard-view__exam-stat-label">待复习错题</span>
              </div>
              <div class="dashboard-view__exam-stat">
                <span class="dashboard-view__exam-stat-value">89%</span>
                <span class="dashboard-view__exam-stat-label">正确率</span>
              </div>
              <div class="dashboard-view__exam-stat">
                <span class="dashboard-view__exam-stat-value">3</span>
                <span class="dashboard-view__exam-stat-label">薄弱知识点</span>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :lg="8">
          <div class="card">
            <h3>考前工具</h3>
            <div class="dashboard-view__quick-actions">
              <el-button type="warning" plain @click="goTo('/diagnosis')">模拟考试</el-button>
              <el-button type="danger" plain @click="goTo('/notes')">错题重练</el-button>
              <el-button type="primary" plain @click="goTo('/diagnosis')">限时训练</el-button>
            </div>
          </div>
        </el-col>
      </template>

      <!-- 讨论模式 -->
      <template v-else-if="currentSceneType === 'discussion'">
        <el-col :xs="24" :lg="16">
          <div class="card">
            <h3>讨论话题</h3>
            <div class="dashboard-view__discussion-list">
              <div v-for="topic in discussionTopics" :key="topic.title" class="dashboard-view__discussion-item">
                <span class="dashboard-view__discussion-title">{{ topic.title }}</span>
                <span class="dashboard-view__discussion-meta">{{ topic.participants }}人参与</span>
              </div>
              <p v-if="discussionTopics.length === 0" class="text-secondary">暂无活跃讨论</p>
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :lg="8">
          <div class="card">
            <h3>协作工具</h3>
            <div class="dashboard-view__quick-actions">
              <el-button type="primary" plain @click="goTo('/ai-chat')">发起讨论</el-button>
              <el-button type="success" plain @click="goTo('/buddy')">白板协作</el-button>
              <el-button type="warning" plain @click="goTo('/classroom/1')">投票</el-button>
            </div>
          </div>
        </el-col>
      </template>
    </el-row>
  </div>
</template>

<script setup lang="ts">
/**
 * AI4Edu 场景化仪表盘
 * 按场景类型显示不同的统计和功能
 */
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSceneStore } from '@/stores/scene'
import type { SceneType } from '@/utils/constants'
import api from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()
const sceneStore = useSceneStore()

// 仪表盘统计（从后端 API 获取）
const dashboardStats = ref({
  course_count: 0,
  note_count: 0,
  resource_count: 0,
  ai_chat_count: 0,
  study_hours: '0h',
})

/** 跳转到指定功能页 */
function goTo(path: string): void {
  router.push(`/scene/${currentSceneType.value}${path}`)
}

const userName = computed(() => authStore.user?.nickname ?? '同学')
const sceneName = computed(() => sceneStore.sceneName)
const sceneClass = computed(() => sceneStore.sceneClass)
const currentSceneType = computed(() => sceneStore.currentSceneType)
const sceneRecommendation = computed(() => sceneStore.recommendation)

// 场景特定统计
const sceneStats = computed(() => {
  const s = dashboardStats.value
  const base = [
    { label: '课程数', value: s.course_count, icon: 'Reading', color: '#1976D2' },
    { label: '笔记数', value: s.note_count, icon: 'EditPen', color: '#388E3C' },
    { label: '学习时长', value: s.study_hours, icon: 'Timer', color: '#F57C00' },
    { label: 'AI对话', value: s.ai_chat_count, icon: 'ChatDotRound', color: '#7B1FA2' },
  ]

  switch (currentSceneType.value) {
    case 'exam':
      return [
        { label: '错题数', value: 24, icon: 'Warning', color: '#F57C00' },
        { label: '模拟考试', value: 3, icon: 'Document', color: '#1976D2' },
        { label: '复习进度', value: '68%', icon: 'TrendCharts', color: '#388E3C' },
        { label: '倒计时', value: '14天', icon: 'Timer', color: '#D32F2F' },
      ]
    case 'discussion':
      return [
        { label: '讨论数', value: 8, icon: 'ChatDotRound', color: '#7B1FA2' },
        { label: '参与人数', value: 32, icon: 'User', color: '#1976D2' },
        { label: '白板数', value: 2, icon: 'Monitor', color: '#388E3C' },
        { label: '投票数', value: 5, icon: 'CheckBox', color: '#F57C00' },
      ]
    default:
      return base
  }
})

// 课堂模式 - 今日课程
const todayCourses = ref([
  { name: '高等数学', time: '08:00-09:40', status: '已结束' },
  { name: '大学物理', time: '10:00-11:40', status: '进行中' },
  { name: '数据结构', time: '14:00-15:40', status: '未开始' },
])

// 讨论模式 - 话题
const discussionTopics = ref([
  { title: '递归算法的优化策略', participants: 12 },
  { title: '牛顿力学的适用范围', participants: 8 },
])

const SCENE_NAMES: Record<string, string> = {
  classroom: '课堂模式',
  self_study: '自习模式',
  exam: '考前模式',
  discussion: '讨论模式',
}

function getSceneName(sceneType: string): string {
  return SCENE_NAMES[sceneType] || sceneType
}

async function switchToRecommended(): Promise<void> {
  if (sceneRecommendation.value) {
    await sceneStore.switchScene(sceneRecommendation.value.recommended_scene as SceneType)
  }
}

onMounted(async () => {
  // 获取场景推荐
  await sceneStore.getRecommendation()
  // 获取仪表盘统计
  try {
    // api 响应拦截器已解包 axios，res = {code, data: stats, message}
    const res = await api.get('/api/v1/dashboard/stats') as any
    if (res.data) {
      dashboardStats.value = res.data
    }
  } catch (e) {
    console.warn('获取仪表盘统计失败', e)
  }
})
</script>

<style lang="scss" scoped>
.dashboard-view {
  &__recommendation {
    margin-bottom: 16px;
  }

  &__header {
    margin-bottom: var(--spacing-lg);
  }

  &__title {
    font-size: 24px;
    font-weight: 700;
    color: var(--color-text-primary);
    margin-bottom: var(--spacing-xs);
  }

  &__subtitle {
    font-size: 14px;
    color: var(--color-text-secondary);
  }

  &__stats {
    margin-bottom: var(--spacing-lg);
  }

  &__stat-card {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-md);
  }

  &__stat-info {
    display: flex;
    flex-direction: column;
  }

  &__stat-value {
    font-size: 24px;
    font-weight: 700;
    color: var(--color-text-primary);
  }

  &__stat-label {
    font-size: 12px;
    color: var(--color-text-secondary);
  }

  &__content {
    .card {
      min-height: 200px;

      h3 {
        margin-bottom: var(--spacing-md);
        color: var(--color-text-primary);
      }
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
    gap: 12px;
    padding: 8px 0;
    border-bottom: 1px solid #f0f0f0;

    &:last-child {
      border-bottom: none;
    }
  }

  &__course-name {
    flex: 1;
    font-weight: 500;
  }

  &__course-time {
    color: #999;
    font-size: 13px;
  }

  &__quick-actions {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  &__graph-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 160px;
    gap: 12px;
    color: #999;
  }

  &__exam-stats {
    display: flex;
    gap: 24px;
    justify-content: center;
    padding: 20px 0;
  }

  &__exam-stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }

  &__exam-stat-value {
    font-size: 32px;
    font-weight: 700;
    color: var(--color-text-primary);
  }

  &__exam-stat-label {
    font-size: 13px;
    color: #999;
  }

  &__discussion-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  &__discussion-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #f0f0f0;

    &:last-child {
      border-bottom: none;
    }
  }

  &__discussion-title {
    font-weight: 500;
  }

  &__discussion-meta {
    color: #999;
    font-size: 13px;
  }
}

.text-secondary {
  color: var(--color-text-secondary);
}
</style>
