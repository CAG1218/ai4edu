<template>
  <div class="quick-start-discussion card discussion-quick-start--gradient">
    <div class="quick-start-discussion__prompt">
      <el-icon :size="24" color="#7B1FA2"><ChatDotRound /></el-icon>
      <span class="quick-start-discussion__prompt-text">有什么想讨论的？</span>
    </div>
    <div class="quick-start-discussion__actions">
      <el-button type="primary" round @click="emit('start', 'topic')">
        <el-icon><Edit /></el-icon>
        发起话题
      </el-button>
      <el-button type="success" round @click="emit('start', 'question')">
        <el-icon><QuestionFilled /></el-icon>
        提问
      </el-button>
      <el-button type="warning" round @click="emit('start', 'poll')">
        <el-icon><CheckBox /></el-icon>
        创建投票
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 快速发起讨论
 * 顶部输入区，提供"发起话题/提问/创建投票"三个入口按钮
 * P0 所有按钮跳转 /agent（AI 智能体中心）
 */
interface Emits {
  /** 点击发起讨论按钮，P0 统一跳转 /agent */
  (e: 'start', actionType: 'topic' | 'question' | 'poll'): void
}

const emit = defineEmits<Emits>()
</script>

<style lang="scss" scoped>
.discussion-quick-start--gradient {
  background: var(--scene-banner-gradient, linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%));
}

.quick-start-discussion {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;

  &__prompt {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  &__prompt-text {
    font-size: 18px;
    font-weight: 600;
    color: var(--color-text-primary, #303133);
  }

  &__actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
}
</style>
