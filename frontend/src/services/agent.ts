/**
 * AI4Edu Agent API Service
 * 封装所有AI智能体相关的API调用
 * 新增: 多模型列表、场景预设、引用来源、上下文摘要
 */
import api from './api'

// ============ 类型定义 ============

export interface AgentSession {
  id: string
  agent_type: string
  title: string
  scene_type?: string
  model_name?: string
  system_prompt?: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface AgentMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  model_name?: string
  created_at: string
  metadata?: Record<string, unknown>
}

export interface AgentTypeInfo {
  agent_type: string
  name: string
  description: string
  icon?: string
  supported_features?: string[]
}

export interface CreateSessionParams {
  agent_type?: string
  title?: string
  scene_type?: string
  course_id?: number
  model_name?: string
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

/** 模型信息 */
export interface ModelInfo {
  provider: string
  model: string
  status: string
  is_default: boolean
  is_configured?: boolean
}

  /** 场景预设 */
export interface ScenePreset {
  scene_type: string
  name: string
  description: string
  icon: string
  preferred_model: string
  default_agent_type: string
}

/** 引用来源 */
export interface Citation {
  type: string
  title: string
  source_url: string
  teacher_name?: string
}

/** 上下文摘要 */
export interface ContextSummary {
  notes_count: number
  resources_count: number
  graph_nodes_count: number
  teacher_methods_count: number
}

/** 会话上下文响应 */
export interface SessionContextResponse {
  notes: Array<{ id: number; title: string; excerpt: string }>
  resources: Array<{ id: number; title: string; resource_type: string }>
  graph_nodes: Array<{ id: string; name: string }>
  teacher_methods: Array<{ id: number; title: string; teacher_name: string }>
  citations: Citation[]
  summary: ContextSummary
}

/** 发送消息完整响应 */
export interface SendMessageResponse {
  user_message: { id: number; role: string; content: string }
  assistant_message: { id: number; role: string; content: string; model_name: string }
  citations: Citation[]
  context_summary: ContextSummary
  model_used: string
  model_fallback: boolean
  detected_intent?: string
  agent_type?: string
}

// ============ API 方法 ============

export const agentApi = {
  /** 获取会话列表 */
  async listSessions(params?: {
    page?: number
    page_size?: number
    agent_type?: string
  }): Promise<PaginatedSessions> {
    const response = await api.get('/agents/sessions', { params })
    return response.data as PaginatedSessions
  },

  /** 创建新会话 */
  async createSession(params: CreateSessionParams): Promise<AgentSession> {
    const response = await api.post('/agents/sessions', params)
    return response.data as AgentSession
  },

  /** 获取会话详情 */
  async getSession(sessionId: string): Promise<AgentSession> {
    const response = await api.get(`/agents/sessions/${sessionId}`)
    return response.data as AgentSession
  },

  /** 发送消息 */
  async sendMessage(sessionId: string, params: SendMessageParams): Promise<SendMessageResponse> {
    const response = await api.post(`/agents/sessions/${sessionId}/messages`, params)
    return response.data as SendMessageResponse
  },

  /** 删除会话 */
  async deleteSession(sessionId: string): Promise<void> {
    await api.delete(`/agents/sessions/${sessionId}`)
  },

  /** 获取Agent类型列表 */
  async listAgentTypes(): Promise<AgentTypeInfo[]> {
    const response = await api.get('/agents/types')
    return response.data as AgentTypeInfo[]
  },

  /** 获取可用模型列表 */
  async listModels(): Promise<ModelInfo[]> {
    const response = await api.get('/agents/models')
    return response.data as ModelInfo[]
  },

  /** 获取场景预设列表 */
  async listScenes(): Promise<ScenePreset[]> {
    const response = await api.get('/agents/scenes')
    return response.data as ScenePreset[]
  },

  /** 获取会话上下文资源 */
  async getSessionContext(sessionId: string): Promise<SessionContextResponse> {
    const response = await api.get(`/agents/sessions/${sessionId}/context`)
    return response.data as SessionContextResponse
  },

  /** 获取WebSocket连接URL */
  getStreamUrl(sessionId: string): string {
    const baseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'
    const token = localStorage.getItem('access_token') || ''
    return `${baseUrl}/api/v1/agents/ws/${sessionId}?token=${token}`
  },
}
