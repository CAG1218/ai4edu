/**
 * AI4Edu 教师路由
 * /teacher/* 路径下的教师工作台页面
 */
import type { RouteRecordRaw } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'

export const teacherRoutes: RouteRecordRaw[] = [
  {
    path: '/teacher',
    component: AppLayout,
    meta: {
      requiresAuth: true,
      roles: ['teacher', 'admin'],
    },
    children: [
      {
        path: '',
        name: 'TeacherDashboard',
        component: () => import('@/views/teacher/TeacherDashboard.vue'),
        meta: {
          title: '教师工作台',
          requiresAuth: true,
        },
      },
      {
        path: 'lesson-plans',
        name: 'TeacherLessonPlans',
        component: () => import('@/views/teacher/LessonPlanView.vue'),
        meta: {
          title: '教案管理',
          requiresAuth: true,
        },
      },
      {
        path: 'lesson-plans/:id',
        name: 'TeacherLessonPlanDetail',
        component: () => import('@/views/teacher/LessonPlanView.vue'),
        meta: {
          title: '教案详情',
          requiresAuth: true,
        },
      },
      {
        path: 'students',
        name: 'TeacherStudents',
        component: () => import('@/views/scene/DashboardView.vue'),
        meta: {
          title: '学生管理',
          requiresAuth: true,
        },
      },
      {
        path: 'diagnosis',
        name: 'ClassDiagnosis',
        component: () => import('@/views/teacher/ClassDiagnosisView.vue'),
        meta: {
          title: '班级诊断',
          requiresAuth: true,
        },
      },
      {
        path: 'analytics',
        name: 'TeacherAnalytics',
        component: () => import('@/views/scene/DashboardView.vue'),
        meta: {
          title: '学情分析',
          requiresAuth: true,
        },
      },
      {
        path: 'resources',
        name: 'TeacherResources',
        component: () => import('@/views/scene/DashboardView.vue'),
        meta: {
          title: '资源管理',
          requiresAuth: true,
        },
      },
    ],
  },
]
