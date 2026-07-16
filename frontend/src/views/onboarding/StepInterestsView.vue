<template>
  <div class="step-interests">
    <h2 class="step-interests__title">你对哪些大学课程感兴趣？</h2>
    <p class="step-interests__subtitle">至少选择 3 个，我们将为你推荐相关学习资源与精准服务</p>

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
 * Onboarding Step 2: 大学兴趣课程选择（约 40 个大学课程标签，至少选 3）
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const subjects: string[] = [
  // 数理基础
  '数学分析', '高等代数', '线性代数', '概率论与数理统计', '离散数学', '复变函数', '常微分方程', '数理方程', '数值分析',
  // 物理与化学
  '大学物理', '大学物理（力学）', '大学物理（电磁学）', '无机化学', '有机化学', '物理化学', '分析化学',
  // 计算机与信息
  'C语言程序设计', '数据结构与算法', '计算机组成原理', '操作系统', '计算机网络', '数据库原理', '软件工程', '人工智能导论', '机器学习', '深度学习', '模式识别', '计算机视觉', '自然语言处理',
  // 电子与电气
  '电路分析', '模拟电子技术', '数字电子技术', '信号与系统', '自动控制原理', '通信原理', '微处理器与接口技术',
  // 人文社科与思政
  '马克思主义基本原理', '中国近现代史纲要', '毛泽东思想和中国特色社会主义理论体系概论', '思想道德与法治', '大学英语', '学术英语写作', '逻辑学', '心理学', '社会学概论', '经济学原理', '微观经济学', '宏观经济学', '会计学原理', '管理学原理', '法学概论', '新闻传播学概论',
  // 生物医学与工程
  '普通生物学', '生物化学', '生理学', '人体解剖学', '材料力学', '工程力学', '机械设计基础', '流体力学', '热力学',
  // 教育学与师范
  '教育学原理', '教育心理学', '课程与教学论', '教师职业道德',
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
  router.push({ name: 'onboarding-major' })
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
