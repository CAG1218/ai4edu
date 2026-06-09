<template>
  <div class="agent-chat">
    <!-- 左侧会话列表 -->
    <div class="agent-chat__sidebar">
      <div class="agent-chat__sidebar-header">
        <h3>AI 助手</h3>
        <el-button type="primary" size="small" @click="handleNewSession">
          <el-icon><Plus /></el-icon> 新会话
        </el-button>
      </div>

      <!-- Agent类型选择 -->
      <div class="agent-chat__type-selector">
        <el-select v-model="selectedAgentType" placeholder="选择助手类型" size="small" @change="handleTypeChange">
          <el-option
            v-for="at in agentStore.agentTypes"
            :key="at.type"
            :label="at.name"
            :value="at.type"
          />
        </el-select>
      </div>

      <!-- 会话列表 -->
      <div class="agent-chat__session-list">
        <div
          v-for="session in agentStore.sessions"
          :key="session.id"
          :class="['agent-chat__session-item', { 'agent-chat__session-item--active': session.id === agentStore.currentSession?.id }]"
          @click="handleSelectSession(session.id)"
        >
          <div class="agent-chat__session-info">
            <span class="agent-chat__session-title">{{ session.title }}</span>
            <span class="agent-chat__session-meta">{{ formatTime(session.updated_at) }}</span>
          </div>
          <el-button
            type="danger"
            link
            size="small"
            @click.stop="handleDeleteSession(session.id)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <el-empty v-if="agentStore.sessions.length === 0" description="暂无会话" :image-size="60" />
      </div>
    </div>

    <!-- 右侧对话区域 -->
    <div class="agent-chat__main">
      <!-- 顶部Agent信息 -->
      <div v-if="agentStore.currentAgentType" class="agent-chat__header">
        <el-avatar :size="36" :style="{ backgroundColor: '#1976D2' }">
          <el-icon :size="20"><ChatDotRound /></el-icon>
        </el-avatar>
        <div class="agent-chat__header-info">
          <span class="agent-chat__header-name">{{ agentStore.currentAgentType.name }}</span>
          <span class="agent-chat__header-desc">{{ agentStore.currentAgentType.description }}</span>
        </div>
      </div>

      <!-- 消息列表 -->
      <div ref="messageContainerRef" class="agent-chat__messages">
        <div
          v-for="msg in agentStore.sortedMessages"
          :key="msg.id"
          :class="['agent-chat__message', `agent-chat__message--${msg.role}`]"
        >
          <el-avatar v-if="msg.role === 'assistant'" :size="32" :style="{ backgroundColor: '#1976D2' }">
            <el-icon :size="16"><ChatDotRound /></el-icon>
          </el-avatar>
          <div class="agent-chat__message-content">
            <div class="agent-chat__message-bubble" v-html="renderMarkdown(msg.content)"></div>
            <span class="agent-chat__message-time">{{ formatTime(msg.created_at) }}</span>
          </div>
        </div>

        <!-- 流式消息显示 -->
        <div v-if="agentStore.isStreaming && agentStore.streamingContent" class="agent-chat__message agent-chat__message--assistant">
          <el-avatar :size="32" :style="{ backgroundColor: '#1976D2' }">
            <el-icon :size="16"><ChatDotRound /></el-icon>
          </el-avatar>
          <div class="agent-chat__message-content">
            <div class="agent-chat__message-bubble agent-chat__message-bubble--streaming">
              <span v-html="renderMarkdown(agentStore.streamingContent)"></span>
              <span class="agent-chat__cursor">|</span>
            </div>
          </div>
        </div>

        <!-- 加载中 -->
        <div v-if="agentStore.isStreaming && !agentStore.streamingContent" class="agent-chat__message agent-chat__message--assistant">
          <el-avatar :size="32" :style="{ backgroundColor: '#1976D2' }">
            <el-icon :size="16"><ChatDotRound /></el-icon>
          </el-avatar>
          <div class="agent-chat__message-content">
            <div class="agent-chat__message-bubble agent-chat__message-bubble--loading">
              <span class="agent-chat__dot"></span>
              <span class="agent-chat__dot"></span>
              <span class="agent-chat__dot"></span>
            </div>
          </div>
        </div>

        <el-empty v-if="!agentStore.hasActiveSession" description="选择或创建一个会话开始对话" :image-size="100" />
      </div>

      <!-- 底部输入区 -->
      <div v-if="agentStore.hasActiveSession" class="agent-chat__input-area">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="2"
          :placeholder="`输入消息，按 Enter 发送，Shift+Enter 换行...`"
          resize="none"
          :disabled="agentStore.isStreaming"
          @keydown.enter.exact.prevent="handleSend"
        />
        <el-button
          type="primary"
          :icon="Promotion"
          :loading="agentStore.isStreaming"
          :disabled="!inputMessage.trim()"
          @click="handleSend"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AI4Edu AI智能体对话页面
 * 左侧会话列表 + 右侧对话区域 + WebSocket流式消息
 */
import { ref, onMounted, nextTick, watch } from 'vue'
import { Promotion, Plus, Delete, ChatDotRound } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useAgentStore } from '@/stores/agent'

const agentStore = useAgentStore()

const inputMessage = ref<string>('')
const selectedAgentType = ref<string>('tutor')
const messageContainerRef = ref<HTMLElement | null>(null)

/** 发送消息 */
async function handleSend(): Promise<void> {
  const content = inputMessage.value.trim()
  if (!content) return

  inputMessage.value = ''
  await agentStore.streamMessage(content)
  await scrollToBottom()
}

/** 选择会话 */
async function handleSelectSession(sessionId: string): Promise<void> {
  await agentStore.selectSession(sessionId)
  await scrollToBottom()
}

/** 创建新会话 */
async function handleNewSession(): Promise<void> {
  await agentStore.createSession(selectedAgentType.value)
  await scrollToBottom()
}

/** 删除会话 */
async function handleDeleteSession(sessionId: string): Promise<void> {
  try {
    await ElMessageBox.confirm('确定删除该会话？', '确认删除', { type: 'warning' })
    await agentStore.deleteSession(sessionId)
  } catch {
    // 用户取消
  }
}

/** 切换Agent类型 */
function handleTypeChange(): void {
  agentStore.fetchSessions(1, 20, selectedAgentType.value)
}

/** 滚动到底部 */
async function scrollToBottom(): Promise<void> {
  await nextTick()
  if (messageContainerRef.value) {
    messageContainerRef.value.scrollTop = messageContainerRef.value.scrollHeight
  }
}

/** 格式化时间 */
function formatTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}小时前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

/** 简易Markdown渲染 */
function renderMarkdown(text: string): string {
  return text
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br/>')
}

// 消息变化时自动滚动
watch(
  () => agentStore.messages.length,
  () => scrollToBottom()
)

onMounted(() => {
  agentStore.fetchAgentTypes()
  agentStore.fetchSessions()
})
</script>

<style lang="scss" scoped>
.agent-chat {
  display: flex;
  height: 100%;
  background: #fff;

  &__sidebar {
    width: 280px;
    border-right: 1px solid #e8e8e8;
    display: flex;
    flex-direction: column;
    background: #fafafa;
  }

  &__sidebar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid #e8e8e8;

    h3 {
      font-size: 16px;
      font-weight: 600;
      margin: 0;
    }
  }

  &__type-selector {
    padding: 12px 16px;
    border-bottom: 1px solid #e8e8e8;
  }

  &__session-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }

  &__session-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s;

    &:hover {
      background: #f0f0f0;
    }

    &--active {
      background: #e3f2fd;
    }
  }

  &__session-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
    overflow: hidden;
  }

  &__session-title {
    font-size: 14px;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__session-meta {
    font-size: 12px;
    color: #999;
  }

  &__main {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  &__header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 20px;
    border-bottom: 1px solid #e8e8e8;
    background: #fff;
  }

  &__header-info {
    display: flex;
    flex-direction: column;
  }

  &__header-name {
    font-size: 15px;
    font-weight: 600;
  }

  &__header-desc {
    font-size: 12px;
    color: #999;
  }

  &__messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  &__message {
    display: flex;
    gap: 10px;
    max-width: 80%;

    &--user {
      align-self: flex-end;
      flex-direction: row-reverse;

      .agent-chat__message-bubble {
        background: #1976d2;
        color: #fff;
      }

      .agent-chat__message-time {
        text-align: right;
      }
    }

    &--assistant {
      align-self: flex-start;
    }
  }

  &__message-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  &__message-bubble {
    padding: 10px 14px;
    border-radius: 12px;
    background: #f5f5f5;
    font-size: 14px;
    line-height: 1.6;
    word-break: break-word;

    &--streaming {
      background: #f5f5f5;
    }

    &--loading {
      display: flex;
      gap: 4px;
      padding: 14px 20px;
    }

    :deep(pre) {
      background: #1e1e1e;
      color: #d4d4d4;
      padding: 12px;
      border-radius: 6px;
      overflow-x: auto;
      margin: 8px 0;
    }

    :deep(code) {
      font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
      font-size: 13px;
    }

    :deep(code:not(pre code)) {
      background: rgba(0, 0, 0, 0.06);
      padding: 2px 6px;
      border-radius: 4px;
    }
  }

  &__message-time {
    font-size: 11px;
    color: #bbb;
  }

  &__cursor {
    animation: blink 1s infinite;
    color: #1976d2;
    font-weight: bold;
  }

  &__dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #999;
    animation: dotPulse 1.4s infinite ease-in-out;

    &:nth-child(2) {
      animation-delay: 0.2s;
    }
    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }

  &__input-area {
    display: flex;
    gap: 10px;
    padding: 16px 20px;
    border-top: 1px solid #e8e8e8;
    background: #fff;
    align-items: flex-end;

    :deep(.el-textarea__inner) {
      border-radius: 8px;
    }
  }
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

@keyframes dotPulse {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.4;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .agent-chat {
    &__sidebar {
      width: 100%;
      position: absolute;
      z-index: 10;
      height: 100%;
    }
    &__message {
      max-width: 95%;
    }
  }
}
</style>
