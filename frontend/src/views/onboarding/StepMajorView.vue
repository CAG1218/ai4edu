<template>
  <div class="step-major">
    <h2 class="step-major__title">你是什么专业？</h2>
    <p class="step-major__subtitle">填写所在专业，我们将为你提供更精准的课程推荐与学习帮助</p>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
      class="step-major__form"
      @submit.prevent="handleNext"
    >
      <el-form-item label="所在专业" prop="major">
        <el-input
          v-model="form.major"
          placeholder="例如：计算机科学与技术、机械工程、数学与应用数学"
          size="large"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <div class="step-major__suggestions">
        <p class="step-major__suggestions-title">热门专业</p>
        <div class="step-major__tags">
          <el-check-tag
            v-for="major in popularMajors"
            :key="major"
            :checked="form.major === major"
            class="step-major__tag"
            size="large"
            @change="selectMajor(major)"
          >
            {{ major }}
          </el-check-tag>
        </div>
      </div>
    </el-form>

    <div class="step-major__action">
      <el-button @click="handlePrev">上一步</el-button>
      <el-button type="primary" :disabled="!form.major.trim()" @click="handleNext">
        下一步
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Onboarding Step 2: 所在专业填写（用于精准推荐课程与服务）
 */
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const form = reactive({
  major: userStore.onboardingData.major || '',
})

const rules: FormRules = {
  major: [
    { required: true, message: '请输入所在专业', trigger: 'blur' },
    { min: 2, max: 100, message: '专业名称长度2-100个字符', trigger: 'blur' },
  ],
}

const popularMajors: string[] = [
  '计算机科学与技术',
  '软件工程',
  '人工智能',
  '数据科学与大数据技术',
  '电子信息工程',
  '自动化',
  '机械工程',
  '数学与应用数学',
  '物理学',
  '化学',
  '生物科学',
  '经济学',
  '金融学',
  '工商管理',
  '法学',
  '汉语言文学',
  '英语',
  '教育学',
  '临床医学',
  '药学',
]

function selectMajor(major: string): void {
  form.major = major
  userStore.setOnboardingData({ major })
}

async function handleNext(): Promise<void> {
  if (!formRef.value) return

  await formRef.value.validate((valid) => {
    if (!valid) return

    userStore.setOnboardingData({ major: form.major.trim() })
    router.push({ name: 'onboarding-interests' })
  })
}

function handlePrev(): void {
  router.push({ name: 'onboarding-role' })
}
</script>

<style lang="scss" scoped>
.step-major {
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

  &__form {
    margin-bottom: 24px;
  }

  &__suggestions {
    margin-bottom: 28px;
  }

  &__suggestions-title {
    font-size: 14px;
    color: #888;
    margin-bottom: 12px;
    text-align: center;
  }

  &__tags {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
  }

  &__tag {
    font-size: 14px;
    padding: 6px 14px;
    border-radius: 16px;
    transition: all 0.2s;
  }

  &__action {
    display: flex;
    justify-content: center;
    gap: 16px;
  }
}
</style>
