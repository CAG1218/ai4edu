<template>
  <div class="exam-dashboard">
    <!-- 场景横幅 -->
    <SceneWelcomeBanner :config="sceneConfig" />

    <!-- 考前专属统计卡 -->
    <SceneStatCard :stats="examMockData.stats" />

    <!-- 考试倒计时大字报 -->
    <ExamCountdown :countdown="examMockData.countdown" />

    <!-- 复习进度环形图 + 错题本概览 -->
    <el-row :gutter="16">
      <el-col :xs="24" :lg="12">
        <ReviewProgress :review-progress="examMockData.reviewProgress" />
      </el-col>
      <el-col :xs="24" :lg="12">
        <WrongBookSummary :stats="examMockData.wrongBookStats" @retry="handleRetry" />
      </el-col>
    </el-row>

    <!-- 薄弱知识点标签 -->
    <WeakPointsTags :weak-points="examMockData.weakPoints" />

    <!-- 考前工具栏 -->
    <QuickActionBar
      :actions="examMockData.toolbarActions"
      title="考前工具"
      @action="handleAction"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * 考前模式仪表盘
 * 组合：场景横幅 + 统计卡 + 倒计时 + 复习进度环形图 + 错题本 + 薄弱知识点 + 工具栏
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSceneStore } from '@/stores/scene'
import { SCENE_CONFIG } from '@/utils/constants'
import SceneWelcomeBanner from '../components/SceneWelcomeBanner.vue'
import SceneStatCard from '../components/SceneStatCard.vue'
import QuickActionBar from '../components/QuickActionBar.vue'
import ExamCountdown from './components/ExamCountdown.vue'
import ReviewProgress from './components/ReviewProgress.vue'
import WrongBookSummary from './components/WrongBookSummary.vue'
import WeakPointsTags from './components/WeakPointsTags.vue'
import { examMockData } from '../mock/scene-mock-data'
import type { QuickAction } from '../types'

const router = useRouter()
const sceneStore = useSceneStore()

/** 场景配置 */
const sceneConfig = computed(() => SCENE_CONFIG[sceneStore.currentSceneType])

/**
 * 场景内路由跳转（A-7 统一模式）
 * @param subPath 子路径
 */
function navigateToSceneRoute(subPath: string): void {
  const sceneType = sceneStore.currentSceneType
  router.push(`/scene/${sceneType}/${subPath}`)
}

/** 处理工具栏快捷操作 */
function handleAction(action: QuickAction): void {
  navigateToSceneRoute(action.route)
}

/** 错题重练 */
function handleRetry(): void {
  navigateToSceneRoute('diagnosis')
}
</script>

<style lang="scss" scoped>
.exam-dashboard {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg, 16px);
}
</style>
