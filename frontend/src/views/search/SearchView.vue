<template>
  <div class="search-page">
    <section class="hero">
      <div>
        <p class="eyebrow">全文检索</p>
        <h1>在你的学习资料中找到答案</h1>
        <p class="subtitle">同时理解关键词和语义，检索笔记、课程资源、知识点与课程。</p>
      </div>
      <div class="search-bar">
        <el-input
          v-model="searchStore.query"
          size="large"
          clearable
          placeholder="例如：用直观方式解释梯度下降"
          @keyup.enter="runSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
          <template #append><el-button type="primary" @click="runSearch">搜索</el-button></template>
        </el-input>
      </div>
    </section>

    <section class="search-controls" aria-label="搜索筛选">
      <div class="control-row">
        <span class="control-label">检索方式</span>
        <el-radio-group v-model="searchStore.mode" size="small" @change="rerunSearch">
          <el-radio-button value="hybrid">智能混合</el-radio-button>
          <el-radio-button value="semantic">语义</el-radio-button>
          <el-radio-button value="keyword">关键词</el-radio-button>
        </el-radio-group>
        <el-tooltip content="智能混合会融合关键词精确匹配与语义相似度" placement="top">
          <el-icon class="help-icon"><QuestionFilled /></el-icon>
        </el-tooltip>
      </div>

      <div class="control-row control-row--wrap">
        <span class="control-label">搜索范围</span>
        <el-checkbox-group v-model="searchStore.sources" size="small" :min="1" @change="rerunSearch">
          <el-checkbox-button v-for="source in sourceOptions" :key="source.value" :value="source.value">
            {{ source.label }}
          </el-checkbox-button>
        </el-checkbox-group>
        <el-select v-model="searchStore.dateRange" clearable placeholder="全部时间" size="small" @change="rerunSearch">
          <el-option label="最近一天" value="1d" />
          <el-option label="最近一周" value="7d" />
          <el-option label="最近一月" value="30d" />
          <el-option label="最近一年" value="365d" />
        </el-select>
      </div>
    </section>

    <section v-loading="searchStore.loading" class="results" aria-live="polite">
      <div v-if="searchStore.query && !searchStore.loading" class="result-summary">
        <span>找到 {{ searchStore.total }} 条结果</span>
        <span v-if="searchStore.mode !== 'semantic'">关键词召回 {{ searchStore.keywordCount }}</span>
        <span v-if="searchStore.mode !== 'keyword'">语义召回 {{ searchStore.semanticCount }}</span>
      </div>

      <el-alert v-if="searchStore.error" :title="searchStore.error" type="error" show-icon :closable="false" />

      <button
        v-for="item in searchStore.results"
        :key="item.id"
        type="button"
        class="result-card"
        @click="openResult(item)"
      >
        <div class="result-card__top">
          <el-tag size="small" effect="plain" :type="typeMeta(item.source.doc_type).tag">
            {{ typeMeta(item.source.doc_type).label }}
          </el-tag>
          <span v-if="item.source.updated_at" class="result-date">{{ formatDate(item.source.updated_at) }}</span>
          <span class="result-score">相关度 {{ displayScore(item) }}</span>
        </div>
        <h2 v-html="safeHighlight(firstHighlight(item, 'title') || item.source.title || item.source.name || '无标题')" />
        <p v-if="resultExcerpt(item)" class="excerpt" v-html="safeHighlight(resultExcerpt(item))" />
        <p v-if="item.source.summary && !item.highlight.summary" class="summary">
          <span>智能摘要</span>{{ item.source.summary }}
        </p>
        <div class="result-footer">
          <el-tag v-for="tag in visibleTags(item)" :key="tag" size="small" type="info" round>{{ tag }}</el-tag>
          <span v-if="item.matched_by?.length" class="matched-by">
            {{ item.matched_by.includes('semantic') ? '语义匹配' : '关键词匹配' }}
          </span>
        </div>
      </button>

      <el-empty
        v-if="searchStore.query && !searchStore.loading && !searchStore.hasResults && !searchStore.error"
        description="没有找到相关内容，试试更宽泛的表达或增加搜索范围"
      />

      <div v-if="searchStore.total > searchStore.pageSize" class="pagination">
        <el-pagination
          layout="prev, pager, next"
          :current-page="searchStore.page"
          :page-size="searchStore.pageSize"
          :total="searchStore.total"
          @current-change="changePage"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { QuestionFilled, Search } from '@element-plus/icons-vue'
import { useSearchStore } from '@/stores/search'
import type { SearchResult, SearchSource } from '@/services/search'

const route = useRoute()
const router = useRouter()
const searchStore = useSearchStore()

const sourceOptions: Array<{ label: string; value: SearchSource }> = [
  { label: '笔记', value: 'note' },
  { label: '学习资源', value: 'resource' },
  { label: '知识点', value: 'graph_node' },
  { label: '课程', value: 'course' },
]

function runSearch(): void {
  const q = searchStore.query.trim()
  if (!q) return
  void router.replace({ query: { ...route.query, q } })
  void searchStore.search(q, 1)
}

function rerunSearch(): void {
  if (searchStore.query.trim()) void searchStore.search(undefined, 1)
}

function changePage(page: number): void {
  void searchStore.search(undefined, page)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function typeMeta(type?: SearchSource): { label: string; tag: 'primary' | 'success' | 'warning' | 'danger' | 'info' } {
  const metadata: Record<SearchSource, { label: string; tag: 'primary' | 'success' | 'warning' | 'danger' | 'info' }> = {
    note: { label: '笔记', tag: 'primary' },
    resource: { label: '学习资源', tag: 'success' },
    graph_node: { label: '知识点', tag: 'warning' },
    course: { label: '课程', tag: 'danger' },
  }
  return metadata[type || 'note']
}

function firstHighlight(item: SearchResult, field: string): string {
  return item.highlight?.[field]?.[0] || ''
}

function resultExcerpt(item: SearchResult): string {
  return firstHighlight(item, 'summary')
    || firstHighlight(item, 'content')
    || firstHighlight(item, 'description')
    || String(item.source.description || item.source.content || '').slice(0, 240)
}

function safeHighlight(value: unknown): string {
  return String(value)
    .split(/(<\/?mark>)/gi)
    .map((part) => /^<\/?mark>$/i.test(part)
      ? part.toLowerCase()
      : part.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'))
    .join('')
}

function visibleTags(item: SearchResult): string[] {
  const tags = Array.isArray(item.source.tags) ? item.source.tags : []
  const subject = item.source.subject ? [String(item.source.subject)] : []
  return [...subject, ...tags.map(String)].slice(0, 4)
}

function displayScore(item: SearchResult): string {
  const score = item.rrf_score ?? item.score ?? 0
  return score < 1 ? `${Math.min(99, Math.round(score * 100 * 20))}%` : `${Math.min(99, Math.round(score))}%`
}

function formatDate(value: string): string {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium' }).format(date)
}

function openResult(item: SearchResult): void {
  const id = item.source.id ?? item.id.split(':').slice(-1)[0]
  const sceneType = String(route.params.sceneType || 'self-study')
  const routes: Partial<Record<SearchSource, { name: string; params: Record<string, string | number> }>> = {
    note: { name: 'SceneNote', params: { sceneType, id } },
    resource: { name: 'ResourceDetail', params: { sceneType, id } },
    graph_node: { name: 'GraphDetail', params: { sceneType, id } },
    course: { name: 'SceneClassroom', params: { sceneType: 'classroom', courseId: id } },
  }
  const target = routes[item.source.doc_type || 'note']
  if (target) void router.push(target)
}

onMounted(() => {
  const q = typeof route.query.q === 'string' ? route.query.q : ''
  if (q) {
    searchStore.query = q
    void searchStore.search(q, 1)
  }
})

watch(() => route.query.q, (value, previous) => {
  if (typeof value === 'string' && value !== previous && value !== searchStore.query) {
    searchStore.query = value
    void searchStore.search(value, 1)
  }
})
</script>

<style lang="scss" scoped>
.search-page { max-width: 980px; margin: 0 auto; padding: 8px 20px 48px; }
.hero { padding: 30px; border-radius: 20px; color: #f8fafc; background: linear-gradient(135deg, #123044, #135b67 58%, #1c7a72); box-shadow: 0 16px 40px rgb(17 52 67 / 16%); }
.eyebrow { margin: 0 0 6px; color: #8de0d1; font-size: 12px; font-weight: 700; letter-spacing: .16em; }
h1 { margin: 0; font-size: clamp(24px, 4vw, 36px); line-height: 1.25; }
.subtitle { margin: 8px 0 22px; color: #d1e6e6; font-size: 14px; }
.search-bar { max-width: 760px; }
.search-bar :deep(.el-input__wrapper) { padding-left: 16px; box-shadow: none; }
.search-bar :deep(.el-input-group__append) { padding: 0; border: 0; background: transparent; }
.search-bar :deep(.el-input-group__append .el-button) { height: 40px; margin: 0; border-radius: 0 8px 8px 0; padding: 0 24px; }
.search-controls { margin: 18px 0; padding: 16px 18px; border: 1px solid var(--color-border-light); border-radius: 14px; background: var(--color-bg-primary); }
.control-row { display: flex; align-items: center; gap: 10px; }
.control-row + .control-row { margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--color-border-light); }
.control-row--wrap { flex-wrap: wrap; }
.control-label { width: 66px; flex: none; color: var(--color-text-secondary); font-size: 13px; font-weight: 600; }
.help-icon { color: var(--color-text-placeholder); }
.result-summary { display: flex; gap: 16px; margin: 4px 2px 10px; color: var(--color-text-secondary); font-size: 13px; }
.result-summary span:first-child { color: var(--color-text-primary); font-weight: 600; }
.result-card { display: block; width: 100%; margin: 0 0 12px; padding: 18px 20px; border: 1px solid var(--color-border-light); border-radius: 14px; color: inherit; text-align: left; background: var(--color-bg-primary); cursor: pointer; transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease; }
.result-card:hover { transform: translateY(-2px); border-color: #72aaa2; box-shadow: 0 10px 24px rgb(27 78 80 / 10%); }
.result-card__top { display: flex; align-items: center; gap: 9px; }
.result-date, .result-score { color: var(--color-text-placeholder); font-size: 12px; }
.result-score { margin-left: auto; }
.result-card h2 { margin: 10px 0 7px; color: var(--color-text-primary); font-size: 18px; line-height: 1.4; }
.excerpt { display: -webkit-box; overflow: hidden; margin: 0; color: var(--color-text-secondary); font-size: 14px; line-height: 1.7; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.summary { margin: 10px 0 0; padding: 9px 12px; border-radius: 8px; color: var(--color-text-secondary); background: color-mix(in srgb, #2a8177 8%, transparent); font-size: 13px; line-height: 1.6; }
.summary span { margin-right: 8px; color: #25766e; font-weight: 700; }
.result-footer { display: flex; align-items: center; gap: 6px; min-height: 24px; margin-top: 12px; }
.matched-by { margin-left: auto; color: var(--color-text-placeholder); font-size: 12px; }
:deep(mark) { border-radius: 2px; color: inherit; background: #ffe39b; padding: 0 2px; }
.pagination { display: flex; justify-content: center; padding-top: 14px; }
@media (max-width: 640px) {
  .search-page { padding-inline: 0; }
  .hero { padding: 22px 16px; border-radius: 14px; }
  .search-controls { border-radius: 10px; }
  .control-label { width: 100%; }
  .result-card { padding: 15px; }
  .result-summary { flex-wrap: wrap; gap: 6px 12px; }
}
</style>
