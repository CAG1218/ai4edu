/**
 * AI4Edu 知识图谱 Store
 * 管理图谱广场统计、节点详情、邻居数据
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { graphApi } from '@/services/graph'
import type { SquareStat, KnowledgeNode, NeighborData, CognitiveGoal } from '@/services/graph'

export const useGraphStore = defineStore('graph', () => {
  // ============ State ============

  /** 图谱广场统计 */
  const squareStats = ref<SquareStat[]>([])
  /** 当前节点详情 */
  const currentGraph = ref<KnowledgeNode | null>(null)
  /** 邻居节点数据 */
  const neighborNodes = ref<NeighborData>({ nodes: [], links: [] })
  /** 认知目标数据 */
  const cognitiveGoal = ref<CognitiveGoal | null>(null)
  /** 搜索结果 */
  const searchResults = ref<KnowledgeNode[]>([])
  /** 加载状态 */
  const loading = ref<boolean>(false)

  // ============ Actions ============

  /** 加载图谱广场统计 */
  async function loadSquareStats(): Promise<void> {
    loading.value = true
    try {
      squareStats.value = await graphApi.getSquareStats()
    } catch (error) {
      console.error('加载图谱广场失败:', error)
    } finally {
      loading.value = false
    }
  }

  /** 加载节点详情 */
  async function loadNodeDetail(nodeId: string): Promise<void> {
    loading.value = true
    try {
      currentGraph.value = await graphApi.getNodeDetail(nodeId)
    } catch (error) {
      console.error('加载节点详情失败:', error)
    } finally {
      loading.value = false
    }
  }

  /** 加载邻居节点 */
  async function loadNeighbors(nodeId: string, depth = 1, limit = 50): Promise<void> {
    loading.value = true
    try {
      neighborNodes.value = await graphApi.getNeighbors(nodeId, depth, limit)
    } catch (error) {
      console.error('加载邻居节点失败:', error)
    } finally {
      loading.value = false
    }
  }

  /** 搜索知识节点 */
  async function searchNodes(q: string, subject?: string): Promise<void> {
    loading.value = true
    try {
      searchResults.value = await graphApi.searchNodes(q, subject)
    } catch (error) {
      console.error('搜索节点失败:', error)
    } finally {
      loading.value = false
    }
  }

  /** 加载认知目标 */
  async function loadCognitiveGoal(nodeId: string): Promise<void> {
    try {
      cognitiveGoal.value = await graphApi.getCognitiveGoals(nodeId)
    } catch (error) {
      console.error('加载认知目标失败:', error)
    }
  }

  return {
    squareStats,
    currentGraph,
    neighborNodes,
    cognitiveGoal,
    searchResults,
    loading,
    loadSquareStats,
    loadNodeDetail,
    loadNeighbors,
    searchNodes,
    loadCognitiveGoal,
  }
})
