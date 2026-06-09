<template>
  <div ref="containerRef" class="force-graph" :style="{ width, height }">
    <svg ref="svgRef" :width="svgWidth" :height="svgHeight">
      <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill="#999" />
        </marker>
      </defs>
      <g class="links">
        <line
          v-for="link in renderedLinks"
          :key="`${link.source.id || link.source}-${link.target.id || link.target}`"
          :x1="getLinkX(link, 'source', 'x')"
          :y1="getLinkX(link, 'source', 'y')"
          :x2="getLinkX(link, 'target', 'x')"
          :y2="getLinkX(link, 'target', 'y')"
          stroke="#ccc"
          stroke-width="1.5"
          :marker-end="link.type !== 'RELATED' ? 'url(#arrowhead)' : ''"
        />
      </g>
      <g class="nodes">
        <g
          v-for="node in renderedNodes"
          :key="node.id"
          :transform="`translate(${node.x || 0}, ${node.y || 0})`"
          class="node-group"
          @mousedown.prevent="onNodeDragStart($event, node)"
          @mouseenter="onNodeHover(node)"
          @mouseleave="onNodeLeave"
          @click="onNodeClick(node)"
        >
          <circle
            :r="getNodeRadius(node)"
            :fill="getNodeColor(node)"
            stroke="#fff"
            stroke-width="2"
            class="node-circle"
          />
          <text
            :dy="getNodeRadius(node) + 14"
            text-anchor="middle"
            fill="#333"
            font-size="12"
            class="node-label"
          >
            {{ truncate(node.name || node.id, 8) }}
          </text>
        </g>
      </g>
    </svg>
    <!-- Tooltip -->
    <div v-if="hoveredNode" class="force-graph__tooltip" :style="tooltipStyle">
      <strong>{{ hoveredNode.name || hoveredNode.id }}</strong>
      <p v-if="hoveredNode.description">{{ hoveredNode.description }}</p>
      <p v-if="hoveredNode.subject">学科: {{ hoveredNode.subject }}</p>
    </div>
    <!-- 缩放控制 -->
    <div class="force-graph__controls">
      <el-button size="small" circle @click="zoomIn">
        <el-icon><ZoomIn /></el-icon>
      </el-button>
      <el-button size="small" circle @click="zoomOut">
        <el-icon><ZoomOut /></el-icon>
      </el-button>
      <el-button size="small" circle @click="resetView">
        <el-icon><FullScreen /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AI4Edu D3 力导向图组件
 * 支持：拖拽/缩放/hover tooltip/节点点击emit
 */
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { ZoomIn, ZoomOut, FullScreen } from '@element-plus/icons-vue'

interface GraphNode {
  id: string
  name?: string
  subject?: string
  description?: string
  x?: number
  y?: number
  [key: string]: unknown
}

interface GraphLink {
  source: string | GraphNode
  target: string | GraphNode
  type?: string
  label?: string
}

const props = withDefaults(defineProps<{
  nodes: GraphNode[]
  links: GraphLink[]
  width?: string
  height?: string
}>(), {
  width: '100%',
  height: '600px',
})

const emit = defineEmits<{
  (e: 'node-click', node: GraphNode): void
  (e: 'node-hover', node: GraphNode | null): void
}>()

const containerRef = ref<HTMLDivElement | null>(null)
const svgRef = ref<SVGSVGElement | null>(null)

const svgWidth = ref(800)
const svgHeight = ref(600)
const hoveredNode = ref<GraphNode | null>(null)
const tooltipPos = ref({ x: 0, y: 0 })

// 渲染用节点（包含位置信息）
const renderedNodes = ref<GraphNode[]>([])
const renderedLinks = ref<GraphLink[]>([])

// 缩放状态
const currentScale = ref(1)
const currentTranslate = ref({ x: 0, y: 0 })

// 拖拽状态
let dragNode: GraphNode | null = null

const tooltipStyle = computed(() => ({
  left: `${tooltipPos.value.x + 15}px`,
  top: `${tooltipPos.value.y - 10}px`,
}))

// 学科颜色映射
const subjectColors: Record<string, string> = {
  math: '#1976D2',
  physics: '#F57C00',
  chemistry: '#4CAF50',
  biology: '#388E3C',
  cs: '#7B1FA2',
  chinese: '#D32F2F',
  english: '#00796B',
  history: '#5D4037',
  geography: '#0288D1',
  politics: '#C62828',
  pe: '#FF6F00',
  art: '#AD1457',
}

function getNodeRadius(node: GraphNode): number {
  const linkCount = props.links.filter(
    (l) => (l.source === node.id || l.source === node) || (l.target === node.id || l.target === node)
  ).length
  return Math.max(16, Math.min(32, 12 + linkCount * 2))
}

function getNodeColor(node: GraphNode): string {
  return subjectColors[node.subject || ''] || '#5B8FF9'
}

function getLinkX(link: GraphLink, end: 'source' | 'target', axis: 'x' | 'y'): number {
  const val = link[end]
  if (typeof val === 'object' && val !== null) {
    return (val as GraphNode)[axis] || 0
  }
  // 查找节点位置
  const node = renderedNodes.value.find((n) => n.id === val)
  return node?.[axis] || 0
}

function truncate(str: string, len: number): string {
  return str.length > len ? str.slice(0, len) + '...' : str
}

// ==================== 力导向布局（简化版） ====================

let animationFrameId: number | null = null

function initLayout(): void {
  if (props.nodes.length === 0) {
    renderedNodes.value = []
    renderedLinks.value = []
    return
  }

  const cx = svgWidth.value / 2
  const cy = svgHeight.value / 2

  // 初始化节点位置
  const nodes = props.nodes.map((n, i) => {
    const angle = (2 * Math.PI * i) / props.nodes.length
    const r = Math.min(svgWidth.value, svgHeight.value) * 0.3
    return {
      ...n,
      x: n.x ?? cx + r * Math.cos(angle),
      y: n.y ?? cy + r * Math.sin(angle),
      vx: 0,
      vy: 0,
    }
  })

  // 构建链接引用
  const links = props.links.map((l) => ({
    ...l,
    source: typeof l.source === 'object' ? (l.source as GraphNode).id : l.source,
    target: typeof l.target === 'object' ? (l.target as GraphNode).id : l.target,
  }))

  renderedNodes.value = nodes
  renderedLinks.value = links

  // 运行力模拟
  runSimulation(nodes, links)
}

function runSimulation(nodes: GraphNode[], links: GraphLink[]): void {
  const iterations = 120
  const alpha = 0.3
  const cx = svgWidth.value / 2
  const cy = svgHeight.value / 2

  for (let iter = 0; iter < iterations; iter++) {
    const currentAlpha = alpha * (1 - iter / iterations)

    // 斥力
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = (nodes[j].x || 0) - (nodes[i].x || 0)
        const dy = (nodes[j].y || 0) - (nodes[i].y || 0)
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const force = 5000 / (dist * dist)
        const fx = (dx / dist) * force * currentAlpha
        const fy = (dy / dist) * force * currentAlpha

        if (!isDragging(nodes[i])) {
          nodes[i].x = (nodes[i].x || 0) - fx
          nodes[i].y = (nodes[i].y || 0) - fy
        }
        if (!isDragging(nodes[j])) {
          nodes[j].x = (nodes[j].x || 0) + fx
          nodes[j].y = (nodes[j].y || 0) + fy
        }
      }
    }

    // 引力（边）
    for (const link of links) {
      const sourceNode = nodes.find((n) => n.id === link.source)
      const targetNode = nodes.find((n) => n.id === link.target)
      if (!sourceNode || !targetNode) continue

      const dx = (targetNode.x || 0) - (sourceNode.x || 0)
      const dy = (targetNode.y || 0) - (sourceNode.y || 0)
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      const force = (dist - 100) * 0.01 * currentAlpha
      const fx = (dx / dist) * force
      const fy = (dy / dist) * force

      if (!isDragging(sourceNode)) {
        sourceNode.x = (sourceNode.x || 0) + fx
        sourceNode.y = (sourceNode.y || 0) + fy
      }
      if (!isDragging(targetNode)) {
        targetNode.x = (targetNode.x || 0) - fx
        targetNode.y = (targetNode.y || 0) - fy
      }
    }

    // 向心力
    for (const node of nodes) {
      if (isDragging(node)) continue
      node.x = (node.x || 0) + (cx - (node.x || 0)) * 0.01 * currentAlpha
      node.y = (node.y || 0) + (cy - (node.y || 0)) * 0.01 * currentAlpha
    }
  }

  renderedNodes.value = [...nodes]
}

function isDragging(_node: GraphNode): boolean {
  return dragNode?.id === _node.id
}

// ==================== 交互 ====================

function onNodeDragStart(event: MouseEvent, node: GraphNode): void {
  dragNode = node
  const startX = event.clientX
  const startY = event.clientY
  const origX = node.x || 0
  const origY = node.y || 0

  function onMouseMove(e: MouseEvent): void {
    if (!dragNode) return
    const dx = (e.clientX - startX) / currentScale.value
    const dy = (e.clientY - startY) / currentScale.value
    dragNode.x = origX + dx
    dragNode.y = origY + dy
    renderedNodes.value = [...renderedNodes.value]
  }

  function onMouseUp(): void {
    dragNode = null
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

function onNodeHover(node: GraphNode): void {
  hoveredNode.value = node
  emit('node-hover', node)
}

function onNodeLeave(): void {
  hoveredNode.value = null
  emit('node-hover', null)
}

function onNodeClick(node: GraphNode): void {
  emit('node-click', node)
}

function zoomIn(): void {
  currentScale.value = Math.min(currentScale.value * 1.2, 4)
  applyTransform()
}

function zoomOut(): void {
  currentScale.value = Math.max(currentScale.value / 1.2, 0.25)
  applyTransform()
}

function resetView(): void {
  currentScale.value = 1
  currentTranslate.value = { x: 0, y: 0 }
  applyTransform()
}

function applyTransform(): void {
  if (svgRef.value) {
    const g = svgRef.value.querySelector('.links') as SVGGElement
    const gNodes = svgRef.value.querySelector('.nodes') as SVGGElement
    const transform = `translate(${currentTranslate.value.x}, ${currentTranslate.value.y}) scale(${currentScale.value})`
    if (g) g.setAttribute('transform', transform)
    if (gNodes) gNodes.setAttribute('transform', transform)
  }
}

function updateSize(): void {
  if (containerRef.value) {
    svgWidth.value = containerRef.value.clientWidth
    svgHeight.value = containerRef.value.clientHeight
  }
}

// 监听数据变化重新布局
watch(
  () => [props.nodes, props.links],
  () => {
    initLayout()
  },
  { deep: true },
)

onMounted(() => {
  updateSize()
  initLayout()
  window.addEventListener('resize', updateSize)
})

onUnmounted(() => {
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
  window.removeEventListener('resize', updateSize)
})
</script>

<style lang="scss" scoped>
.force-graph {
  position: relative;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--border-radius-md);
  overflow: hidden;

  svg {
    display: block;
  }

  .node-circle {
    cursor: grab;
    transition: r 0.15s ease;

    &:hover {
      stroke-width: 3;
      stroke: var(--color-info);
    }
  }

  .node-label {
    pointer-events: none;
    user-select: none;
  }

  &__tooltip {
    position: absolute;
    padding: 8px 12px;
    background: rgba(0, 0, 0, 0.8);
    color: #fff;
    border-radius: var(--border-radius-sm);
    font-size: 13px;
    max-width: 250px;
    pointer-events: none;
    z-index: 100;

    strong {
      display: block;
      margin-bottom: 4px;
    }

    p {
      margin: 2px 0;
      font-size: 12px;
      color: #ccc;
    }
  }

  &__controls {
    position: absolute;
    bottom: 12px;
    right: 12px;
    display: flex;
    gap: 4px;
  }
}
</style>
