<template>
  <div class="room-detail">
    <el-page-header @back="$router.push('/student/home')">
      <template #content>
        <span>{{ room.room_name }}</span>
      </template>
    </el-page-header>

    <el-card style="margin-top: 20px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="位置">{{ room.location }}</el-descriptions-item>
        <el-descriptions-item label="开放时间">{{ room.open_time }} - {{ room.close_time }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="room.is_available ? 'success' : 'danger'">{{ room.is_available ? '开放中' : '已关闭' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="空闲座位">{{ room.free_seats }}/{{ room.total_seats }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ room.description || '无' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>座位列表</span>
          <div>
            <el-switch v-model="hasPowerFilter" active-text="仅看有插座" style="margin-right: 12px" @change="fetchSeats" />
          </div>
        </div>
      </template>
      <div class="seat-grid">
        <div
          v-for="seat in seats"
          :key="seat.seat_id"
          class="seat-item"
          :class="{ occupied: seat.is_occupied, disabled: !seat.is_active }"
          @click="goSeat(seat)"
        >
          <div class="seat-number">{{ seat.seat_number }}号</div>
          <div v-if="seat.has_power" class="power-tag">有插座</div>
          <el-tag v-if="!seat.is_active" type="info" size="small">停用</el-tag>
          <el-tag v-else :type="seat.is_occupied ? 'danger' : 'success'" size="small">
            {{ seat.is_occupied ? '占用' : '开放中' }}
          </el-tag>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { studyroomAPI, seatAPI } from '../../api'

const route = useRoute()
const router = useRouter()
const roomId = route.params.roomId
const room = ref({})
const seats = ref([])
const hasPowerFilter = ref(false)

const fetchRoom = async () => {
  const res = await studyroomAPI.getDetail(roomId)
  room.value = res.data
}

const fetchSeats = async () => {
  const params = {}
  if (hasPowerFilter.value) params.has_power = true
  const res = await seatAPI.getList(roomId, params)
  seats.value = res.data
}

const goSeat = (seat) => {
  if (!seat.is_active) {
    ElMessage.warning('该座位已停用')
    return
  }
  router.push(`/student/seat/${seat.seat_id}`)
}

onMounted(() => {
  fetchRoom()
  fetchSeats()
})
</script>

<style scoped>
.room-detail {
  max-width: 1000px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.seat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 16px;
}
.seat-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}
.seat-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}
.seat-item.occupied {
  background: #fef0f0;
  border-color: #f56c6c;
}
.seat-item.disabled {
  background: #f5f7fa;
  border-color: #dcdfe6;
  cursor: not-allowed;
  opacity: 0.5;
}
.seat-item.disabled:hover {
  border-color: #dcdfe6;
  box-shadow: none;
}
.seat-number {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 8px;
}
.power-tag {
  color: #67c23a;
  font-size: 12px;
  margin-bottom: 4px;
}
</style>