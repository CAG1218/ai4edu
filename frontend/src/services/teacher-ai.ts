import api from './api'

export interface TeacherAICourse {
  id: number
  name: string
  subject: string
  grade: string
  semester: string
}

export interface TeacherAIContextSummary {
  course_count: number
  lesson_plan_count: number
  resource_count: number
  student_count: number
  diagnosis_count: number
  classroom_count: number
  classroom_record_count: number
}

export interface TeacherAIContext {
  courses: TeacherAICourse[]
  summary: TeacherAIContextSummary
  sources: string[]
}

export interface TeacherAIHistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface TeacherAIReply {
  answer: string
  model: string
  course_id: number | null
  context_summary: TeacherAIContextSummary
  sources: string[]
}

export const teacherAIApi = {
  async getContext(courseId?: number): Promise<TeacherAIContext> {
    const response = await api.get('/teachers/ai-chat/context', {
      params: courseId ? { course_id: courseId } : undefined,
    })
    return response.data as TeacherAIContext
  },

  async sendMessage(
    message: string,
    history: TeacherAIHistoryMessage[],
    courseId?: number,
  ): Promise<TeacherAIReply> {
    const response = await api.post('/teachers/ai-chat/messages', {
      message,
      history,
      course_id: courseId ?? null,
    }, { timeout: 90000 })
    return response.data as TeacherAIReply
  },
}
