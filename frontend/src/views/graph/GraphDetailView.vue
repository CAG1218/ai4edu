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
          <el-descriptions-item label="学科ID">{{ id }}</el-descriptions-item>
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
            <el-tag v-if="rec.subject" size="small" type="info">{{ rec.subject }}</el-tag>
          </el-card>
        </div>
        <el-empty v-else description="请先选择一个知识点获取推荐" />
      </el-tab-pane>

      <!-- Tab6: 任务 -->
      <el-tab-pane label="任务" name="tasks">
        <el-table :data="tasks" empty-text="暂无任务" stripe>
          <el-table-column prop="name" label="任务名称" />
          <el-table-column prop="type" label="类型" width="120">
            <template #default="{ row }">
              <el-tag :type="row.type === 'learning' ? 'success' : 'warning'" size="small">
                {{ row.type === 'learning' ? '学习' : '复习' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'done' ? 'success' : row.status === 'doing' ? 'primary' : 'info'" size="small">
                {{ row.status === 'done' ? '完成' : row.status === 'doing' ? '进行中' : '待开始' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
/**
 * AI4Edu 知识图谱详情视图
 * 六维Tab：概览/关联资源/关联关系/认知目标/推荐/任务
 */
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useGraphStore } from '@/stores/graph'
import { graphApi } from '@/services/graph'
import ForceGraph from '@/components/graph/ForceGraph.vue'
import NodeCard from '@/components/graph/NodeCard.vue'
import LinkInfo from '@/components/graph/LinkInfo.vue'
import type { KnowledgeNode, GraphLink } from '@/services/graph'

const route = useRoute()
const router = useRouter()
const graphStore = useGraphStore()

const id = computed(() => route.params.id as string)
const activeTab = ref('overview')
const nodeQuery = ref('')
const selectedNodeId = ref<string | null>(null)
const nodeResources = ref<unknown[]>([])
const recommendations = ref<KnowledgeNode[]>([])
const selectedLink = ref<GraphLink | null>(null)
const radarRef = ref<HTMLDivElement | null>(null)

// 任务模拟数据
const tasks = ref([
  { name: '学习基础概念', type: 'learning', status: 'done' },
  { name: '完成练习题', type: 'learning', status: 'doing' },
  { name: '复习核心知识点', type: 'review', status: 'todo' },
])

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

async function renderCognitiveRadar(nodeId: string): Promise<void> {
  try {
    await graphStore.loadCognitiveGoal(nodeId)
    const data = graphStore.cognitiveGoal
    if (!data || !radarRef.value) return

    // 动态导入 ECharts
    const echarts = (await import('echarts')).default
    const chart = echarts.init(radarRef.value)

    chart.setOption({
      title: { text: data.node_name + ' 认知目标', left: 'center' },
      tooltip: {},
      radar: {
        indicator: data.dimensions.map((d) => ({ name: d, max: 100 })),
        shape: 'circle',
        splitNumber: 5,
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: data.values,
              name: data.node_name,
              areaStyle: { opacity: 0.3 },
            },
          ],
        },
      ],
    })

    // 响应式
    const resizeObserver = new ResizeObserver(() => chart.resize())
    resizeObserver.observe(radarRef.value)
  } catch (error) {
    console.error('渲染认知目标雷达图失败:', error)
  }
}

// 监听 Tab 切换，选择默认节点加载关系图
watch(activeTab, async (tab) => {
  if (tab === 'relations' && !selectedNodeId.value) {
    // 加载学科下的节点
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
}
</style>
