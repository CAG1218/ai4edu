<template>
  <div class="hot-topics-rank card">
    <div class="hot-topics-rank__header">
      <h3 class="hot-topics-rank__title">
        <span class="hot-topics-rank__fire">🔥</span>
        热门话题
      </h3>
      <el-button type="primary" link size="small">查看全部</el-button>
    </div>

    <div class="hot-topics-rank__list">
      <div
        v-for="(topic, index) in hotTopics"
        :key="topic.id"
        class="hot-topics-rank__item"
      >
        <!-- 热度色条 -->
        <div
          class="hot-topics-rank__heat-bar"
          :class="[`hot-topics-rank__heat-bar--${getHeatLevel(topic.heatScore)}`]"
        ></div>

        <!-- 排名 -->
        <span
          class="hot-topics-rank__rank"
          :class="{ 'hot-topics-rank__rank--top': index < 3 }"
        >{{ index + 1 }}</span>

        <!-- 话题信息 -->
        <div class="hot-topics-rank__info">
          <span class="hot-topics-rank__topic-title">{{ topic.title }}</span>
          <div class="hot-topics-rank__tags">
            <el-tag
              v-for="tag in topic.tags"
              :key="tag"
              size="small"
              effect="plain"
              round
            >{{ tag }}</el-tag>
          </div>
          <div class="hot-topics-rank__meta">
            <span><el-icon><User /></el-icon> {{ topic.participants }}人参与</span>
            <span><el-icon><ChatLineRound /></el-icon> {{ topic.replies }}条回复</span>
            <span class="hot-topics-rank__heat">热度 {{ topic.heatScore }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 热门话题排行
 * 排行榜样式：序号 + 标题 + 参与人数 + 回复数 + 热度
 * 左侧热度色条（红=高热度、橙=中、灰=低）
 */
import type { DiscussionTopic } from '../../types'

interface Props {
  /** 热门话题列表 */
  hotTopics: DiscussionTopic[]
}

defineProps<Props>()

/** 热度等级 */
function getHeatLevel(score: number): 'high' | 'medium' | 'low' {
  if (score >= 70) return 'high'
  if (score >= 40) return 'medium'
  return 'low'
}
</script>

<style lang="scss" scoped>
.hot-topics-rank {
  min-height: 340px;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary, #303133);
    margin: 0;
  }

  &__fire {
    font-size: 18px;
  }

  &__list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  &__item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 12px;
    border-radius: 8px;
    background: #fafafa;
    transition: background 0.2s ease;
    position: relative;
    overflow: hidden;

    &:hover {
      background: #f5f0fa;
    }
  }

  &__heat-bar {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    border-radius: 2px;

    &--high {
      background: linear-gradient(180deg, #F56C6C 0%, #E6A23C 100%);
    }
    &--medium {
      background: linear-gradient(180deg, #E6A23C 0%, #FFB74D 100%);
    }
    &--low {
      background: #dcdfe6;
    }
  }

  &__rank {
    flex-shrink: 0;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
    color: var(--color-text-secondary, #909399);
    background: #f0f0f0;
    margin-left: 4px;

    &--top {
      color: #fff;
      background: linear-gradient(135deg, #F56C6C 0%, #E6A23C 100%);
    }
  }

  &__info {
    flex: 1;
    min-width: 0;
  }

  &__topic-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text-primary, #303133);
    display: block;
    margin-bottom: 4px;
  }

  &__tags {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    margin-bottom: 4px;
  }

  &__meta {
    display: flex;
    gap: 12px;
    font-size: 12px;
    color: var(--color-text-secondary, #909399);

    span {
      display: flex;
      align-items: center;
      gap: 2px;
    }
  }

  &__heat {
    color: #E6A23C;
    font-weight: 600;
  }
}
</style>
