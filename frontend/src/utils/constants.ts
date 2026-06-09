/**
 * AI4Edu 常量定义
 * 场景枚举、角色枚举等
 */

/**
 * 场景类型枚举
 */
export enum SceneType {
  CLASSROOM = 'classroom',
  SELF_STUDY = 'self_study',
  EXAM = 'exam',
  DISCUSSION = 'discussion',
}

/**
 * 场景配置映射
 */
export const SCENE_CONFIG: Record<SceneType, { name: string; nameEn: string; icon: string; color: string }> = {
  [SceneType.CLASSROOM]: {
    name: '课堂模式',
    nameEn: 'Classroom',
    icon: 'School',
    color: '#1976D2',
  },
  [SceneType.SELF_STUDY]: {
    name: '自习模式',
    nameEn: 'Self Study',
    icon: 'Reading',
    color: '#388E3C',
  },
  [SceneType.EXAM]: {
    name: '考前模式',
    nameEn: 'Exam Prep',
    icon: 'EditPen',
    color: '#F57C00',
  },
  [SceneType.DISCUSSION]: {
    name: '讨论模式',
    nameEn: 'Discussion',
    icon: 'ChatDotRound',
    color: '#7B1FA2',
  },
}

/**
 * 用户角色枚举
 */
export enum UserRole {
  STUDENT = 'student',
  TEACHER = 'teacher',
  ADMIN = 'admin',
  SUPER_ADMIN = 'super_admin',
}

/**
 * 角色配置映射
 */
export const ROLE_CONFIG: Record<UserRole, { name: string; nameEn: string }> = {
  [UserRole.STUDENT]: { name: '学生', nameEn: 'Student' },
  [UserRole.TEACHER]: { name: '教师', nameEn: 'Teacher' },
  [UserRole.ADMIN]: { name: '管理员', nameEn: 'Admin' },
  [UserRole.SUPER_ADMIN]: { name: '超级管理员', nameEn: 'Super Admin' },
}

/**
 * 资源类型枚举
 */
export enum ResourceType {
  PDF = 'pdf',
  DOCX = 'docx',
  PPTX = 'pptx',
  VIDEO = 'video',
  AUDIO = 'audio',
  IMAGE = 'image',
  OTHER = 'other',
}

/**
 * 笔记类型枚举
 */
export enum NoteType {
  PERSONAL = 'personal',
  COURSE = 'course',
  AI_GENERATED = 'ai_generated',
}

/**
 * AI智能体类型枚举
 */
export enum AgentType {
  TUTOR = 'tutor',
  STUDY_BUDDY = 'study_buddy',
  EXAMINER = 'examiner',
  ASSISTANT = 'assistant',
}

/**
 * 通知类型枚举
 */
export enum NotificationType {
  SYSTEM = 'system',
  COURSE = 'course',
  ASSIGNMENT = 'assignment',
  SOCIAL = 'social',
  AI = 'ai',
}

/**
 * 学伴人设枚举
 */
export enum BuddyPersonality {
  ENCOURAGING = 'encouraging',
  STRICT = 'strict',
  HUMOROUS = 'humorous',
  GENTLE = 'gentle',
}

/**
 * 默认分页大小
 */
export const DEFAULT_PAGE_SIZE = 20

/**
 * Token 存储 Key
 */
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  CURRENT_SCENE: 'current_scene',
  USER_PREFERENCES: 'user_preferences',
  LOCALE: 'locale',
  ONBOARDING_COMPLETED: 'onboarding_completed',
} as const
