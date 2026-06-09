/**
 * AI4Edu Agent API Service
 * 封装所有AI智能体相关的API调用
 */
import api from './api'

// ============ 类型定义 ============

export interface AgentSession {
  id: string
  agent_type: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface AgentMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
  metadata?: Record<string, unknown>
}

export interface AgentTypeInfo {
  type: string
  name: string
  description: string
  avatar_url?: string
  capabilities?: string[]
}

export interface CreateSessionParams {
  agent_type: string
  title?: string
}

export interface SendMessageParams {
  content: string
  attachments?: string[]
}

export interface PaginatedSessions {
  items: AgentSession[]
  total: number
  page: number
  page_size: number
}

// ============ API 方法 ============

export const agentApi = {
  /** 获取会话列表 */
  async listSessions(params?: {
    page?: number
    page_size?: number
    agent_type?: string
  }): Promise<PaginatedSessions> {
    const response = await api.get('/agent/sessions', { params })
    return response.data as PaginatedSessions
  },

  /** 创建新会话 */
  async createSession(params: CreateSessionParams): Promise<AgentSession> {
    const response = await api.post('/agent/sessions', params)
    return response.data as AgentSession
  },

  /** 获取会话详情 */
  async getSession(sessionId: string): Promise<AgentSession> {
    const response = await api.get(`/agent/sessions/${sessionId}`)
    return response.data as AgentSession
  },

  /** 发送消息 */
  async sendMessage(sessionId: string, params: SendMessageParams): Promise<AgentMessage> {
    const response = await api.post(`/agent/sessions/${sessionId}/messages`, params)
    return response.data as AgentMessage
  },

  /** 删除会话 */
  async deleteSession(sessionId: string): Promise<void> {
    await api.delete(`/agent/sessions/${sessionId}`)
  },

  /** 获取Agent类型列表 */
  async listAgentTypes(): Promise<AgentTypeInfo[]> {
    const response = await api.get('/agent/types')
    return response.data as AgentTypeInfo[]
  },

  /** 获取WebSocket连接URL */
  getStreamUrl(sessionId: string): string {
    const baseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'
    const token = localStorage.getItem('access_token') || ''
    return `${baseUrl}/ws/agent/chat/${sessionId}?token=${token}`
  },
}
