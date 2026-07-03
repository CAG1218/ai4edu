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

// ============ v2 新增类型 ============

/** 模型负载均衡状态 */
export interface ModelBalancerProvider {
  provider: string
  model_name: string
  is_available: boolean
  is_configured: boolean
  avg_latency_ms: number
  success_rate: number
  failure_count: number
  last_check_time: number
}

/** 模型负载均衡响应 */
export interface ModelBalancerStatus {
  providers: ModelBalancerProvider[]
  current_strategy: string
  recommended_model: string | null
}

/** 课堂记录 */
export interface ClassroomRecord {
  id: number
  classroom_id: number
  course_id: number
  record_type: string
  status: string
  transcript?: string
  segments?: Array<{ text: string; start: number; end: number }>
  knowledge_points?: string[]
  provider?: string
  error_msg?: string
  file_url?: string
  created_at?: string
  updated_at?: string
}

/** 导出记录 */
export interface ExportRecord {
  id: number
  session_id: number
  export_format: string
  status: string
  file_size: number
  error_msg?: string
  created_at?: string
  completed_at?: string
  expired_at?: string
}

/** 导出下载链接 */
export interface ExportDownload {
  download_url: string
  expired_at: string
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

  // ============ v2 新增: 模型负载均衡 ============

  /** 获取模型负载均衡状态 */
  async getModelBalancerStatus(): Promise<ModelBalancerStatus> {
    const response = await api.get('/agents/models/balancer')
    return response.data as ModelBalancerStatus
  },

  // ============ v2 新增: 课堂记录 ============

  /** 获取课堂记录列表 */
  async listClassroomRecords(params?: {
    classroom_id?: number
    course_id?: number
    record_type?: string
    status_filter?: string
    page?: number
    page_size?: number
  }): Promise<{ items: ClassroomRecord[]; total: number; page: number; page_size: number }> {
    const response = await api.get('/agents/classroom-records', { params })
    return response.data as { items: ClassroomRecord[]; total: number; page: number; page_size: number }
  },

  /** 获取课堂记录详情 */
  async getClassroomRecord(recordId: number): Promise<ClassroomRecord> {
    const response = await api.get(`/agents/classroom-records/${recordId}`)
    return response.data as ClassroomRecord
  },

  /** 重新处理课堂记录 */
  async reprocessClassroomRecord(recordId: number): Promise<void> {
    await api.post(`/agents/classroom-records/${recordId}/reprocess`)
  },

  /** 删除课堂记录 */
  async deleteClassroomRecord(recordId: number): Promise<void> {
    await api.delete(`/agents/classroom-records/${recordId}`)
  },

  // ============ v2 新增: 对话导出 ============

  /** 创建导出任务 */
  async createExport(sessionId: number, exportFormat: string): Promise<ExportRecord> {
    const response = await api.post(`/agents/sessions/${sessionId}/exports`, {
      export_format: exportFormat,
    })
    return response.data as ExportRecord
  },

  /** 获取会话的导出列表 */
  async listExports(
    sessionId: number,
    page: number = 1,
    pageSize: number = 20,
  ): Promise<{ items: ExportRecord[]; total: number; page: number; page_size: number }> {
    const response = await api.get(`/agents/sessions/${sessionId}/exports`, {
      params: { page, page_size: pageSize },
    })
    return response.data as { items: ExportRecord[]; total: number; page: number; page_size: number }
  },

  /** 获取导出详情 */
  async getExport(exportId: number): Promise<ExportRecord> {
    const response = await api.get(`/agents/exports/${exportId}`)
    return response.data as ExportRecord
  },

  /** 获取导出下载链接 */
  async downloadExport(exportId: number): Promise<ExportDownload> {
    const response = await api.get(`/agents/exports/${exportId}/download`)
    return response.data as ExportDownload
  },
}
