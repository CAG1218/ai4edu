/**
 * 学生选课相关 API。
 */
import api from './api'

export interface EnrolledCourse {
  id: number
  name: string
  subject: string
  graph_subject_id: string
  location: string | null
  class_time: string | null
  teacher_name: string
  class_weeks: string | null
  semester: string
  progress: number
}

export const courseApi = {
  async listMyCourses(): Promise<EnrolledCourse[]> {
    const response = await api.get('/users/me/courses')
    return (response as any).data ?? response
  },
}
