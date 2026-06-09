<template>
  <div class="search-view">
    <div class="search-view__header">
      <h2>搜索</h2>
      <div class="search-view__bar">
        <el-input
          v-model="searchStore.query"
          placeholder="搜索资源、笔记、知识点、课程..."
          prefix-icon="Search"
          clearable
          size="large"
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button @click="handleSearch">搜索</el-button>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 分类Tab -->
    <el-tabs v-model="searchStore.searchType" @tab-change="handleTypeChange">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="笔记" name="note" />
      <el-tab-pane label="资源" name="resource" />
      <el-tab-pane label="知识点" name="graph_node" />
      <el-tab-pane label="课程" name="course" />
    </el-tabs>

    <!-- 高级筛选 -->
    <div class="search-view__filters">
      <el-select v-model="dateRange" placeholder="时间范围" clearable size="small" style="width: 140px">
        <el-option label="全部时间" value="" />
        <el-option label="最近一天" value="1d" />
        <el-option label="最近一周" value="7d" />
        <el-option label="最近一月" value="30d" />
      </el-select>
    </div>

    <!-- 搜索结果 -->
    <div v-loading="searchStore.loading" class="search-view__results">
      <div v-if="searchStore.hasResults">
        <div v-for="item in searchStore.results" :key="item.id" class="search-view__result-item">
          <div class="search-view__result-header">
            <el-tag size="small" :type="getTypeTagType(item.source?.doc_type)">{{ getTypeLabel(item.source?.doc_type) }}</el-tag>
            <span class="search-view__result-score">相关度: {{ (item.rrf_score || item.score || 0).toFixed(4) }}</span>
          </div>
          <h3 class="search-view__result-title" v-html="getHighlightedTitle(item)" />
          <p v-if="getHighlightedContent(item)" class="search-view__result-content" v-html="getHighlightedContent(item)" />
          <div class="search-view__result-meta">
            <span v-if="item.source?.doc_type">{{ getTypeLabel(item.source.doc_type) }}</span>
          </div>
        </div>
      </div>
      <el-empty v-else-if="searchStore.query && !searchStore.loading" description="未找到相关结果" />
    </div>

    <!-- 分页 -->
    <div v-if="searchStore.total > 20" class="search-view__pagination">
      <el-pagination
        layout="prev, pager, next"
        :total="searchStore.total"
        :page-size="20"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AI4Edu 搜索结果视图
 * 分类Tab + 高亮关键词 + 高级筛选 + 分页
 */
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useSearchStore } from '@/stores/search'
import type { SearchResult } from '@/services/search'

const route = useRoute()
const searchStore = useSearchStore()

const dateRange = ref('')

function getTypeTagType(type?: string): string {
  const map: Record<string, string> = {
    resource: 'success',
    note: 'primary',
    graph_node: 'warning',
    course: 'danger',
  }
  return map[type || ''] || 'info'
}

function getTypeLabel(type?: string): string {
  const map: Record<string, string> = {
    resource: '资源',
    note: '笔记',
    graph_node: '知识点',
    course: '课程',
  }
  return map[type || ''] || '其他'
}

function getHighlightedTitle(item: SearchResult): string {
  const title = (item.source?.title as string) || (item.source?.name as string) || '无标题'
  if (item.highlight?.title?.[0]) {
    return item.highlight.title[0]
  }
  return title
}

function getHighlightedContent(item: SearchResult): string {
  if (item.highlight?.content?.length) {
    return item.highlight.content.slice(0, 2).join('... ')
  }
  const content = (item.source?.content as string) || (item.source?.description as string) || ''
  return content ? content.slice(0, 200) + '...' : ''
}

function handleSearch(): void {
  searchStore.search()
}

function handleTypeChange(): void {
  if (searchStore.query) {
    searchStore.search()
  }
}

function handlePageChange(page: number): void {
  searchStore.search()
}

onMounted(() => {
  const q = route.query.q as string
  if (q) {
    searchStore.query = q
    searchStore.search(q)
  }
})

watch(() => route.query.q, (q) => {
  if (q && typeof q === 'string') {
    searchStore.query = q
    searchStore.search(q)
  }
})
</script>

<style lang="scss" scoped>
.search-view {
  &__header {
    margin-bottom: var(--spacing-lg);

    h2 {
      font-size: 22px;
      font-weight: 700;
      color: var(--color-text-primary);
      margin-bottom: 12px;
    }
  }

  &__bar {
    max-width: 600px;
  }

  &__filters {
    margin: 12px 0;
  }

  &__results {
    min-height: 300px;
  }

  &__result-item {
    padding: 16px;
    border-bottom: 1px solid var(--color-border-light);

    &:hover {
      background: var(--color-bg-secondary);
    }
  }

  &__result-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }

  &__result-score {
    font-size: 12px;
    color: var(--color-text-secondary);
  }

  &__result-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary);
    margin-bottom: 4px;
    cursor: pointer;

    &:hover {
      color: var(--color-info);
    }

    :deep(mark) {
      background: #fff3cd;
      color: inherit;
      padding: 0 2px;
    }
  }

  &__result-content {
    font-size: 14px;
    color: var(--color-text-secondary);
    line-height: 1.6;
    margin-bottom: 6px;

    :deep(mark) {
      background: #fff3cd;
      color: inherit;
      padding: 0 2px;
    }
  }

  &__result-meta {
    font-size: 12px;
    color: var(--color-text-placeholder);
  }

  &__pagination {
    display: flex;
    justify-content: center;
    margin-top: var(--spacing-lg);
  }
}
</style>
