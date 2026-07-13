<template>
  <div class="graph-detail">
    <div class="graph-detail__header">
      <el-button text @click="goBack">
        <el-icon><ArrowLeft /></el-icon> 返回广场
      </el-button>
      <h2>{{ currentSubject?.name || id }}</h2>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- Tab1: 概览 -->
      <el-tab-pane label="概览" name="overview">
        <el-descriptions :column="2" border v-loading="graphStore.loading">
          <el-descriptions-item label="学科">{{ currentSubject?.name }}</el-descriptions-item>
          <el-descriptions-item label="知识点数量">{{ currentSubject?.node_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="完整度">{{ currentSubject?.completeness || 0 }}%</el-descriptions-item>
          <el-descriptions-item label="易误解知识点">{{ currentSubject?.misconception_count || 0 }} 个</el-descriptions-item>
        </el-descriptions>

        <!-- 搜索节点 -->
        <div class="graph-detail__search-section">
          <h3>搜索知识点</h3>
          <el-input
            v-model="nodeQuery"
            placeholder="输入知识点名称..."
            @keyup.enter="searchNodes"
          >
            <template #append>
              <el-button @click="searchNodes">搜索</el-button>
            </template>
          </el-input>
          <div v-if="graphStore.searchResults.length > 0" class="graph-detail__search-results">
            <NodeCard
              v-for="node in graphStore.searchResults"
              :key="node.id"
              :node="node"
              @click="selectNode(node)"
              @open-misconception="openMisconceptionDialog(node)"
            />
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab2: 关联资源 -->
      <el-tab-pane label="关联资源" name="resources">
        <el-table :data="nodeResources" empty-text="暂无关联资源" stripe>
          <el-table-column prop="title" label="资源名称" />
          <el-table-column prop="resource_type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ row.resource_type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="file_size" label="大小" width="100">
            <template #default="{ row }">
              {{ row.file_size ? formatSize(row.file_size) : '-' }}
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- Tab3: 关联关系 -->
      <el-tab-pane label="关联关系" name="relations">
        <ForceGraph
          :nodes="graphStore.neighborNodes.nodes"
          :links="graphStore.neighborNodes.links"
          height="500px"
          @node-click="selectNode"
          @node-hover="handleNodeHover"
          @link-click="handleLinkClick"
        />
        <div v-if="selectedLink" class="graph-detail__link-info">
          <LinkInfo :link="selectedLink" />
        </div>
      </el-tab-pane>

      <!-- Tab4: 认知目标 -->
      <el-tab-pane label="认知目标" name="cognitive">
        <div v-if="selectedNodeId" class="graph-detail__cognitive">
          <h3>{{ graphStore.currentGraph?.name || selectedNodeId }} 的认知目标</h3>
          <div ref="radarRef" class="graph-detail__radar"></div>
        </div>
        <el-empty v-else description="请先选择一个知识点" />
      </el-tab-pane>

      <!-- Tab5: 推荐 -->
      <el-tab-pane label="推荐" name="recommend">
        <div v-if="recommendations.length > 0" class="graph-detail__recommendations">
          <el-card
            v-for="rec in recommendations"
            :key="rec.id"
            shadow="hover"
            class="graph-detail__rec-card"
            @click="selectNode(rec)"
          >
            <div class="graph-detail__rec-name">{{ rec.name || rec.id }}</div>
            <p v-if="rec.description" class="graph-detail__rec-desc">{{ rec.description }}</p>
            <div class="graph-detail__rec-tags">
              <el-tag v-if="rec.subject" size="small" type="info">{{ subjectNameMap[rec.subject] || rec.subject }}</el-tag>
              <el-tag
                v-if="(rec as any)._recommendation_reason === '跨学科关联节点'"
                size="small"
                type="warning"
                effect="dark"
              >
                跨学科
              </el-tag>
              <el-tag
                v-if="(rec as any)._recommendation_reason"
                size="small"
                type="success"
                effect="plain"
              >
                {{ (rec as any)._recommendation_reason }}
              </el-tag>
            </div>
          </el-card>
        </div>
        <el-empty v-else description="请先选择一个知识点获取推荐" />
      </el-tab-pane>

      <!-- Tab6: 任务 -->
      <el-tab-pane label="任务" name="tasks">
        <div v-if="selectedNodeId">
          <el-table
            v-if="graphStore.nodeTasks.length > 0"
            :data="graphStore.nodeTasks"
            empty-text="暂无关联任务"
            stripe
          >
            <el-table-column prop="name" label="任务名称" />
            <el-table-column prop="type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag :type="taskTypeTagType(row.type)" size="small">
                  {{ taskTypeLabel(row.type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="taskStatusTagType(row.status)" size="small">
                  {{ taskStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="source" label="来源" width="100">
              <template #default="{ row }">
                <el-tag size="small" type="info" effect="plain">{{ taskSourceLabel(row.source) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="due_date" label="截止时间" width="180">
              <template #default="{ row }">
                {{ row.due_date ? formatDate(row.due_date) : '-' }}
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无关联任务" />
        </div>
        <el-empty v-else description="请先选择一个知识点" />
      </el-tab-pane>
    </el-tabs>

    <!-- Misconception 详情弹窗 -->
    <MisconceptionDialog
      v-if="mcDialogVisible"
      :misconceptions="graphStore.misconceptions"
      :editable="isTeacher"
      @add="handleAddMc"
      @update="handleUpdateMc"
      @delete="handleDeleteMc"
      @suggest="handleSuggestMc"
      @close="mcDialogVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * AI4EDU 知识图谱详情视图
 * 六维Tab：概览/关联资源/关联关系/认知目标/推荐/任务
 * 支持 misconception 标注管理、真实任务数据、认知目标均值对比
 */
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useGraphStore } from '@/stores/graph'
import { useAuthStore } from '@/stores/auth'
import { graphApi } from '@/services/graph'
import ForceGraph from '@/components/graph/ForceGraph.vue'
import NodeCard from '@/components/graph/NodeCard.vue'
import LinkInfo from '@/components/graph/LinkInfo.vue'
import MisconceptionDialog from '@/components/graph/MisconceptionDialog.vue'
import type { KnowledgeNode, GraphLink, MisconceptionInput } from '@/services/graph'

const route = useRoute()
const router = useRouter()
const graphStore = useGraphStore()
const authStore = useAuthStore()

const id = computed(() => route.params.id as string)
const activeTab = ref('overview')
const nodeQuery = ref('')
const selectedNodeId = ref<string | null>(null)
const nodeResources = ref<unknown[]>([])
const recommendations = ref<KnowledgeNode[]>([])
const selectedLink = ref<GraphLink | null>(null)
const radarRef = ref<HTMLDivElement | null>(null)
const mcDialogVisible = ref<boolean>(false)

const isTeacher = computed(() => authStore.isTeacher || authStore.isAdmin)

const subjectNameMap: Record<string, string> = {
  math: '数学', physics: '物理学', chemistry: '化学', biology: '生物学',
  cs: '计算机科学', chinese: '语文', english: '英语', history: '历史',
  geography: '地理', politics: '政治', pe: '体育', art: '艺术',
}

const currentSubject = computed(() =>
  graphStore.squareStats.find((s) => s.id === id.value)
)

function goBack(): void {
  router.push({ name: 'GraphSquare' })
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / (1024 * 1024)).toFixed(1) + 'MB'
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  try {
    const d = new Date(dateStr)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch {
    return dateStr
  }
}

function taskTypeLabel(type: string): string {
  const labels: Record<string, string> = { learning: '学习', review: '复习', diagnosis: '诊断' }
  return labels[type] || type
}

function taskTypeTagType(type: string): 'success' | 'warning' | 'danger' {
  const map: Record<string, 'success' | 'warning' | 'danger'> = {
    learning: 'success', review: 'warning', diagnosis: 'danger',
  }
  return map[type] || 'warning'
}

function taskStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: '待开始', in_progress: '进行中', completed: '已完成',
  }
  return labels[status] || status
}

function taskStatusTagType(status: string): 'info' | 'primary' | 'success' {
  const map: Record<string, 'info' | 'primary' | 'success'> = {
    pending: 'info', in_progress: 'primary', completed: 'success',
  }
  return map[status] || 'info'
}

function taskSourceLabel(source: string): string {
  const labels: Record<string, string> = { course: '课程', diagnosis: '诊断' }
  return labels[source] || source
}

async function searchNodes(): Promise<void> {
  if (!nodeQuery.value.trim()) return
  await graphStore.searchNodes(nodeQuery.value, id.value)
}

async function selectNode(node: KnowledgeNode): Promise<void> {
  selectedNodeId.value = node.id
  await graphStore.loadNodeDetail(node.id)
  await graphStore.loadNeighbors(node.id, 1, 50)
  await loadNodeResources(node.id)
  await loadRecommendations(node.id)
  await renderCognitiveRadar(node.id)
  // 加载该节点的任务
  await graphStore.loadNodeTasks(node.id)
  // 加载该节点的误解标注
  await graphStore.loadMisconceptions(node.id)
}

async function loadNodeResources(nodeId: string): Promise<void> {
  try {
    nodeResources.value = await graphApi.getNodeResources(nodeId)
  } catch {
    nodeResources.value = []
  }
}

async function loadRecommendations(nodeId: string): Promise<void> {
  try {
    recommendations.value = await graphApi.getRecommendations(nodeId)
  } catch {
    recommendations.value = []
  }
}

function handleNodeHover(node: KnowledgeNode | null): void {
  if (!node) {
    selectedLink.value = null
  }
}

function handleLinkClick(link: GraphLink): void {
  selectedLink.value = link
}

// ========== Misconception 管理 ==========

function openMisconceptionDialog(node: KnowledgeNode): void {
  selectedNodeId.value = node.id
  graphStore.loadMisconceptions(node.id).then(() => {
    mcDialogVisible.value = true
  })
}

async function handleAddMc(data: MisconceptionInput): Promise<void> {
  if (!selectedNodeId.value) return
  try {
    await graphStore.addMisconception(selectedNodeId.value, data)
  } catch {
    // 错误已在 store 中处理
  }
}

async function handleUpdateMc(mcId: string, data: Partial<MisconceptionInput>): Promise<void> {
  if (!selectedNodeId.value) return
  try {
    await graphStore.updateMisconception(selectedNodeId.value, mcId, data)
  } catch {
    // 错误已在 store 中处理
  }
}

async function handleDeleteMc(mcId: string): Promise<void> {
  if (!selectedNodeId.value) return
  try {
    await graphStore.deleteMisconception(selectedNodeId.value, mcId)
    if (graphStore.misconceptions.length === 0) {
      mcDialogVisible.value = false
    }
  } catch {
    // 错误已在 store 中处理
  }
}

async function handleSuggestMc(): Promise<void> {
  if (!selectedNodeId.value) return
  const suggestions = await graphStore.suggestMisconceptions(selectedNodeId.value)
  if (suggestions.length === 0) {
    // 无建议时提示
    return
  }
  // 逐条确认添加
  for (const sug of suggestions) {
    try {
      await graphStore.addMisconception(selectedNodeId.value, {
        misconception: sug.misconception,
        correction: sug.correction,
        topic: sug.topic,
        keywords: sug.keywords,
      })
    } catch {
      // 跳过失败项
    }
  }
}

// ========== 认知目标雷达图 ==========

async function renderCognitiveRadar(nodeId: string): Promise<void> {
  try {
    // P1: 携带 include_avg=true 获取学科均值
    await graphStore.loadCognitiveGoal(nodeId, true)
    const data = graphStore.cognitiveGoal
    if (!data || !radarRef.value) return

    const echarts = (await import('echarts')).default
    const chart = echarts.init(radarRef.value)

    const seriesData: Array<{ value: number[]; name: string; areaStyle?: { opacity: number } }> = [
      {
        value: data.values,
        name: data.node_name,
        areaStyle: { opacity: 0.3 },
      },
    ]

    // P1: 学科均值对比线
    if (data.subject_avg && data.subject_avg.length > 0) {
      seriesData.push({
        value: data.subject_avg,
        name: '学科均值',
        areaStyle: { opacity: 0.1 },
      })
    }

    chart.setOption({
      title: { text: data.node_name + ' 认知目标', left: 'center' },
      tooltip: {},
      legend: {
        data: seriesData.map((s) => s.name),
        bottom: 10,
      },
      radar: {
        indicator: data.dimensions.map((d) => ({ name: d, max: 100 })),
        shape: 'circle',
        splitNumber: 5,
      },
      series: [
        {
          type: 'radar',
          data: seriesData,
        },
      ],
    })

    const resizeObserver = new ResizeObserver(() => chart.resize())
    resizeObserver.observe(radarRef.value)
  } catch (error) {
    console.error('渲染认知目标雷达图失败:', error)
  }
}

// 监听 Tab 切换
watch(activeTab, async (tab) => {
  if (tab === 'relations' && !selectedNodeId.value) {
    await graphStore.searchNodes('', id.value)
    if (graphStore.searchResults.length > 0) {
      await selectNode(graphStore.searchResults[0])
    }
  }
})

onMounted(() => {
  if (!graphStore.squareStats.length) {
    graphStore.loadSquareStats()
  }
})
</script>

<style lang="scss" scoped>
.graph-detail {
  &__header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: var(--spacing-lg);

    h2 {
      font-size: 20px;
      font-weight: 700;
      color: var(--color-text-primary);
    }
  }

  &__search-section {
    margin-top: var(--spacing-lg);

    h3 {
      margin-bottom: 10px;
      font-size: 16px;
    }
  }

  &__search-results {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 12px;
    margin-top: 12px;
  }

  &__link-info {
    margin-top: 16px;
  }

  &__cognitive {
    h3 {
      margin-bottom: 16px;
    }
  }

  &__radar {
    width: 100%;
    height: 400px;
  }

  &__recommendations {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 12px;
  }

  &__rec-card {
    cursor: pointer;
    transition: transform 0.15s ease;

    &:hover {
      transform: translateY(-2px);
    }
  }

  &__rec-name {
    font-weight: 600;
    margin-bottom: 4px;
  }

  &__rec-desc {
    font-size: 13px;
    color: var(--color-text-secondary);
    margin-bottom: 8px;
  }

  &__rec-tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }
}
</style>
