<template>
  <div class="lesson-plan">
    <div class="lesson-plan__header">
      <h2>AI 备课助手</h2>
      <p class="lesson-plan__subtitle">输入课程目标，AI帮你生成完整教案</p>
    </div>

    <div class="lesson-plan__body">
      <!-- 左侧：输入+生成 -->
      <div class="lesson-plan__input-panel">
        <el-form :model="planForm" label-position="top">
          <el-form-item label="课程名称">
            <el-input v-model="planForm.courseName" placeholder="如：高等数学" />
          </el-form-item>
          <el-form-item label="教学目标">
            <el-input
              v-model="planForm.objectives"
              type="textarea"
              :rows="3"
              placeholder="描述本次课的教学目标..."
            />
          </el-form-item>
          <el-form-item label="知识点">
            <el-select
              v-model="planForm.knowledgePoints"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="添加知识点"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="教学时长">
            <el-select v-model="planForm.duration" style="width: 100%">
              <el-option label="1课时（45分钟）" value="45" />
              <el-option label="2课时（90分钟）" value="90" />
              <el-option label="3课时（135分钟）" value="135" />
            </el-select>
          </el-form-item>
          <el-form-item label="学生水平">
            <el-radio-group v-model="planForm.studentLevel">
              <el-radio-button value="basic">基础</el-radio-button>
              <el-radio-button value="intermediate">中等</el-radio-button>
              <el-radio-button value="advanced">提高</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="generating" @click="generatePlan" style="width: 100%">
              <el-icon><MagicStick /></el-icon> AI 生成教案
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 右侧：教案预览和编辑 -->
      <div class="lesson-plan__preview-panel">
        <div v-if="!generatedPlan && !generating" class="lesson-plan__empty">
          <el-icon :size="64" color="#dcdfe6"><Document /></el-icon>
          <p>在左侧输入课程信息，AI将为你生成完整教案</p>
        </div>

        <div v-if="generating" class="lesson-plan__generating">
          <el-icon :size="40" class="lesson-plan__spin"><Loading /></el-icon>
          <p>AI正在生成教案...</p>
        </div>

        <div v-if="generatedPlan && !generating" class="lesson-plan__result">
          <div class="lesson-plan__result-header">
            <h3>{{ generatedPlan.title }}</h3>
            <div class="lesson-plan__result-actions">
              <el-button size="small" @click="editPlan">编辑</el-button>
              <el-button size="small" type="primary" @click="savePlan">保存教案</el-button>
            </div>
          </div>
          <div class="lesson-plan__result-content">
            <section class="lesson-plan__section">
              <h4>教学目标</h4>
              <ul>
                <li v-for="(obj, idx) in generatedPlan.objectives" :key="idx">{{ obj }}</li>
              </ul>
            </section>
            <section class="lesson-plan__section">
              <h4>教学过程</h4>
              <div v-for="(step, idx) in generatedPlan.steps" :key="idx" class="lesson-plan__step">
                <div class="lesson-plan__step-header">
                  <el-tag size="small" type="primary">步骤 {{ idx + 1 }}</el-tag>
                  <span class="lesson-plan__step-title">{{ step.title }}</span>
                  <span class="lesson-plan__step-duration">{{ step.duration }}分钟</span>
                </div>
                <p class="lesson-plan__step-content">{{ step.content }}</p>
              </div>
            </section>
            <section class="lesson-plan__section">
              <h4>课后作业</h4>
              <ul>
                <li v-for="(hw, idx) in generatedPlan.homework" :key="idx">{{ hw }}</li>
              </ul>
            </section>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部：相关资源推荐 -->
    <div v-if="generatedPlan" class="lesson-plan__resources">
      <h3>相关资源推荐</h3>
      <el-row :gutter="12">
        <el-col :xs="12" :sm="8" :md="6" v-for="res in recommendedResources" :key="res.title">
          <div class="lesson-plan__resource-card" @click="goToResource(res.id)">
            <el-icon :size="20" color="#1976D2"><Document /></el-icon>
            <div class="lesson-plan__resource-info">
              <span class="lesson-plan__resource-title">{{ res.title }}</span>
              <span class="lesson-plan__resource-type">{{ res.type }}</span>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AI4Edu 备课助手页
 * 左侧输入+AI生成 + 右侧教案预览 + 底部资源推荐
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MagicStick, Document, Loading } from '@element-plus/icons-vue'
import api from '@/services/api'

const router = useRouter()

const generating = ref<boolean>(false)

const planForm = reactive({
  courseName: '',
  objectives: '',
  knowledgePoints: [] as string[],
  duration: '90',
  studentLevel: 'intermediate',
})

interface PlanStep {
  title: string
  duration: number
  content: string
}

interface GeneratedPlan {
  title: string
  objectives: string[]
  steps: PlanStep[]
  homework: string[]
}

const generatedPlan = ref<GeneratedPlan | null>(null)

const recommendedResources = ref([
  { id: 1, title: '微积分基础教程', type: 'PDF文档' },
  { id: 2, title: '极限与连续讲解', type: '视频' },
  { id: 3, title: '导数练习题集', type: 'PDF文档' },
  { id: 4, title: '微积分思维导图', type: '图片' },
])

async function generatePlan(): Promise<void> {
  if (!planForm.courseName.trim()) {
    ElMessage.warning('请输入课程名称')
    return
  }

  generating.value = true
  try {
    const response = await api.post('/teacher/lesson-plan/generate', {
      course_name: planForm.courseName,
      objectives: planForm.objectives,
      knowledge_points: planForm.knowledgePoints,
      duration: Number(planForm.duration),
      student_level: planForm.studentLevel,
    })
    generatedPlan.value = response.data as GeneratedPlan
    ElMessage.success('教案生成成功')
  } catch (error) {
    console.error('生成教案失败:', error)
    // 降级：使用模拟数据
    generatedPlan.value = {
      title: `${planForm.courseName} — 教案`,
      objectives: [
        '理解核心概念的定义和内涵',
        '掌握基本定理的证明思路',
        '能够运用所学知识解决实际问题',
      ],
      steps: [
        { title: '导入新课', duration: 10, content: '通过生活实例引入，激发学生兴趣，建立新旧知识的联系。' },
        { title: '概念讲解', duration: 25, content: '详细讲解核心概念，配合图示和示例，帮助学生建立直观理解。' },
        { title: '互动练习', duration: 20, content: '设计分层练习题，从基础到进阶，让不同水平的学生都有收获。' },
        { title: '总结提升', duration: 10, content: '回顾本节课重点，引导学生归纳知识框架，布置课后拓展任务。' },
      ],
      homework: [
        '完成课本P45 第1-5题',
        '整理本节课知识框架图',
        '预习下节内容并写出疑问',
      ],
    }
  } finally {
    generating.value = false
  }
}

function editPlan(): void {
  ElMessage.info('教案编辑功能开发中')
}

async function savePlan(): Promise<void> {
  try {
    await api.post('/teacher/lesson-plan/save', generatedPlan.value)
    ElMessage.success('教案已保存')
  } catch {
    ElMessage.error('保存失败')
  }
}

function goToResource(id: number): void {
  router.push({ name: 'ResourceDetail', params: { id } })
}
</script>

<style lang="scss" scoped>
.lesson-plan {
  &__header {
    margin-bottom: 20px;

    h2 {
      font-size: 22px;
      font-weight: 700;
      color: #303133;
      margin: 0 0 4px;
    }
  }

  &__subtitle {
    font-size: 14px;
    color: #909399;
    margin: 0;
  }

  &__body {
    display: flex;
    gap: 20px;
    min-height: 500px;
  }

  &__input-panel {
    width: 360px;
    flex-shrink: 0;
    background: #fff;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
    overflow-y: auto;
  }

  &__preview-panel {
    flex: 1;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
    overflow-y: auto;
  }

  &__empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 12px;
    color: #c0c4cc;
    padding: 40px;

    p {
      font-size: 14px;
    }
  }

  &__generating {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 16px;
    color: #909399;
  }

  &__spin {
    animation: spin 1s linear infinite;
  }

  &__result {
    padding: 24px;
  }

  &__result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 2px solid #1976D2;

    h3 {
      font-size: 20px;
      font-weight: 700;
      color: #303133;
      margin: 0;
    }
  }

  &__result-actions {
    display: flex;
    gap: 8px;
  }

  &__result-content {
    line-height: 1.8;
  }

  &__section {
    margin-bottom: 24px;

    h4 {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 12px;
      padding-left: 10px;
      border-left: 3px solid #1976D2;
    }

    ul {
      padding-left: 20px;
      margin: 0;

      li {
        margin-bottom: 6px;
        font-size: 14px;
        color: #606266;
      }
    }
  }

  &__step {
    margin-bottom: 16px;
    padding: 12px 16px;
    background: #fafafa;
    border-radius: 8px;
    border-left: 3px solid #1976D2;
  }

  &__step-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
  }

  &__step-title {
    font-size: 15px;
    font-weight: 600;
    color: #303133;
  }

  &__step-duration {
    font-size: 12px;
    color: #909399;
    margin-left: auto;
  }

  &__step-content {
    font-size: 14px;
    color: #606266;
    line-height: 1.6;
    margin: 0;
  }

  &__resources {
    margin-top: 24px;
    padding: 20px;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);

    h3 {
      font-size: 16px;
      font-weight: 600;
      margin: 0 0 16px;
    }
  }

  &__resource-card {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    background: #fafafa;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s;
    margin-bottom: 8px;

    &:hover {
      background: #f0f0f0;
    }
  }

  &__resource-info {
    display: flex;
    flex-direction: column;
  }

  &__resource-title {
    font-size: 14px;
    font-weight: 500;
    color: #303133;
  }

  &__resource-type {
    font-size: 12px;
    color: #909399;
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .lesson-plan {
    &__body {
      flex-direction: column;
    }
    &__input-panel {
      width: 100%;
    }
  }
}
</style>
