<template>
  <div class="student-layout">
    <el-container>
      <el-header>
        <div class="header-content">
          <h3 @click="$router.push('/student/home')" style="cursor:pointer">自习座位预约系统</h3>
          <div class="header-right">
            <el-menu mode="horizontal" :ellipsis="false" router>
              <el-menu-item index="/student/home">首页</el-menu-item>
              <el-menu-item index="/student/history">我的预约</el-menu-item>
              <el-menu-item index="/student/profile">个人中心</el-menu-item>
            </el-menu>
            <el-button v-if="authStore.isAdmin" @click="$router.push('/admin/dashboard')">返回管理端</el-button>
            <el-dropdown>
              <span class="user-info">
                <el-icon><User /></el-icon>
                {{ authStore.user?.username }}
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="$router.push('/student/profile')">个人中心</el-dropdown-item>
                  <el-dropdown-item v-if="authStore.isAdmin" @click="$router.push('/admin/dashboard')">管理后台</el-dropdown-item>
                  <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.student-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f5f7fa;
}
.student-layout > .el-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.el-header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
  flex-shrink: 0;
}
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}
.header-content h3 {
  color: #409eff;
  margin: 0;
}
.header-right {
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
  flex: 1;
  overflow-y: auto;
}
</style>