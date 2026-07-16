<template>
  <div class="my-discussion-feed card">
    <h3 class="my-discussion-feed__title">
      <el-icon><ChatLineSquare /></el-icon>
      我的讨论
    </h3>

    <!-- 我的提问 -->
    <div class="my-discussion-feed__section">
      <div class="my-discussion-feed__section-header">
        <span class="my-discussion-feed__section-title">💬 我的提问 ({{ myQuestions.length }})</span>
      </div>
      <div class="my-discussion-feed__items">
        <div
          v-for="item in myQuestions"
          :key="item.id"
          class="my-discussion-feed__item"
        >
          <span class="my-discussion-feed__item-title">{{ item.title }}</span>
          <div class="my-discussion-feed__item-meta">
            <span v-if="item.newReplies > 0" class="my-discussion-feed__new-replies">
              <span class="my-discussion-feed__bell">🔔</span>
              {{ item.newReplies }} 条新回复
            </span>
            <el-tag v-if="item.resolved" type="success" size="small" effect="plain">已解决 ✅</el-tag>
            <el-tag v-else type="warning" size="small" effect="plain">待解决</el-tag>
          </div>
        </div>
        <p v-if="myQuestions.length === 0" class="my-discussion-feed__empty">暂无提问</p>
      </div>
    </div>

    <!-- 我参与的 -->
    <div class="my-discussion-feed__section">
      <div class="my-discussion-feed__section-header">
        <span class="my-discussion-feed__section-title">📢 我参与的 ({{ participated.length }})</span>
      </div>
      <div class="my-discussion-feed__items">
        <div
          v-for="item in participated"
          :key="item.id"
          class="my-discussion-feed__item"
        >
          <span class="my-discussion-feed__item-title">{{ item.title }}</span>
          <div class="my-discussion-feed__item-meta">
            <span v-if="item.newReplies > 0" class="my-discussion-feed__new-replies">
              <span class="my-discussion-feed__bell">🔔</span>
              {{ item.newReplies }} 条新回复
            </span>
            <el-tag v-if="item.resolved" type="success" size="small" effect="plain">已解决 ✅</el-tag>
            <el-tag v-else type="info" size="small" effect="plain">讨论中</el-tag>
          </div>
        </div>
        <p v-if="participated.length === 0" class="my-discussion-feed__empty">暂无参与的讨论</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 我的讨论动态
 * 分区显示"我的提问"和"我参与的"，新回复有未读标记（🔔弹跳动画）
 */
import { computed } from 'vue'
import { DiscussionType } from '../../types'
import type { MyDiscussionItem } from '../../types'

interface Props {
  /** 我的讨论列表 */
  myDiscussions: MyDiscussionItem[]
}

const props = defineProps<Props>()

/** 我的提问 */
const myQuestions = computed(() =>
  props.myDiscussions.filter(d => d.type === DiscussionType.MY_QUESTION)
)

/** 我参与的 */
const participated = computed(() =>
  props.myDiscussions.filter(d => d.type === DiscussionType.PARTICIPATED)
)
</script>

<style lang="scss" scoped>
.my-discussion-feed {
  min-height: 340px;

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-primary, #303133);
    margin: 0 0 16px 0;
  }

  &__section {
    margin-bottom: 16px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  &__section-header {
    margin-bottom: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid #f0f0f0;
  }

  &__section-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--color-text-secondary, #606266);
  }

  &__items {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  &__item {
    padding: 8px 10px;
    border-radius: 6px;
    background: #fafafa;
    transition: background 0.2s ease;

    &:hover {
      background: #f5f0fa;
    }
  }

  &__item-title {
    font-size: 13px;
    font-weight: 500;
    color: var(--color-text-primary, #303133);
    display: block;
    margin-bottom: 4px;
    line-height: 1.4;
  }

  &__item-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  &__new-replies {
    display: flex;
    align-items: center;
    gap: 2px;
    font-size: 12px;
    color: #E6A23C;
    font-weight: 500;
  }

  &__bell {
    display: inline-block;
    animation: discussion-bounce 1.5s ease-in-out infinite;
  }

  &__empty {
    font-size: 13px;
    color: var(--color-text-secondary, #c0c4cc);
    text-align: center;
    padding: 12px 0;
    margin: 0;
  }
}
</style>
