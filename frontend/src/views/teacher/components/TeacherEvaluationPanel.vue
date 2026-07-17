<template>
  <el-card shadow="never" class="teacher-evaluation-panel">
    <template #header>
      <div class="panel-header">
        <div>
          <h3>教师评价</h3>
          <p>选择课程和学生，评价将直接显示在学生成长档案中。</p>
        </div>
        <el-button
          v-if="selectedStudent"
          link
          type="primary"
          @click="openGrowthProfile"
        >
          查看成长档案
        </el-button>
      </div>
    </template>

    <el-form label-position="top" class="evaluation-form">
      <div class="selector-grid">
        <el-form-item label="课程" required>
          <el-select
            v-model="selectedCourseId"
            placeholder="请选择课程"
            style="width: 100%"
            @change="loadStudents"
          >
            <el-option
              v-for="course in courses"
              :key="course.id"
              :label="course.name"
              :value="course.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="学生" required>
          <el-select
            v-model="selectedStudentId"
            :loading="studentsLoading"
            :disabled="!selectedCourseId"
            filterable
            placeholder="请选择学生"
            style="width: 100%"
          >
            <el-option
              v-for="student in students"
              :key="student.id"
              :label="student.nickname"
              :value="student.id"
            >
              <span>{{ student.nickname }}</span>
              <span class="student-meta">{{ student.grade || '未设置年级' }}</span>
            </el-option>
          </el-select>
        </el-form-item>
      </div>

      <div class="selector-grid">
        <el-form-item label="评价类型" required>
          <el-select v-model="evaluationType" style="width: 100%">
            <el-option label="综合评价" value="overall" />
            <el-option label="学业表现" value="academic" />
            <el-option label="学习态度" value="attitude" />
            <el-option label="进步评价" value="improvement" />
          </el-select>
        </el-form-item>

        <el-form-item label="评分" required>
          <el-rate v-model="rating" show-score :max="5" />
        </el-form-item>
      </div>

      <el-form-item label="评价内容" required>
        <el-input
          v-model="content"
          type="textarea"
          :rows="3"
          maxlength="500"
          show-word-limit
          placeholder="请输入对该学生本课程学习表现的评价"
        />
      </el-form-item>

      <el-form-item label="学习建议">
        <el-input
          v-model="suggestion"
          type="textarea"
          :rows="2"
          maxlength="300"
          show-word-limit
          placeholder="可填写后续学习建议"
        />
      </el-form-item>

      <div class="form-footer">
        <span>发布后学生可在成长档案的“教师评价”栏目查看课程和任课教师。</span>
        <el-button type="primary" :loading="submitting" @click="submitEvaluation">
          发布评价
        </el-button>
      </div>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { growthApi } from '@/services/growth'

export interface TeacherCourseOption {
  id: number
  name: string
}

interface StudentOption {
  id: number
  nickname: string
  grade: string | null
  school: string | null
}

const props = defineProps<{
  courses: TeacherCourseOption[]
}>()

const router = useRouter()
const selectedCourseId = ref<number>()
const selectedStudentId = ref<number>()
const students = ref<StudentOption[]>([])
const studentsLoading = ref(false)
const submitting = ref(false)
const evaluationType = ref('overall')
const rating = ref(5)
const content = ref('')
const suggestion = ref('')

const selectedStudent = computed(() =>
  students.value.find((student) => student.id === selectedStudentId.value),
)

watch(
  () => props.courses,
  async (courses) => {
    if (!selectedCourseId.value && courses.length > 0) {
      selectedCourseId.value = courses[0].id
      await loadStudents()
    }
  },
  { immediate: true },
)

async function loadStudents(): Promise<void> {
  selectedStudentId.value = undefined
  students.value = []
  if (!selectedCourseId.value) return
  studentsLoading.value = true
  try {
    const response = await api.get('/teachers/students', {
      params: { course_id: selectedCourseId.value },
    })
    students.value = response.data as StudentOption[]
  } catch (error) {
    console.error('加载课程学生失败:', error)
  } finally {
    studentsLoading.value = false
  }
}

async function submitEvaluation(): Promise<void> {
  if (!selectedCourseId.value) {
    ElMessage.warning('请先选择课程')
    return
  }
  if (!selectedStudentId.value) {
    ElMessage.warning('请选择需要评价的学生')
    return
  }
  if (!content.value.trim()) {
    ElMessage.warning('请输入评价内容')
    return
  }

  submitting.value = true
  try {
    await growthApi.createEvaluation({
      student_id: selectedStudentId.value,
      course_id: selectedCourseId.value,
      evaluation_type: evaluationType.value,
      rating: rating.value,
      content: content.value.trim(),
      suggestion: suggestion.value.trim() || undefined,
      is_visible: true,
    })
    content.value = ''
    suggestion.value = ''
    evaluationType.value = 'overall'
    rating.value = 5
    ElMessage.success('评价已发布，并已同步到学生成长档案')
  } finally {
    submitting.value = false
  }
}

function openGrowthProfile(): void {
  if (!selectedStudent.value) return
  router.push({
    name: 'TeacherStudentGrowthProfile',
    params: { studentId: selectedStudent.value.id },
    query: {
      name: selectedStudent.value.nickname,
      grade: selectedStudent.value.grade || undefined,
      school: selectedStudent.value.school || undefined,
    },
  })
}
</script>

<style lang="scss" scoped>
.teacher-evaluation-panel {
  margin-top: 16px;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;

  h3 { margin: 0 0 5px; }
  p { margin: 0; color: #909399; font-size: 12px; line-height: 1.5; }
}

.selector-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.student-meta {
  float: right;
  margin-left: 16px;
  color: #909399;
  font-size: 12px;
}

.form-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;

  span { color: #909399; font-size: 12px; line-height: 1.5; }
}

@media (max-width: 720px) {
  .selector-grid { grid-template-columns: 1fr; gap: 0; }
  .form-footer { align-items: stretch; flex-direction: column; }
}
</style>
