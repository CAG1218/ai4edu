<template>
  <div class="graph-square">
    <div class="graph-square__header">
      <h2>知识图谱广场</h2>
      <div class="graph-square__actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索学科..."
          prefix-icon="Search"
          clearable
          class="graph-square__search"
          @input="handleSearch"
        />
        <el-select v-model="sortBy" placeholder="排序方式" style="width: 140px" @change="handleSort">
          <el-option label="默认" value="default" />
          <el-option label="节点数" value="node_count" />
          <el-option label="完整度" value="completeness" />
          <el-option label="名称" value="name" />
        </el-select>
      </div>
    </div>

    <div v-loading="graphStore.loading" class="graph-square__grid">
      <el-row :gutter="16">
        <el-col
          v-for="subject in filteredStats"
          :key="subject.id"
          :xs="12"
          :sm="8"
          :md="6"
          :lg="4"
        >
          <el-card
            shadow="hover"
            class="graph-square__card"
            @click="goToDetail(subject.id)"
          >
            <div class="graph-square__card-icon" :style="{ background: subject.color + '20', color: subject.color }">
              <el-icon :size="32"><component :is="subject.icon" /></el-icon>
            </div>
            <h3 class="graph-square__card-name">{{ subject.name }}</h3>
            <div class="graph-square__card-stats">
              <span>{{ subject.node_count }} 个知识点</span>
            </div>
            <div class="graph-square__card-progress">
              <span class="graph-square__card-progress-label">完整度</span>
              <el-progress
                type="circle"
                :width="48"
                :percentage="subject.completeness"
                :stroke-width="4"
                :color="subject.color"
              />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-empty v-if="filteredStats.length === 0 && !graphStore.loading" description="暂无学科数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AI4Edu 知识图谱广场视图
 * 12学科分类卡片网格 + 搜索 + 排序
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGraphStore } from '@/stores/graph'
import type { SquareStat } from '@/services/graph'

const router = useRouter()
const graphStore = useGraphStore()

const searchQuery = ref('')
const sortBy = ref('default')

const filteredStats = computed(() => {
  let list = [...graphStore.squareStats]

  // 搜索过滤
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter((s) => s.name.toLowerCase().includes(q) || s.id.toLowerCase().includes(q))
  }

  // 排序
  switch (sortBy.value) {
    case 'node_count':
      list.sort((a, b) => b.node_count - a.node_count)
      break
    case 'completeness':
      list.sort((a, b) => b.completeness - a.completeness)
      break
    case 'name':
      list.sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
      break
  }

  return list
})

function handleSearch(): void {
  // 搜索由 computed 自动处理
}

function handleSort(): void {
  // 排序由 computed 自动处理
}

function goToDetail(subjectId: string): void {
  router.push({
    name: 'GraphDetail',
    params: { id: subjectId },
  })
}

onMounted(() => {
  graphStore.loadSquareStats()
})
</script>

<style lang="scss" scoped>
.graph-square {
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);

    h2 {
      font-size: 22px;
      font-weight: 700;
      color: var(--color-text-primary);
    }
  }

  &__actions {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  &__search {
    width: 200px;
  }

  &__grid {
    min-height: 300px;
  }

  &__card {
    cursor: pointer;
    text-align: center;
    margin-bottom: var(--spacing-md);
    transition: transform 0.15s ease;

    &:hover {
      transform: translateY(-4px);
    }

    :deep(.el-card__body) {
      padding: 20px;
    }
  }

  &__card-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    border-radius: 50%;
    margin-bottom: 12px;
  }

  &__card-name {
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary);
    margin-bottom: 6px;
  }

  &__card-stats {
    font-size: 13px;
    color: var(--color-text-secondary);
    margin-bottom: 12px;
  }

  &__card-progress {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
  }

  &__card-progress-label {
    font-size: 12px;
    color: var(--color-text-secondary);
  }
}
</style>
