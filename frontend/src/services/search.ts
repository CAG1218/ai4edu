/**
 * AI4Edu 搜索 API
 */
import api from './api'

// ============ 类型定义 ============

export interface SearchResult {
  id: string
  score: number
  rrf_score?: number
  source: Record<string, unknown>
  highlight: Record<string, string[]>
  type: string
}

export interface HybridSearchResponse {
  query: string
  total: number
  bm25_count: number
  vector_count: number
  results: SearchResult[]
}

// ============ API 方法 ============

export const searchApi = {
  /** 混合检索 */
  async search(q: string, searchType = 'all', limit = 20): Promise<HybridSearchResponse> {
    const response = await api.get('/search/', {
      params: { q, search_type: searchType, limit },
    })
    return response.data
  },

  /** 搜索建议 */
  async suggest(q: string, limit = 10): Promise<string[]> {
    const response = await api.get('/search/suggest', {
      params: { q, limit },
    })
    return response.data
  },

  /** 热门搜索 */
  async getHotSearches(limit = 10): Promise<string[]> {
    const response = await api.get('/search/hot', {
      params: { limit },
    })
    return response.data
  },

  /** 手动索引 */
  async indexDocument(data: {
    doc_id: string
    doc_type?: string
    title?: string
    content?: string
    description?: string
  }): Promise<void> {
    await api.post('/search/index', null, { params: data })
  },
}
