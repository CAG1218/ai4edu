<template>
  <div class="step-interests">
    <h2 class="step-interests__title">你对哪些学科感兴趣？</h2>
    <p class="step-interests__subtitle">至少选择 3 个，我们将为你推荐相关学习资源</p>

    <div class="step-interests__tags">
      <el-check-tag
        v-for="subject in subjects"
        :key="subject"
        :checked="selectedInterests.includes(subject)"
        @change="toggleInterest(subject)"
        class="step-interests__tag"
        size="large"
      >
        {{ subject }}
      </el-check-tag>
    </div>

    <div class="step-interests__counter">
      <span :class="{ 'step-interests__counter--warn': selectedInterests.length < 3 }">
        已选择 {{ selectedInterests.length }}/3
      </span>
      <span v-if="selectedInterests.length < 3" class="step-interests__counter--hint">
        还需选择 {{ 3 - selectedInterests.length }} 个
      </span>
    </div>

    <div class="step-interests__action">
      <el-button @click="handlePrev">上一步</el-button>
      <el-button
        type="primary"
        :disabled="selectedInterests.length < 3"
        @click="handleNext"
      >
        下一步
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Onboarding Step 2: 兴趣学科选择（20 学科标签，至少选 3）
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const subjects: string[] = [
  '语文', '数学', '英语', '物理', '化学',
  '生物', '历史', '地理', '政治', '信息技术',
  '美术', '音乐', '体育', '科学', '编程',
  '心理学', '经济学', '哲学', '天文学', '环境科学',
]

const selectedInterests = ref<string[]>([...(userStore.onboardingData.interests || [])])

onMounted(() => {
  if (selectedInterests.value.length === 0) {
    selectedInterests.value = []
  }
})

function toggleInterest(subject: string): void {
  const idx = selectedInterests.value.indexOf(subject)
  if (idx >= 0) {
    selectedInterests.value.splice(idx, 1)
  } else {
    selectedInterests.value.push(subject)
  }
  userStore.setOnboardingData({ interests: [...selectedInterests.value] })
}

function handlePrev(): void {
  router.push({ name: 'onboarding-role' })
}

function handleNext(): void {
  if (selectedInterests.value.length < 3) return
  router.push({ name: 'onboarding-goal' })
}
</script>

<style lang="scss" scoped>
.step-interests {
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

  &__tags {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    justify-content: center;
    margin-bottom: 20px;
  }

  &__tag {
    font-size: 15px;
    padding: 8px 20px;
    border-radius: 20px;
    transition: all 0.2s;
  }

  &__counter {
    text-align: center;
    margin-bottom: 24px;
    font-size: 14px;
    color: #667eea;

    &--warn {
      color: #f56c6c;
    }

    &--hint {
      margin-left: 8px;
      color: #999;
      font-size: 13px;
    }
  }

  &__action {
    display: flex;
    justify-content: center;
    gap: 16px;
  }
}
</style>
