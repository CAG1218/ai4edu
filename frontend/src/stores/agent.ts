/**
 * AI4Edu Agent Store
 * 管理AI会话列表、当前会话、消息流、Agent类型、流式消息接收
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import { agentApi, type AgentSession, type AgentMessage, type AgentTypeInfo } from '@/services/agent'
import { ElMessage } from 'element-plus'

export const useAgentStore = defineStore('agent', () => {
  // ============ State ============

  /** 会话列表 */
  const sessions = ref<AgentSession[]>([])
  /** 当前选中会话 */
  const currentSession = ref<AgentSession | null>(null)
  /** 当前会话消息列表 */
  const messages = ref<AgentMessage[]>([])
  /** Agent类型列表 */
  const agentTypes = ref<AgentTypeInfo[]>([])
  /** 是否正在流式接收 */
  const isStreaming = ref<boolean>(false)
  /** 流式消息内容（逐字追加） */
  const streamingContent = ref<string>('')
  /** 加载状态 */
  const loading = ref<boolean>(false)
  /** 消息加载状态 */
  const messagesLoading = ref<boolean>(false)
  /** 会话总数 */
  const totalSessions = ref<number>(0)
  /** 当前页码 */
  const currentPage = ref<number>(1)
  /** WebSocket实例 */
  let wsConnection: WebSocket | null = null

  // ============ Getters ============

  /** 当前Agent类型 */
  const currentAgentType = computed<AgentTypeInfo | null>(() => {
    if (!currentSession.value) return null
    return agentTypes.value.find((t) => t.type === currentSession.value!.agent_type) ?? null
  })

  /** 是否有活跃会话 */
  const hasActiveSession = computed<boolean>(() => currentSession.value !== null)

  /** 排序后的消息列表（按时间升序） */
  const sortedMessages = computed<AgentMessage[]>(() => {
    return [...messages.value].sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    )
  })

  // ============ Actions ============

  /**
   * 获取会话列表
   * @param page 页码
   * @param pageSize 每页数量
   * @param agentType Agent类型筛选
   */
  async function fetchSessions(page: number = 1, pageSize: number = 20, agentType?: string): Promise<void> {
    loading.value = true
    try {
      const response = await agentApi.listSessions({
        page,
        page_size: pageSize,
        agent_type: agentType,
      })
      sessions.value = response.items
      totalSessions.value = response.total
      currentPage.value = page
    } catch (error) {
      console.error('获取会话列表失败:', error)
      ElMessage.error('获取会话列表失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建新会话
   * @param agentType Agent类型
   * @param title 会话标题
   */
  async function createSession(agentType: string, title?: string): Promise<AgentSession | null> {
    try {
      const session = await agentApi.createSession({ agent_type: agentType, title })
      sessions.value.unshift(session)
      currentSession.value = session
      messages.value = []
      return session
    } catch (error) {
      console.error('创建会话失败:', error)
      ElMessage.error('创建会话失败')
      return null
    }
  }

  /**
   * 选择会话
   * @param sessionId 会话ID
   */
  async function selectSession(sessionId: string): Promise<void> {
    const session = sessions.value.find((s) => s.id === sessionId)
    if (!session) {
      try {
        currentSession.value = await agentApi.getSession(sessionId)
      } catch (error) {
        console.error('获取会话详情失败:', error)
        return
      }
    } else {
      currentSession.value = session
    }
    // 加载消息历史
    await fetchMessages(sessionId)
    // 断开旧WebSocket
    disconnectStream()
  }

  /**
   * 获取会话消息列表
   * @param sessionId 会话ID
   */
  async function fetchMessages(sessionId: string): Promise<void> {
    messagesLoading.value = true
    try {
      const response = await api.get(`/agent/sessions/${sessionId}/messages`)
      messages.value = response.data as AgentMessage[]
    } catch (error) {
      console.error('获取消息列表失败:', error)
      messages.value = []
    } finally {
      messagesLoading.value = false
    }
  }

  /**
   * 发送消息（HTTP方式，非流式）
   * @param content 消息内容
   */
  async function sendMessage(content: string): Promise<void> {
    if (!currentSession.value) {
      ElMessage.warning('请先选择或创建会话')
      return
    }

    // 添加用户消息到列表
    const userMessage: AgentMessage = {
      id: `temp_${Date.now()}`,
      session_id: currentSession.value.id,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    messages.value.push(userMessage)

    try {
      const assistantMessage = await agentApi.sendMessage(currentSession.value.id, { content })
      messages.value.push(assistantMessage)
    } catch (error) {
      console.error('发送消息失败:', error)
      ElMessage.error('发送消息失败')
    }
  }

  /**
   * 流式发送消息（WebSocket）
   * @param content 消息内容
   */
  async function streamMessage(content: string): Promise<void> {
    if (!currentSession.value) {
      ElMessage.warning('请先选择或创建会话')
      return
    }

    // 添加用户消息
    const userMessage: AgentMessage = {
      id: `temp_${Date.now()}`,
      session_id: currentSession.value.id,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    messages.value.push(userMessage)

    // 建立WebSocket连接
    isStreaming.value = true
    streamingContent.value = ''

    const wsUrl = agentApi.getStreamUrl(currentSession.value.id)
    wsConnection = new WebSocket(wsUrl)

    wsConnection.onopen = () => {
      // 发送消息
      wsConnection!.send(
        JSON.stringify({
          type: 'chat',
          content,
          session_id: currentSession.value!.id,
        })
      )
    }

    wsConnection.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string)

        if (data.type === 'token') {
          // 流式追加内容
          streamingContent.value += data.content
        } else if (data.type === 'message_end') {
          // 消息结束，将流式内容转为正式消息
          const assistantMessage: AgentMessage = {
            id: data.message_id || `msg_${Date.now()}`,
            session_id: currentSession.value!.id,
            role: 'assistant',
            content: streamingContent.value,
            created_at: new Date().toISOString(),
            metadata: data.metadata,
          }
          messages.value.push(assistantMessage)
          streamingContent.value = ''
          isStreaming.value = false
        } else if (data.type === 'error') {
          ElMessage.error(data.message || 'AI回复出错')
          isStreaming.value = false
          streamingContent.value = ''
        }
      } catch (e) {
        console.error('解析WebSocket消息失败:', e)
      }
    }

    wsConnection.onerror = (error) => {
      console.error('WebSocket连接错误:', error)
      ElMessage.error('连接失败，请稍后重试')
      isStreaming.value = false
      streamingContent.value = ''
    }

    wsConnection.onclose = () => {
      isStreaming.value = false
    }
  }

  /**
   * 断开WebSocket连接
   */
  function disconnectStream(): void {
    if (wsConnection) {
      wsConnection.close()
      wsConnection = null
    }
    isStreaming.value = false
    streamingContent.value = ''
  }

  /**
   * 获取Agent类型列表
   */
  async function fetchAgentTypes(): Promise<void> {
    try {
      agentTypes.value = await agentApi.listAgentTypes()
    } catch (error) {
      console.error('获取Agent类型失败:', error)
    }
  }

  /**
   * 删除会话
   * @param sessionId 会话ID
   */
  async function deleteSession(sessionId: string): Promise<void> {
    try {
      await agentApi.deleteSession(sessionId)
      sessions.value = sessions.value.filter((s) => s.id !== sessionId)
      if (currentSession.value?.id === sessionId) {
        currentSession.value = null
        messages.value = []
        disconnectStream()
      }
      ElMessage.success('会话已删除')
    } catch (error) {
      console.error('删除会话失败:', error)
      ElMessage.error('删除会话失败')
    }
  }

  /**
   * 清除当前会话状态
   */
  function clearCurrentSession(): void {
    disconnectStream()
    currentSession.value = null
    messages.value = []
    streamingContent.value = ''
  }

  return {
    // State
    sessions,
    currentSession,
    messages,
    agentTypes,
    isStreaming,
    streamingContent,
    loading,
    messagesLoading,
    totalSessions,
    currentPage,
    // Getters
    currentAgentType,
    hasActiveSession,
    sortedMessages,
    // Actions
    fetchSessions,
    createSession,
    selectSession,
    fetchMessages,
    sendMessage,
    streamMessage,
    disconnectStream,
    fetchAgentTypes,
    deleteSession,
    clearCurrentSession,
  }
})
