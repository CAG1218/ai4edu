<template>
  <div class="teacher-ai">
    <header class="teacher-ai__header">
      <div>
        <h1>教师 AI 助手</h1>
        <p>基于您的教案、课程与班级学情进行独立问答</p>
      </div>
      <div class="teacher-ai__model">
        <span></span>
        DeepSeek · 教师专用链路
      </div>
    </header>

    <el-card shadow="never" class="teacher-ai__context-card" v-loading="contextLoading">
      <div class="teacher-ai__context-head">
        <div>
          <strong>问答材料范围</strong>
          <p>选择课程后，回答将仅依据该课程的教案和班级情况。</p>
        </div>
        <el-select
          v-model="selectedCourseId"
          clearable
          placeholder="全部任教课程"
          style="width: 240px"
          @change="loadContext"
        >
          <el-option
            v-for="course in courseOptions"
            :key="course.id"
            :label="course.name"
            :value="course.id"
          />
        </el-select>
      </div>

      <div class="teacher-ai__stats">
        <div><strong>{{ context.summary.course_count }}</strong><span>课程</span></div>
        <div><strong>{{ context.summary.lesson_plan_count }}</strong><span>教案</span></div>
        <div><strong>{{ context.summary.resource_count }}</strong><span>教师资源</span></div>
        <div><strong>{{ context.summary.student_count }}</strong><span>学生</span></div>
        <div><strong>{{ context.summary.diagnosis_count }}</strong><span>诊断</span></div>
        <div><strong>{{ context.summary.classroom_count }}</strong><span>课堂</span></div>
        <div><strong>{{ context.summary.classroom_record_count }}</strong><span>课堂记录</span></div>
      </div>
      <div class="teacher-ai__sources">
        <span>当前可用材料：</span>
        <el-tag v-for="source in context.sources" :key="source" size="small" effect="plain">{{ source }}</el-tag>
        <span v-if="context.sources.length === 0">暂无材料，助手会提示需要补充的数据</span>
      </div>
    </el-card>

    <el-card shadow="never" class="teacher-ai__chat-card">
      <div ref="messageContainer" class="teacher-ai__messages">
        <div
          v-for="(message, index) in messages"
          :key="index"
          :class="['teacher-ai__message', `teacher-ai__message--${message.role}`]"
        >
          <div class="teacher-ai__avatar">{{ message.role === 'assistant' ? 'AI' : '我' }}</div>
          <div class="teacher-ai__bubble">
            <div>{{ message.content }}</div>
            <small v-if="message.model">{{ message.model }}</small>
          </div>
        </div>
        <div v-if="sending" class="teacher-ai__message teacher-ai__message--assistant">
          <div class="teacher-ai__avatar">AI</div>
          <div class="teacher-ai__bubble teacher-ai__bubble--loading">
            <i></i><i></i><i></i>
          </div>
        </div>
      </div>

      <div class="teacher-ai__suggestions">
        <button v-for="question in suggestions" :key="question" @click="useSuggestion(question)">
          {{ question }}
        </button>
      </div>

      <div class="teacher-ai__composer">
        <el-input
          v-model="input"
          type="textarea"
          :rows="3"
          resize="none"
          maxlength="4000"
          show-word-limit
          placeholder="例如：根据本周教案和诊断结果，我应该如何调整下节课？"
          :disabled="sending"
          @keydown.enter.exact.prevent="send"
        />
        <el-button type="primary" :loading="sending" :disabled="!input.trim()" @click="send">
          发送
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  teacherAIApi,
  type TeacherAIContext,
  type TeacherAIContextSummary,
  type TeacherAICourse,
  type TeacherAIHistoryMessage,
} from '@/services/teacher-ai'

interface ChatMessage extends TeacherAIHistoryMessage {
  model?: string
}

const emptySummary = (): TeacherAIContextSummary => ({
  course_count: 0,
  lesson_plan_count: 0,
  resource_count: 0,
  student_count: 0,
  diagnosis_count: 0,
  classroom_count: 0,
  classroom_record_count: 0,
})

const context = ref<TeacherAIContext>({ courses: [], summary: emptySummary(), sources: [] })
const courseOptions = ref<TeacherAICourse[]>([])
const selectedCourseId = ref<number | undefined>()
const contextLoading = ref(false)
const sending = ref(false)
const input = ref('')
const messageContainer = ref<HTMLElement | null>(null)
const messages = ref<ChatMessage[]>([
  { role: 'assistant', content: '您好，我是教师工作台专属 AI 助手。您可以结合教案和班级学情向我提问。' },
])

const suggestions = [
  '概括当前班级最需要关注的学习问题',
  '根据现有教案提出分层教学建议',
  '分析薄弱知识点并设计下节课活动',
  '为当前课程制定一周复习安排',
]

async function loadContext(): Promise<void> {
  contextLoading.value = true
  try {
    const result = await teacherAIApi.getContext(selectedCourseId.value)
    context.value = result
    if (!selectedCourseId.value) courseOptions.value = result.courses
  } catch (error) {
    console.error('加载教师AI材料失败:', error)
    ElMessage.error('加载教案和班级材料失败')
  } finally {
    contextLoading.value = false
  }
}

function useSuggestion(question: string): void {
  input.value = question
}

async function scrollToBottom(): Promise<void> {
  await nextTick()
  if (messageContainer.value) messageContainer.value.scrollTop = messageContainer.value.scrollHeight
}

async function send(): Promise<void> {
  const content = input.value.trim()
  if (!content || sending.value) return

  const history = messages.value
    .filter((message, index) => index > 0 && message.content.trim())
    .slice(-12)
    .map(({ role, content: historyContent }) => ({ role, content: historyContent }))

  messages.value.push({ role: 'user', content })
  input.value = ''
  sending.value = true
  await scrollToBottom()
  try {
    const reply = await teacherAIApi.sendMessage(content, history, selectedCourseId.value)
    messages.value.push({ role: 'assistant', content: reply.answer, model: reply.model })
    context.value.summary = reply.context_summary
    context.value.sources = reply.sources
  } catch (error) {
    console.error('教师AI问答失败:', error)
    ElMessage.error('教师 AI 暂时无法回答，请稍后重试')
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

onMounted(loadContext)
</script>

<style lang="scss" scoped>
.teacher-ai {
  max-width: 1180px;
  margin: 0 auto;

  &__header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 18px;

    h1 { margin: 0 0 6px; font-size: 25px; }
    p { margin: 0; color: #909399; }
  }

  &__model {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 9px 14px;
    color: #606266;
    background: #f3f7ff;
    border-radius: 18px;
    font-size: 13px;

    span { width: 9px; height: 9px; background: #67c23a; border-radius: 50%; }
  }

  &__context-card { margin-bottom: 16px; }
  &__context-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 15px;
    p { margin: 5px 0 0; color: #909399; font-size: 13px; }
  }

  &__stats {
    display: grid;
    grid-template-columns: repeat(7, minmax(0, 1fr));
    gap: 10px;
    margin-bottom: 13px;

    div { padding: 11px; text-align: center; background: #f7f9fc; border-radius: 8px; }
    strong { display: block; margin-bottom: 3px; color: #303133; font-size: 19px; }
    span { color: #909399; font-size: 12px; }
  }

  &__sources { display: flex; align-items: center; flex-wrap: wrap; gap: 7px; color: #909399; font-size: 12px; }
  &__chat-card :deep(.el-card__body) { padding: 0; }
  &__messages { height: 430px; padding: 22px; overflow-y: auto; background: #f8fafc; }
  &__message { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 18px; }
  &__message--user { flex-direction: row-reverse; }
  &__avatar { display: grid; flex: 0 0 34px; height: 34px; place-items: center; color: #fff; background: #409eff; border-radius: 50%; font-size: 12px; font-weight: 700; }
  &__message--user &__avatar { background: #909399; }
  &__bubble { max-width: 76%; padding: 12px 15px; color: #303133; white-space: pre-wrap; line-height: 1.7; background: #fff; border-radius: 4px 14px 14px; box-shadow: 0 1px 4px rgba(0, 0, 0, .06); }
  &__message--user &__bubble { color: #fff; background: #409eff; border-radius: 14px 4px 14px 14px; }
  &__bubble small { display: block; margin-top: 8px; color: #a8abb2; font-size: 11px; }
  &__bubble--loading { display: flex; gap: 5px; padding: 17px; }
  &__bubble--loading i { width: 6px; height: 6px; background: #a8abb2; border-radius: 50%; animation: pulse 1s infinite alternate; }
  &__bubble--loading i:nth-child(2) { animation-delay: .2s; }
  &__bubble--loading i:nth-child(3) { animation-delay: .4s; }
  &__suggestions { display: flex; flex-wrap: wrap; gap: 8px; padding: 13px 18px 0; border-top: 1px solid #ebeef5; }
  &__suggestions button { padding: 7px 11px; color: #606266; background: #f5f7fa; border: 1px solid #e4e7ed; border-radius: 14px; cursor: pointer; }
  &__suggestions button:hover { color: #409eff; border-color: #a0cfff; }
  &__composer { display: flex; align-items: flex-end; gap: 12px; padding: 14px 18px 18px; }
}

@keyframes pulse { from { opacity: .35; transform: translateY(1px); } to { opacity: 1; transform: translateY(-2px); } }

@media (max-width: 900px) {
  .teacher-ai__stats { grid-template-columns: repeat(3, 1fr); }
  .teacher-ai__context-head, .teacher-ai__header { flex-direction: column; }
}
</style>
