<template>
  <div class="enrolled-courses" v-loading="loading">
    <el-empty
      v-if="!loading && courses.length === 0"
      description="暂无已选课程"
      :image-size="70"
    />

    <div v-else class="enrolled-courses__list">
      <article
        v-for="course in courses"
        :key="course.id"
        class="enrolled-courses__item"
        role="button"
        tabindex="0"
        :aria-label="`查看${course.name}知识图谱`"
        @click="openCourseGraph(course)"
        @keydown.enter.prevent="openCourseGraph(course)"
        @keydown.space.prevent="openCourseGraph(course)"
      >
        <div class="enrolled-courses__header">
          <div>
            <h4>{{ course.name }}</h4>
            <el-tag size="small" effect="plain">{{ course.semester }}</el-tag>
          </div>
          <el-button type="primary" link>
            查看课程图谱
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>

        <dl class="enrolled-courses__details">
          <div>
            <dt><el-icon><Location /></el-icon>上课地点</dt>
            <dd>{{ course.location || '待安排' }}</dd>
          </div>
          <div>
            <dt><el-icon><Clock /></el-icon>上课时间</dt>
            <dd>{{ course.class_time || '待安排' }}</dd>
          </div>
          <div>
            <dt><el-icon><User /></el-icon>任课教师</dt>
            <dd>{{ course.teacher_name }}</dd>
          </div>
          <div>
            <dt><el-icon><Calendar /></el-icon>上课周次</dt>
            <dd>{{ course.class_weeks || '待安排' }}</dd>
          </div>
        </dl>
      </article>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, Calendar, Clock, Location, User } from '@element-plus/icons-vue'
import { courseApi, type EnrolledCourse } from '@/services/course'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const courses = ref<EnrolledCourse[]>([])

async function loadCourses(): Promise<void> {
  loading.value = true
  try {
    courses.value = await courseApi.listMyCourses()
  } catch (error) {
    console.error('获取选课列表失败:', error)
    courses.value = []
  } finally {
    loading.value = false
  }
}

function openCourseGraph(course: EnrolledCourse): void {
  router.push({
    name: 'GraphDetail',
    params: {
      sceneType: String(route.params.sceneType || 'classroom'),
      id: course.graph_subject_id,
    },
    query: { course_id: String(course.id), course_name: course.name },
  })
}

onMounted(loadCourses)
</script>

<style lang="scss" scoped>
.enrolled-courses {
  min-height: 220px;

  &__list {
    display: grid;
    gap: 12px;
  }

  &__item {
    padding: 14px 16px;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    background: #fff;
    cursor: pointer;
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;

    &:hover,
    &:focus-visible {
      border-color: #409eff;
      box-shadow: 0 5px 16px rgba(64, 158, 255, 0.16);
      transform: translateY(-1px);
      outline: none;
    }
  }

  &__header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;

    h4 {
      display: inline-block;
      margin: 0 8px 0 0;
      color: #303133;
      font-size: 15px;
    }
  }

  &__details {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px 20px;
    margin: 0;

    div {
      min-width: 0;
    }

    dt {
      display: flex;
      align-items: center;
      gap: 4px;
      margin-bottom: 3px;
      color: #909399;
      font-size: 12px;
    }

    dd {
      margin: 0;
      overflow: hidden;
      color: #606266;
      font-size: 13px;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

@media (max-width: 640px) {
  .enrolled-courses__details {
    grid-template-columns: 1fr;
  }
}
</style>
