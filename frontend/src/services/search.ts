import api from './api'

export type SearchSource = 'note' | 'resource' | 'graph_node' | 'course'
export type SearchMode = 'hybrid' | 'keyword' | 'semantic'

export interface SearchDocument {
  id?: number | string
  doc_type?: SearchSource
  title?: string
  name?: string
  content?: string
  description?: string
  summary?: string
  tags?: string[]
  subject?: string
  resource_type?: string
  updated_at?: string
  [key: string]: unknown
}

export interface SearchResult {
  id: string
  score: number
  rrf_score?: number
  source: SearchDocument
  highlight: Record<string, string[]>
  type: string
  matched_by?: string[]
}

export interface HybridSearchResponse {
  query: string
  total: number
  page: number
  page_size: number
  keyword_count: number
  semantic_count: number
  sources: SearchSource[]
  mode: SearchMode
  results: SearchResult[]
}

export interface SearchOptions {
  mode?: SearchMode
  sources?: SearchSource[]
  dateRange?: string
  page?: number
  pageSize?: number
}

export const searchApi = {
  async search(q: string, options: SearchOptions = {}): Promise<HybridSearchResponse> {
    const response = await api.get('/search/', {
      params: {
        q,
        mode: options.mode || 'hybrid',
        sources: options.sources,
        date_range: options.dateRange || undefined,
        page: options.page || 1,
        page_size: options.pageSize || 20,
      },
      paramsSerializer: { indexes: null },
    })
    return response.data
  },

  async suggest(q: string, limit = 10): Promise<string[]> {
    const response = await api.get('/search/suggest', { params: { q, limit } })
    return response.data
  },

  async getHotSearches(limit = 10): Promise<string[]> {
    const response = await api.get('/search/hot', { params: { limit } })
    return response.data
  },

  async reindexNote(noteId: number): Promise<{ summary: string; keywords: string[] }> {
    const response = await api.post(`/search/notes/${noteId}/reindex`)
    return response.data
  },
}
