<template>
  <div class="step-goal">
    <h2 class="step-goal__title">你的学习目标是什么？</h2>
    <p class="step-goal__subtitle">选择你的学习目标，可多选</p>

    <div class="step-goal__cards">
      <div
        v-for="goal in goals"
        :key="goal.value"
        :class="['step-goal__card', { 'step-goal__card--active': selectedGoals.includes(goal.value) }]"
        @click="toggleGoal(goal.value)"
      >
        <div class="step-goal__card-icon" :style="{ color: goal.color }">
          <el-icon :size="36"><component :is="goal.icon" /></el-icon>
        </div>
        <h3 class="step-goal__card-title">{{ goal.label }}</h3>
        <p class="step-goal__card-desc">{{ goal.description }}</p>
      </div>
    </div>

    <div class="step-goal__action">
      <el-button @click="handlePrev">上一步</el-button>
      <el-button
        type="primary"
        :disabled="selectedGoals.length === 0"
        :loading="loading"
        @click="handleComplete"
      >
        完成引导
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Onboarding Step 3: 学习目标选择（4 目标卡片，可多选）
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import { useSceneStore } from '@/stores/scene'
import { authApi } from '@/services/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const userStore = useUserStore()
const sceneStore = useSceneStore()

interface GoalOption {
  value: string
  label: string
  icon: string
  color: string
  description: string
}

const goals: GoalOption[] = [
  {
    value: '考试提分',
    label: '考试提分',
    icon: 'Trophy',
    color: '#F57C00',
    description: '针对考试重点高效复习，提升成绩',
  },
  {
    value: '系统学习',
    label: '系统学习',
    icon: 'Reading',
    color: '#388E3C',
    description: '按知识点体系系统地学习，夯实基础',
  },
  {
    value: '课堂同步',
    label: '课堂同步',
    icon: 'School',
    color: '#1976D2',
    description: '跟随课堂进度，课前预习课后复习',
  },
  {
    value: '协作交流',
    label: '协作交流',
    icon: 'ChatDotRound',
    color: '#7B1FA2',
    description: '与同学讨论交流，合作学习',
  },
]

const selectedGoals = ref<string[]>([...(userStore.onboardingData.goals || [])])
const loading = ref(false)

function toggleGoal(goalValue: string): void {
  const idx = selectedGoals.value.indexOf(goalValue)
  if (idx >= 0) {
    selectedGoals.value.splice(idx, 1)
  } else {
    selectedGoals.value.push(goalValue)
  }
  userStore.setOnboardingData({ goals: [...selectedGoals.value] })
}

async function handleComplete(): Promise<void> {
  if (selectedGoals.value.length === 0) return
  loading.value = true

  try {
    // 根据目标推荐默认场景
    const goalSceneMap: Record<string, string> = {
      '考试提分': 'exam',
      '系统学习': 'self_study',
      '课堂同步': 'classroom',
      '协作交流': 'discussion',
    }

    // 选择第一个目标对应的场景作为默认
    const defaultScene = goalSceneMap[selectedGoals.value[0]] || 'classroom'

    // 切换到推荐场景
    await sceneStore.switchScene(defaultScene as any)

    // ✅ 调用后端接口持久化引导完成状态
    const userId = authStore.user?.id
    if (userId) {
      await authApi.completeOnboarding(userId, {
        role: userStore.onboardingData.role || '',
        interests: userStore.onboardingData.interests || [],
        goals: selectedGoals.value,
      })
      // 刷新 authStore 中的用户信息，确保 onboarding_completed=true
      await authStore.fetchCurrentUser()
    }

    // 更新本地状态
    userStore.completeOnboarding()

    ElMessage.success('引导完成，开始你的学习之旅！')
    const redirect = (router.currentRoute.value.query.redirect as string) || '/'
    await router.push(redirect)
  } catch (error) {
    const msg = error instanceof Error ? error.message : '操作失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

function handlePrev(): void {
  router.push({ name: 'onboarding-interests' })
}
</script>

<style lang="scss" scoped>
.step-goal {
  &__title {
    font-size: 28px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 8px;
    color: #1a1a2e;
  }

  &__subtitle {
    text-align: center;
    color: #666;
    margin-bottom: 28px;
    font-size: 15px;
  }

  &__cards {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin-bottom: 32px;
  }

  &__card {
    padding: 24px;
    border: 2px solid #e8e8e8;
    border-radius: 16px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
      border-color: #667eea;
      transform: translateY(-2px);
    }

    &--active {
      border-color: #667eea;
      background: linear-gradient(135deg, #f5f7ff 0%, #eef1ff 100%);
      box-shadow: 0 4px 16px rgba(102, 126, 234, 0.15);
    }
  }

  &__card-icon {
    margin-bottom: 12px;
  }

  &__card-title {
    font-size: 17px;
    font-weight: 600;
    color: #1a1a2e;
    margin-bottom: 6px;
  }

  &__card-desc {
    font-size: 13px;
    color: #888;
    line-height: 1.5;
  }

  &__action {
    display: flex;
    justify-content: center;
    gap: 16px;
  }
}

@media (max-width: 640px) {
  .step-goal__cards {
    grid-template-columns: 1fr;
  }
}
</style>
