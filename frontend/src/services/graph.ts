/**
 * AI4Edu 知识图谱 API
 */
import api from './api'

// ============ 类型定义 ============

export interface SquareStat {
  id: string
  name: string
  icon: string
  color: string
  node_count: number
  completeness: number
}

export interface KnowledgeNode {
  id: string
  name: string
  subject?: string
  description?: string
  cognitive_level?: Record<string, number>
  [key: string]: unknown
}

export interface GraphLink {
  source: string
  target: string
  type: string
  label: string
}

export interface NeighborData {
  nodes: KnowledgeNode[]
  links: GraphLink[]
}

export interface CognitiveGoal {
  dimensions: string[]
  values: number[]
  node_name: string
}

// ============ API 方法 ============

export const graphApi = {
  /** 获取图谱广场统计 */
  async getSquareStats(): Promise<SquareStat[]> {
    const response = await api.get('/graphs/square')
    return response.data
  },

  /** 获取节点详情 */
  async getNodeDetail(nodeId: string): Promise<KnowledgeNode> {
    const response = await api.get(`/graphs/nodes/${nodeId}`)
    return response.data
  },

  /** 获取邻居节点 */
  async getNeighbors(nodeId: string, depth = 1, limit = 50): Promise<NeighborData> {
    const response = await api.get(`/graphs/nodes/${nodeId}/neighbors`, {
      params: { depth, limit },
    })
    return response.data
  },

  /** 获取节点关联资源 */
  async getNodeResources(nodeId: string): Promise<unknown[]> {
    const response = await api.get(`/graphs/nodes/${nodeId}/resources`)
    return response.data
  },

  /** 获取推荐节点 */
  async getRecommendations(nodeId: string, limit = 10): Promise<KnowledgeNode[]> {
    const response = await api.get(`/graphs/nodes/${nodeId}/recommendations`, {
      params: { limit },
    })
    return response.data
  },

  /** 获取认知目标 */
  async getCognitiveGoals(nodeId: string): Promise<CognitiveGoal> {
    const response = await api.get(`/graphs/nodes/${nodeId}/cognitive`)
    return response.data
  },

  /** 创建知识节点 */
  async createNode(data: { id: string; name: string; subject: string; description?: string }): Promise<KnowledgeNode> {
    const response = await api.post('/graphs/nodes', null, { params: data })
    return response.data
  },

  /** 更新知识节点 */
  async updateNode(nodeId: string, data: Record<string, unknown>): Promise<KnowledgeNode> {
    const response = await api.put(`/graphs/nodes/${nodeId}`, null, { params: data })
    return response.data
  },

  /** 创建节点关系 */
  async createRelationship(fromId: string, toId: string, relType = 'RELATED', label?: string): Promise<unknown> {
    const response = await api.post(`/graphs/nodes/${fromId}/link/${toId}`, null, {
      params: { rel_type: relType, label },
    })
    return response.data
  },

  /** 删除节点关系 */
  async deleteRelationship(fromId: string, toId: string, relType = 'RELATED'): Promise<void> {
    await api.delete(`/graphs/nodes/${fromId}/link/${toId}`, {
      params: { rel_type: relType },
    })
  },

  /** 搜索知识节点 */
  async searchNodes(q: string, subject?: string, limit = 20): Promise<KnowledgeNode[]> {
    const response = await api.get('/graphs/search', {
      params: { q, subject, limit },
    })
    return response.data
  },
}
