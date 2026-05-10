<template>
  <div class="admin-layout">
    <el-container>
      <el-aside width="220px">
        <div class="aside-header">
          <h3>管理后台</h3>
        </div>
        <el-menu router :default-active="route.path" background-color="#304156" text-color="#bfcbd9" active-text-color="#409eff">
          <el-menu-item index="/admin/dashboard">
            <el-icon><DataAnalysis /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/admin/rooms">
            <el-icon><OfficeBuilding /></el-icon>
            <span>自习室管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/seats">
            <el-icon><Grid /></el-icon>
            <span>座位管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/reservations">
            <el-icon><Tickets /></el-icon>
            <span>预约记录</span>
          </el-menu-item>
          <el-menu-item index="/admin/violations">
            <el-icon><WarningFilled /></el-icon>
            <span>违约记录</span>
          </el-menu-item>
          <el-menu-item index="/admin/users">
            <el-icon><UserFilled /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/roles">
            <el-icon><Setting /></el-icon>
            <span>角色管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/config">
            <el-icon><Tools /></el-icon>
            <span>参数调整</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-container>
        <el-header>
          <div class="admin-header">
            <span class="title">{{ route.meta.title || '' }}</span>
            <div class="header-actions">
              <el-button @click="$router.push('/student/home')">返回学生端</el-button>
              <el-dropdown>
                <span class="user-info">
                  <el-icon><User /></el-icon>
                  {{ authStore.user?.username }}
                </span>
                <template #dropdown>
                  <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-header>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
  overflow: hidden;
}
.admin-layout > .el-container {
  height: 100%;
}
.admin-layout > .el-container > .el-container {
  display: flex;
  flex-direction: column;
}
.el-aside {
  background: #304156;
  height: 100vh;
  overflow-y: auto;
}
.aside-header {
  padding: 16px;
  text-align: center;
}
.aside-header h3 {
  color: #fff;
  margin: 0;
  font-size: 16px;
}
.el-header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
  flex-shrink: 0;
}
.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}
.admin-header .title {
  font-size: 16px;
  font-weight: bold;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}
.el-main {
  padding: 20px;
  background: #f5f7fa;
  flex: 1;
  overflow-y: auto;
}
</style>