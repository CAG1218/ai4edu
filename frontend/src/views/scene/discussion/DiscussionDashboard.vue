<template>
  <div class="discussion-dashboard">
    <!-- 场景横幅 -->
    <SceneWelcomeBanner :config="sceneConfig" />

    <!-- 讨论专属统计卡 -->
    <SceneStatCard :stats="discussionMockData.stats" />

    <!-- 快速发起讨论 -->
    <QuickStartDiscussion @start="handleStartDiscussion" />

    <!-- 热门话题 + 我的讨论 -->
    <el-row :gutter="16">
      <el-col :xs="24" :lg="14">
        <HotTopicsRank :hot-topics="discussionMockData.hotTopics" />
      </el-col>
      <el-col :xs="24" :lg="10">
        <MyDiscussionFeed :my-discussions="discussionMockData.myDiscussions" />
      </el-col>
    </el-row>

    <!-- 协作工具栏 -->
    <QuickActionBar
      :actions="discussionMockData.collabActions"
      title="协作工具"
      @action="handleAction"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * 讨论模式仪表盘
 * 组合：场景横幅 + 统计卡 + 发起讨论 + 热门话题 + 我的讨论 + 协作工具栏
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSceneStore } from '@/stores/scene'
import { SCENE_CONFIG } from '@/utils/constants'
import SceneWelcomeBanner from '../components/SceneWelcomeBanner.vue'
import SceneStatCard from '../components/SceneStatCard.vue'
import QuickActionBar from '../components/QuickActionBar.vue'
import QuickStartDiscussion from './components/QuickStartDiscussion.vue'
import HotTopicsRank from './components/HotTopicsRank.vue'
import MyDiscussionFeed from './components/MyDiscussionFeed.vue'
import { discussionMockData } from '../mock/scene-mock-data'
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

/** 发起讨论（跳转 AI 智能体中心） */
function handleStartDiscussion(): void {
  navigateToSceneRoute('agent')
}
</script>

<style lang="scss" scoped>
.discussion-dashboard {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg, 16px);
}
</style>
