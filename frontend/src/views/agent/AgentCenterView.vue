<template>
  <div class="agent-center">
    <!-- 顶部标题栏 -->
    <div class="agent-center__header">
      <div class="agent-center__header-title">
        <h2>AI 智能体中心</h2>
        <p class="agent-center__header-subtitle">跟着老师的方法学，带着自己的资源问</p>
      </div>
      <!-- 模型状态指示灯 -->
      <div class="agent-center__model-status" @click="handleRefreshModels">
        <span :class="['agent-center__status-dot', statusDotClass]"></span>
        <span class="agent-center__status-text">{{ statusText }}</span>
      </div>
    </div>

    <!-- 场景卡片区域 -->
    <div class="agent-center__scenes">
      <el-row :gutter="20">
        <el-col v-for="scene in scenes" :key="scene.scene_type" :span="6">
          <SceneCard
            :scene="scene"
            :loading="creatingScene === scene.scene_type"
            @select="handleSceneSelect"
          />
        </el-col>
      </el-row>
    </div>

    <!-- 最近会话列表 -->
    <div class="agent-center__recent">
      <div class="agent-center__recent-header">
        <h3>最近会话</h3>
        <el-button text type="primary" @click="handleViewAllSessions">查看全部</el-button>
      </div>
      <div class="agent-center__session-list">
        <div
          v-for="session in recentSessions"
          :key="session.id"
          class="agent-center__session-item"
          @click="handleSessionClick(session)"
        >
          <div class="agent-center__session-info">
            <span class="agent-center__session-icon">{{ getSceneIcon(session.scene_type) }}</span>
            <div class="agent-center__session-detail">
              <span class="agent-center__session-title">{{ session.title }}</span>
              <span class="agent-center__session-meta">
                {{ getSceneName(session.scene_type) }} · {{ session.message_count }}条消息
              </span>
            </div>
          </div>
          <span class="agent-center__session-time">{{ formatTime(session.updated_at) }}</span>
        </div>
        <el-empty v-if="recentSessions.length === 0" description="暂无会话记录" :image-size="80" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AI 智能体中心 - 场景入口页
 * 展示 4 个场景卡片 + 最近会话列表 + 模型状态指示灯
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import SceneCard from './components/SceneCard.vue'
import { useAgentStore } from '@/stores/agent'
import type { ScenePreset, AgentSession } from '@/services/agent'

const router = useRouter()
const agentStore = useAgentStore()

/** 场景列表 */
const scenes = ref<ScenePreset[]>([])
/** 最近会话列表 */
const recentSessions = ref<AgentSession[]>([])
/** 正在创建的场景类型 */
const creatingScene = ref<string>('')

/** 可用模型数量 */
const availableModelCount = computed(() => {
  return agentStore.models.filter((m) => m.status === 'available').length
})

/** 状态指示灯样式 */
const statusDotClass = computed(() => {
  const count = availableModelCount.value
  if (count >= 2) return 'agent-center__status-dot--green'
  if (count === 1) return 'agent-center__status-dot--yellow'
  return 'agent-center__status-dot--red'
})

/** 状态文本 */
const statusText = computed(() => {
  const count = availableModelCount.value
  if (count >= 2) return `模型正常 (${count}个可用)`
  if (count === 1) return `模型降级 (${count}个可用)`
  return '模型不可用 (演示模式)'
})

/** 场景选择 */
async function handleSceneSelect(scene: ScenePreset): Promise<void> {
  creatingScene.value = scene.scene_type
  try {
    const session = await agentStore.createSceneSession(scene.scene_type)
    if (session) {
      router.push({
        name: 'SceneAIChat',
        params: {
          sceneType: scene.scene_type,
          sessionId: String(session.id),
        },
      })
    }
  } catch (error) {
    console.error('创建场景会话失败:', error)
    ElMessage.error('创建场景会话失败')
  } finally {
    creatingScene.value = ''
  }
}

/** 点击最近会话 */
function handleSessionClick(session: AgentSession): void {
  router.push({
    name: 'SceneAIChat',
    params: {
      sceneType: session.scene_type || 'self_study',
      sessionId: String(session.id),
    },
  })
}

/** 查看全部会话 */
function handleViewAllSessions(): void {
  router.push({ name: 'SceneAIChat' })
}

/** 刷新模型状态 */
async function handleRefreshModels(): Promise<void> {
  await agentStore.fetchModels()
}

/** 获取场景图标 */
function getSceneIcon(sceneType?: string): string {
  const iconMap: Record<string, string> = {
    self_study: '📖',
    preview: '🔍',
    review: '📝',
    exam_prep: '🏆',
  }
  return iconMap[sceneType || ''] || '💬'
}

/** 获取场景名称 */
function getSceneName(sceneType?: string): string {
  const nameMap: Record<string, string> = {
    self_study: '自习答疑',
    preview: '课前预习',
    review: '课后复习',
    exam_prep: '考前冲刺',
  }
  return nameMap[sceneType || ''] || 'AI对话'
}

/** 格式化时间 */
function formatTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}小时前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

onMounted(async () => {
  await Promise.all([
    agentStore.fetchScenes(),
    agentStore.fetchModels(),
    agentStore.fetchSessions(1, 5),
  ])
  recentSessions.value = agentStore.sessions.slice(0, 5)
  scenes.value = agentStore.scenes
})
</script>

<style lang="scss" scoped>
.agent-center {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
  }

  &__header-title {
    h2 {
      font-size: 24px;
      font-weight: 700;
      margin: 0 0 4px 0;
      color: #1a1a2e;
    }
  }

  &__header-subtitle {
    font-size: 14px;
    color: #888;
    margin: 0;
  }

  &__model-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 20px;
    background: #f5f5f5;
    cursor: pointer;
    transition: background 0.2s;

    &:hover {
      background: #eaeaea;
    }
  }

  &__status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;

    &--green {
      background: #4caf50;
      box-shadow: 0 0 6px rgba(76, 175, 80, 0.5);
    }
    &--yellow {
      background: #ff9800;
      box-shadow: 0 0 6px rgba(255, 152, 0, 0.5);
    }
    &--red {
      background: #f44336;
      box-shadow: 0 0 6px rgba(244, 67, 54, 0.5);
    }
  }

  &__status-text {
    font-size: 13px;
    color: #555;
  }

  &__scenes {
    margin-bottom: 40px;
  }

  &__recent {
    margin-top: 32px;
  }

  &__recent-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    h3 {
      font-size: 18px;
      font-weight: 600;
      margin: 0;
      color: #1a1a2e;
    }
  }

  &__session-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  &__session-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-radius: 10px;
    background: #fff;
    border: 1px solid #eee;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      border-color: #1976d2;
      box-shadow: 0 2px 8px rgba(25, 118, 210, 0.1);
    }
  }

  &__session-info {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  &__session-icon {
    font-size: 20px;
  }

  &__session-detail {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  &__session-title {
    font-size: 14px;
    font-weight: 500;
    color: #333;
  }

  &__session-meta {
    font-size: 12px;
    color: #999;
  }

  &__session-time {
    font-size: 12px;
    color: #bbb;
  }
}
</style>
