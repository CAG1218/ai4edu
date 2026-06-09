/**
 * AI4Edu 搜索 Store
 * 管理搜索查询、结果、建议、历史
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { searchApi } from '@/services/search'
import type { SearchResult, HybridSearchResponse } from '@/services/search'

const HISTORY_KEY = 'ai4edu_search_history'
const MAX_HISTORY = 10

export const useSearchStore = defineStore('search', () => {
  // ============ State ============

  const query = ref<string>('')
  const results = ref<SearchResult[]>([])
  const suggestions = ref<string[]>([])
  const searchType = ref<string>('all')
  const total = ref<number>(0)
  const loading = ref<boolean>(false)
  const searchHistory = ref<string[]>(
    JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
  )

  // ============ Getters ============

  const hasResults = computed(() => results.value.length > 0)

  // ============ Actions ============

  /** 执行搜索 */
  async function search(q?: string): Promise<void> {
    const searchQuery = q || query.value
    if (!searchQuery.trim()) return

    loading.value = true
    query.value = searchQuery

    try {
      const response: HybridSearchResponse = await searchApi.search(
        searchQuery,
        searchType.value,
      )
      results.value = response.results
      total.value = response.total
      addToHistory(searchQuery)
    } catch (error) {
      console.error('搜索失败:', error)
    } finally {
      loading.value = false
    }
  }

  /** 获取搜索建议 */
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

  /** 添加到搜索历史 */
  function addToHistory(q: string): void {
    const history = searchHistory.value.filter((h) => h !== q)
    history.unshift(q)
    searchHistory.value = history.slice(0, MAX_HISTORY)
    localStorage.setItem(HISTORY_KEY, JSON.stringify(searchHistory.value))
  }

  /** 清除搜索历史 */
  function clearHistory(): void {
    searchHistory.value = []
    localStorage.removeItem(HISTORY_KEY)
  }

  /** 设置搜索类型 */
  function setSearchType(type: string): void {
    searchType.value = type
  }

  return {
    query,
    results,
    suggestions,
    searchType,
    total,
    loading,
    searchHistory,
    hasResults,
    search,
    getSuggestions,
    addToHistory,
    clearHistory,
    setSearchType,
  }
})
