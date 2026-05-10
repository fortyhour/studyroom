import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue')
  },
  {
    path: '/',
    redirect: '/student/home'
  },
  {
    path: '/student',
    component: () => import('../views/student/StudentLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: 'home', name: 'StudentHome', component: () => import('../views/student/Home.vue') },
      { path: 'room/:roomId', name: 'RoomDetail', component: () => import('../views/student/RoomDetail.vue') },
      { path: 'seat/:seatId', name: 'SeatDetail', component: () => import('../views/student/SeatDetail.vue') },
      { path: 'profile', name: 'StudentProfile', component: () => import('../views/student/Profile.vue') },
      { path: 'history', name: 'ReservationHistory', component: () => import('../views/student/ReservationHistory.vue') },
      { path: 'history/:resId', name: 'ReservationDetail', component: () => import('../views/student/ReservationDetail.vue') }
    ]
  },
  {
    path: '/admin',
    component: () => import('../views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/admin/Dashboard.vue') },
      { path: 'rooms', name: 'RoomManage', component: () => import('../views/admin/RoomManage.vue') },
      { path: 'seats', name: 'SeatManage', component: () => import('../views/admin/SeatManage.vue') },
      { path: 'users', name: 'UserManage', component: () => import('../views/admin/UserManage.vue') },
      { path: 'roles', name: 'RoleManage', component: () => import('../views/admin/RoleManage.vue') },
      { path: 'reservations', name: 'AdminReservations', component: () => import('../views/admin/AdminReservations.vue') },
      { path: 'violations', name: 'ViolationRecords', component: () => import('../views/admin/ViolationRecords.vue') },
      { path: 'config', name: 'SystemConfig', component: () => import('../views/admin/SystemConfig.vue') }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }
  if (to.meta.requiresAdmin) {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      try {
        const user = JSON.parse(userStr)
        const roles = user.roles || []
        const isAdmin = roles.some(r => {
          const name = typeof r === 'string' ? r : r.role_name
          return name === '管理员' || name === '超级管理员'
        })
        if (!isAdmin) {
          next('/student/home')
          return
        }
      } catch (e) {
        next('/login')
        return
      }
    } else {
      next('/login')
      return
    }
  }
  next()
})

export default router