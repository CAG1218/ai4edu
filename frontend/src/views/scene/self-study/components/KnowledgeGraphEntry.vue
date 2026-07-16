<template>
  <div class="knowledge-graph-entry card" @click="emit('enter')">
    <h3 class="knowledge-graph-entry__title">
      <el-icon><Connection /></el-icon>
      知识图谱
    </h3>

    <!-- 迷你拓扑 SVG（静态，P0 不可交互，点击整个卡片跳转） -->
    <div class="knowledge-graph-entry__svg-wrapper">
      <svg viewBox="0 0 300 180" class="knowledge-graph-entry__svg" xmlns="http://www.w3.org/2000/svg">
        <!-- 连接线 -->
        <line x1="100" y1="30" x2="50" y2="85" stroke="#c0c4cc" stroke-width="1.5" />
        <line x1="100" y1="30" x2="150" y2="85" stroke="#c0c4cc" stroke-width="1.5" />
        <line x1="200" y1="30" x2="150" y2="85" stroke="#c0c4cc" stroke-width="1.5" />
        <line x1="200" y1="30" x2="250" y2="85" stroke="#c0c4cc" stroke-width="1.5" />
        <line x1="150" y1="85" x2="100" y2="140" stroke="#c0c4cc" stroke-width="1.5" />
        <line x1="150" y1="85" x2="200" y2="140" stroke="#c0c4cc" stroke-width="1.5" />

        <!-- 节点 -->
        <g v-for="node in svgNodes" :key="node.id" class="graph-node">
          <circle
            :cx="node.cx"
            :cy="node.cy"
            r="16"
            :fill="node.color"
            :class="{ 'graph-node--weak': node.isWeak }"
          />
          <text
            :x="node.cx"
            :y="node.cy + 4"
            text-anchor="middle"
            font-size="9"
            fill="#fff"
            font-weight="600"
          >{{ node.shortLabel }}</text>
          <text
            :x="node.cx"
            :y="node.cy + 28"
            text-anchor="middle"
            font-size="9"
            fill="#606266"
          >{{ node.label }}</text>
        </g>
      </svg>
    </div>

    <!-- 图谱概要信息 -->
    <div class="knowledge-graph-entry__summary">
      <span class="knowledge-graph-entry__stat">
        <el-icon color="#388E3C"><Connection /></el-icon>
        {{ graphMini.totalNodes }} 个知识点
      </span>
      <span class="knowledge-graph-entry__weak">
        <el-icon color="#EF5350"><Warning /></el-icon>
        {{ graphMini.weakNodes }} 个薄弱节点待巩固
      </span>
    </div>

    <el-button type="success" plain class="knowledge-graph-entry__btn" @click.stop="emit('enter')">
      进入图谱
      <el-icon class="knowledge-graph-entry__btn-icon"><ArrowRight /></el-icon>
    </el-button>
  </div>
</template>

<script setup lang="ts">
/**
 * 知识图谱入口
 * 静态 SVG 迷你拓扑图（7 节点），红色标注薄弱节点
 * P0 点击整个卡片跳转 /scene/self_study/graphs
 */
import { computed } from 'vue'
import type { KnowledgeGraphMini } from '../../types'

interface Props {
  /** 知识图谱迷你数据 */
  graphMini: KnowledgeGraphMini
}

interface Emits {
  /** 点击进入图谱 */
  (e: 'enter'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

/** SVG 节点位置映射（与 mock 数据 7 节点对应） */
const svgNodes = computed(() => {
  const positions = [
    { cx: 100, cy: 30 },
    { cx: 200, cy: 30 },
    { cx: 50, cy: 85 },
    { cx: 150, cy: 85 },
    { cx: 250, cy: 85 },
    { cx: 100, cy: 140 },
    { cx: 200, cy: 140 },
  ]
  return props.graphMini.nodes.map((node, index) => ({
    id: node.id,
    cx: positions[index].cx,
    cy: positions[index].cy,
    color: node.color,
    isWeak: node.isWeak,
    label: node.label,
    shortLabel: node.label.length > 2 ? node.label.substring(0, 2) : node.label,
  }))
})
</script>

<style lang="scss" scoped>
.knowledge-graph-entry {
  min-height: 320px;
  cursor: pointer;
  transition: box-shadow 0.3s ease;

  &:hover {
    box-shadow: 0 4px 20px rgba(56, 142, 60, 0.15);
  }

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary, #303133);
    margin: 0 0 12px 0;
  }

  &__svg-wrapper {
    display: flex;
    justify-content: center;
    padding: 8px 0;
  }

  &__svg {
    width: 100%;
    max-width: 280px;
    height: auto;
  }

  &__summary {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin: 8px 0 16px;
    font-size: 13px;

    span {
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }

  &__weak {
    color: #EF5350;
    font-weight: 500;
  }

  &__btn {
    width: 100%;

    &-icon {
      margin-left: 4px;
    }
  }
}

.graph-node {
  &--weak {
    animation: graph-node-pulse 2s infinite;
  }
}
</style>
