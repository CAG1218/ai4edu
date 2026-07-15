import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { searchApi } from '@/services/search'
import type { SearchMode, SearchResult, SearchSource } from '@/services/search'

const HISTORY_KEY = 'ai4edu_search_history'
const MAX_HISTORY = 10

export const useSearchStore = defineStore('search', () => {
  const query = ref('')
  const results = ref<SearchResult[]>([])
  const suggestions = ref<string[]>([])
  const sources = ref<SearchSource[]>(['note', 'resource', 'graph_node', 'course'])
  const mode = ref<SearchMode>('hybrid')
  const dateRange = ref('')
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const keywordCount = ref(0)
  const semanticCount = ref(0)
  const loading = ref(false)
  const error = ref('')
  const searchHistory = ref<string[]>(JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'))

  const hasResults = computed(() => results.value.length > 0)

  async function search(q?: string, requestedPage = 1): Promise<void> {
    const searchQuery = (q ?? query.value).trim()
    if (!searchQuery || !sources.value.length) return
    loading.value = true
    error.value = ''
    query.value = searchQuery
    page.value = requestedPage
    try {
      const response = await searchApi.search(searchQuery, {
        mode: mode.value,
        sources: sources.value,
        dateRange: dateRange.value,
        page: page.value,
        pageSize: pageSize.value,
      })
      results.value = response.results
      total.value = response.total
      keywordCount.value = response.keyword_count
      semanticCount.value = response.semantic_count
      addToHistory(searchQuery)
    } catch (cause) {
      results.value = []
      total.value = 0
      error.value = cause instanceof Error ? cause.message : '搜索失败，请稍后重试'
    } finally {
      loading.value = false
    }
  }

  async function getSuggestions(prefix: string): Promise<void> {
    if (!prefix.trim()) {
      suggestions.value = []
      return
    }
    try {
      suggestions.value = await searchApi.suggest(prefix)
    } catch {
      suggestions.value = []
    }
  }

  function addToHistory(value: string): void {
    searchHistory.value = [value, ...searchHistory.value.filter((item) => item !== value)].slice(0, MAX_HISTORY)
    localStorage.setItem(HISTORY_KEY, JSON.stringify(searchHistory.value))
  }

  function clearHistory(): void {
    searchHistory.value = []
    localStorage.removeItem(HISTORY_KEY)
  }

  return {
    query, results, suggestions, sources, mode, dateRange, total, page, pageSize,
    keywordCount, semanticCount, loading, error, searchHistory, hasResults,
    search, getSuggestions, addToHistory, clearHistory,
  }
})
