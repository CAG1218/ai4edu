<template>
  <div class="step-role">
    <h2 class="step-role__title">你是谁？</h2>
    <p class="step-role__subtitle">选择你的身份，我们将为你定制专属的学习体验</p>

    <div class="step-role__cards">
      <div
        v-for="role in roles"
        :key="role.value"
        :class="['step-role__card', { 'step-role__card--active': selectedRole === role.value }]"
        @click="selectRole(role.value)"
      >
        <div class="step-role__card-icon">
          <el-icon :size="48"><component :is="role.icon" /></el-icon>
        </div>
        <h3 class="step-role__card-title">{{ role.label }}</h3>
        <p class="step-role__card-desc">{{ role.description }}</p>
        <el-tag v-if="selectedRole === role.value" type="success" effect="dark" round>
          已选择
        </el-tag>
      </div>
    </div>

    <div class="step-role__action">
      <el-button type="primary" size="large" :disabled="!selectedRole" @click="handleNext">
        下一步
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Onboarding Step 1: 角色选择（3 张卡片）
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

interface RoleOption {
  value: string
  label: string
  icon: string
  description: string
}

const roles: RoleOption[] = [
  {
    value: 'student',
    label: '我是学生',
    icon: 'User',
    description: '跟随课堂节奏、自主学习、备考冲刺',
  },
  {
    value: 'teacher',
    label: '我是教师',
    icon: 'School',
    description: '管理课程、布置作业、追踪学情',
  },
  {
    value: 'parent',
    label: '我是家长',
    icon: 'Home',
    description: '关注孩子学习进度、查看学情报告',
  },
]

const selectedRole = ref<string>(userStore.onboardingData.role || '')

function selectRole(role: string): void {
  selectedRole.value = role
  userStore.setOnboardingData({ role })
}

function handleNext(): void {
  if (!selectedRole.value) return
  router.push({ name: 'onboarding-interests' })
}
</script>

<style lang="scss" scoped>
.step-role {
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
    margin-bottom: 32px;
    font-size: 15px;
  }

  &__cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-bottom: 32px;
  }

  &__card {
    position: relative;
    padding: 28px 20px;
    border: 2px solid #e8e8e8;
    border-radius: 16px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
      border-color: #667eea;
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
    }

    &--active {
      border-color: #667eea;
      background: linear-gradient(135deg, #f5f7ff 0%, #eef1ff 100%);
      box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);

      .step-role__card-icon {
        color: #667eea;
      }
    }
  }

  &__card-icon {
    color: #999;
    margin-bottom: 16px;
    transition: color 0.3s;
  }

  &__card-title {
    font-size: 18px;
    font-weight: 600;
    color: #1a1a2e;
    margin-bottom: 8px;
  }

  &__card-desc {
    font-size: 13px;
    color: #888;
    line-height: 1.5;
    margin-bottom: 8px;
  }

  &__action {
    text-align: center;
  }
}

@media (max-width: 640px) {
  .step-role__cards {
    grid-template-columns: 1fr;
  }
}
</style>
