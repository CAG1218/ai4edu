<template>
  <div class="self-study-dashboard">
    <!-- 场景横幅 -->
    <SceneWelcomeBanner :config="sceneConfig" />

    <!-- 自习专属统计卡 -->
    <SceneStatCard :stats="selfStudyMockData.stats" />

    <!-- 今日学习计划（置顶全宽） -->
    <StudyPlanProgress :tasks="selfStudyMockData.tasks" @toggle="handleTaskToggle" />

    <!-- 知识图谱入口 + 闪卡复习 -->
    <el-row :gutter="16">
      <el-col :xs="24" :lg="12">
        <KnowledgeGraphEntry :graph-mini="selfStudyMockData.graphMini" @enter="handleEnterGraph" />
      </el-col>
      <el-col :xs="24" :lg="12">
        <FlashcardReview :stats="selfStudyMockData.flashcardStats" @start="handleStartReview" />
      </el-col>
    </el-row>

    <!-- 学习时长统计 -->
    <StudyTimeStats :data="selfStudyMockData.studyTime" />
  </div>
</template>

<script setup lang="ts">
/**
 * 自习模式仪表盘
 * 组合：场景横幅 + 统计卡 + 学习计划进度 + 知识图谱入口 + 闪卡复习 + 学习时长统计
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSceneStore } from '@/stores/scene'
import { SCENE_CONFIG } from '@/utils/constants'
import SceneWelcomeBanner from '../components/SceneWelcomeBanner.vue'
import SceneStatCard from '../components/SceneStatCard.vue'
import StudyPlanProgress from './components/StudyPlanProgress.vue'
import KnowledgeGraphEntry from './components/KnowledgeGraphEntry.vue'
import FlashcardReview from './components/FlashcardReview.vue'
import StudyTimeStats from './components/StudyTimeStats.vue'
import { selfStudyMockData } from '../mock/scene-mock-data'
import type { StudyTask } from '../types'

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

/** 处理任务勾选（P0 仅前端状态变更，P2 对接后端） */
function handleTaskToggle(_task: StudyTask): void {
  // P0: 任务状态为 mock 数据，勾选不持久化；P2 需调用 API 更新
  console.log('任务勾选:', _task.id, _task.title)
}

/** 进入知识图谱 */
function handleEnterGraph(): void {
  navigateToSceneRoute('graphs')
}

/** 开始闪卡复习 */
function handleStartReview(): void {
  navigateToSceneRoute('graphs')
}
</script>

<style lang="scss" scoped>
.self-study-dashboard {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg, 16px);
}
</style>
