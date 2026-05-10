<template>
  <div class="home-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>自习室列表</span>
          <div class="filter-bar">
            <el-input v-model="keyword" placeholder="搜索位置" clearable style="width: 200px" />
            <el-button type="primary" @click="fetchRooms">搜索</el-button>
          </div>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :span="8" v-for="room in rooms" :key="room.room_id" style="margin-bottom: 20px">
          <el-card shadow="hover" class="room-card" :class="{ 'room-disabled': !room.is_available }" @click="goRoom(room)">
            <h4>{{ room.room_name }}</h4>
            <p><el-icon><Location /></el-icon> {{ room.location }}</p>
            <p><el-icon><Clock /></el-icon> {{ room.open_time }} - {{ room.close_time }}</p>
            <el-progress :percentage="room.total_seats ? Math.round(room.occupied_seats / room.total_seats * 100) : 0" :color="room.free_seats > 0 ? '#67c23a' : '#f56c6c'">
              <template #default="{ percentage }">
                <span>{{ room.free_seats }}/{{ room.total_seats }} 空闲</span>
              </template>
            </el-progress>
            <el-tag :type="room.is_available ? 'success' : 'danger'" size="small" style="margin-top: 8px">
              {{ room.is_available ? '开放中' : '已关闭' }}
            </el-tag>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { studyroomAPI } from '../../api'

const router = useRouter()
const rooms = ref([])
const keyword = ref('')

const fetchRooms = async () => {
  const params = {}
  if (keyword.value) params.location = keyword.value
  const res = await studyroomAPI.getList(params)
  rooms.value = res.data.items
}

const goRoom = (room) => {
  if (!room.is_available) {
    ElMessage.warning('该自习室已关闭，无法进入')
    return
  }
  router.push(`/student/room/${room.room_id}`)
}

onMounted(fetchRooms)
</script>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.filter-bar {
  display: flex;
  gap: 10px;
}
.room-card {
  cursor: pointer;
  transition: transform 0.2s;
}
.room-card:hover {
  transform: translateY(-4px);
}
.room-card.room-disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
.room-card.room-disabled:hover {
  transform: none;
}
.room-card h4 {
  margin: 0 0 8px;
}
.room-card p {
  color: #909399;
  margin: 4px 0;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>