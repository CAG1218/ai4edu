<template>
  <div class="class-diagnosis" v-loading="loading">
    <div class="header">
      <div><h2>班级诊断</h2><p>依据已完成的学习诊断汇总课程掌握情况</p></div>
      <el-select v-model="selectedCourse" placeholder="选择课程" clearable style="width: 220px" @change="loadDiagnosis">
        <el-option v-for="course in courses" :key="course.id" :label="course.name" :value="course.id" />
      </el-select>
    </div>

    <el-row :gutter="16" class="summary">
      <el-col :xs="12" :sm="8"><el-card shadow="never"><span>诊断次数</span><strong>{{ diagnosis.total_diagnoses }}</strong></el-card></el-col>
      <el-col :xs="12" :sm="8"><el-card shadow="never"><span>平均得分</span><strong>{{ diagnosis.average_score || '--' }}</strong></el-card></el-col>
      <el-col :xs="12" :sm="8"><el-card shadow="never"><span>薄弱知识点</span><strong>{{ diagnosis.weak_points.length }}</strong></el-card></el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="14">
        <el-card shadow="never">
          <template #header><h3>知识点掌握情况</h3></template>
          <div v-if="diagnosis.knowledge_distribution.length" class="heatmap-grid">
            <div v-for="item in diagnosis.knowledge_distribution" :key="item.name" class="heatmap-cell" :style="{ backgroundColor: getHeatColor(item.mastery) }">
              <span>{{ item.name }}</span><strong>{{ item.mastery }}%</strong>
            </div>
          </div>
          <el-empty v-else description="当前课程尚无已完成的诊断数据" :image-size="90" />
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card shadow="never">
          <template #header><h3>薄弱知识点</h3></template>
          <div v-if="diagnosis.weak_points.length" class="weak-list">
            <div v-for="(item, index) in diagnosis.weak_points" :key="item.name" class="weak-item">
              <b>{{ index + 1 }}</b><span>{{ item.name }}</span><el-progress :percentage="item.mastery" :show-text="false" /><strong>{{ item.mastery }}%</strong>
            </div>
          </div>
          <el-empty v-else description="暂无薄弱知识点" :image-size="70" />
        </el-card>

        <el-card shadow="never" class="suggestions-card">
          <template #header><h3>教学建议</h3></template>
          <ul v-if="diagnosis.suggestions.length"><li v-for="item in diagnosis.suggestions" :key="item">{{ item }}</li></ul>
          <el-empty v-else description="积累诊断数据后将显示教学建议" :image-size="70" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '@/services/api'

interface Course { id: number; name: string }
interface KnowledgePoint { name: string; mastery: number }
interface DiagnosisData {
  total_diagnoses: number
  average_score: number
  knowledge_distribution: KnowledgePoint[]
  weak_points: KnowledgePoint[]
  suggestions: string[]
}

const loading = ref(false)
const courses = ref<Course[]>([])
const selectedCourse = ref<number | undefined>()
const diagnosis = ref<DiagnosisData>({ total_diagnoses: 0, average_score: 0, knowledge_distribution: [], weak_points: [], suggestions: [] })

function getHeatColor(value: number): string {
  if (value >= 80) return '#4caf50'
  if (value >= 60) return '#8bc34a'
  if (value >= 40) return '#ffc107'
  if (value >= 20) return '#ff9800'
  return '#f44336'
}

async function loadDiagnosis(): Promise<void> {
  loading.value = true
  try {
    const response = await api.get('/teachers/analytics', { params: { course_id: selectedCourse.value || undefined } })
    diagnosis.value = { ...diagnosis.value, ...(response.data as DiagnosisData) }
  } finally { loading.value = false }
}

onMounted(async () => {
  loading.value = true
  try {
    const response = await api.get('/teachers/courses')
    courses.value = response.data as Course[]
    selectedCourse.value = courses.value[0]?.id
    await loadDiagnosis()
  } finally { loading.value = false }
})
</script>

<style lang="scss" scoped>
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; h2 { margin: 0 0 4px; } p { margin: 0; color: #909399; } }
.summary { margin-bottom: 16px; :deep(.el-card__body) { display: flex; justify-content: space-between; align-items: center; } span { color: #606266; } strong { font-size: 22px; } }
h3 { margin: 0; font-size: 16px; }
.heatmap-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.heatmap-cell { min-height: 70px; padding: 10px; color: #fff; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; text-align: center; }
.weak-list { display: flex; flex-direction: column; gap: 14px; }
.weak-item { display: grid; grid-template-columns: 26px minmax(80px, 1fr) 1fr 48px; align-items: center; gap: 8px; b { width: 24px; height: 24px; display: grid; place-items: center; color: #fff; background: #f56c6c; border-radius: 50%; } strong { text-align: right; color: #f56c6c; } }
.suggestions-card { margin-top: 16px; ul { padding-left: 20px; margin: 0; } li { margin-bottom: 10px; color: #606266; line-height: 1.6; } }
@media (max-width: 768px) { .header { align-items: flex-start; gap: 12px; flex-direction: column; } .heatmap-grid { grid-template-columns: repeat(2, 1fr); } }
</style>
