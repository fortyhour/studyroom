<template>
  <div class="seat-detail">
    <el-page-header @back="$router.go(-1)">
      <template #content>
        <span>{{ seat.seat_number }}号座位</span>
      </template>
    </el-page-header>

    <el-card style="margin-top: 20px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="座位编号">{{ seat.seat_number }}号</el-descriptions-item>
        <el-descriptions-item label="插座">
          <el-tag :type="seat.has_power ? 'success' : 'info'">{{ seat.has_power ? '有' : '无' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="开放时间">{{ availability.open_time }} - {{ availability.close_time }}</el-descriptions-item>
        <el-descriptions-item label="日期">{{ date }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>时间段（绿=开放中 红=已占用）</span>
          <el-date-picker v-model="date" type="date" value-format="YYYY-MM-DD" :disabled-date="disabledDate" @change="fetchAvailability" />
        </div>
      </template>

      <div v-if="slots.length === 0" style="text-align:center;color:#909399;padding:20px;">
        暂无数据
      </div>

      <div v-else class="time-slots">
        <div
          v-for="(slot, index) in slots"
          :key="slot.start"
          class="time-slot"
          :class="{
            selected: selectedIndices.has(index),
            occupied: !slot.free,
            free: slot.free
          }"
          @click="toggleSlot(index)"
        >
          {{ slot.start }} - {{ slot.end }}
        </div>
      </div>

      <div v-if="selectedIndices.size > 0" style="margin-top: 20px; text-align: center;">
        <span>已选择 {{ selectedIndices.size }} 小时</span>
        <el-button type="primary" style="margin-left: 16px" :loading="submitting" @click="handleReserve">
          立即预约
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { seatAPI, reservationAPI, systemConfigAPI } from '../../api'

const route = useRoute()
const router = useRouter()
const seatId = route.params.seatId
const seat = ref({})
const availability = ref({})
const todayLocal = new Date()
const dateStr = `${todayLocal.getFullYear()}-${String(todayLocal.getMonth() + 1).padStart(2, '0')}-${String(todayLocal.getDate()).padStart(2, '0')}`
const date = ref(dateStr)
const slots = ref([])
const submitting = ref(false)
const selectedIndices = ref(new Set())
const maxReservationDays = ref(7)

const fetchSeat = async () => {
  const res = await seatAPI.getDetail(seatId)
  seat.value = res.data
}

const fetchMaxDays = async () => {
  try {
    const res = await systemConfigAPI.getPublicConfigs()
    maxReservationDays.value = parseInt(res.data.MAX_RESERVATION_DAYS) || 7
  } catch (e) {
    maxReservationDays.value = 7
  }
}

const disabledDate = (time) => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const maxDate = new Date(today)
  maxDate.setDate(today.getDate() + maxReservationDays.value)
  return time.getTime() < today.getTime() || time.getTime() > maxDate.getTime()
}

const fetchAvailability = async () => {
  const res = await seatAPI.getAvailability(seatId, date.value)
  availability.value = res.data
  const rawSlots = res.data.slots
  const todayStr = `${todayLocal.getFullYear()}-${String(todayLocal.getMonth() + 1).padStart(2, '0')}-${String(todayLocal.getDate()).padStart(2, '0')}`
  if (date.value === todayStr) {
    const nowHour = new Date().getHours()
    for (const slot of rawSlots) {
      const endHour = parseInt(slot.end.split(':')[0])
      if (endHour <= nowHour) {
        slot.free = false
      }
    }
  }
  slots.value = rawSlots
  selectedIndices.value = new Set()
}

const toggleSlot = (index) => {
  const slot = slots.value[index]
  if (!slot.free) return

  const current = selectedIndices.value
  if (current.has(index)) {
    current.delete(index)
    selectedIndices.value = new Set(current)
    return
  }

  if (current.size > 0) {
    const selected = [...current].sort((a, b) => a - b)
    const last = selected[selected.length - 1]
    const first = selected[0]
    if (index === last + 1) {
      current.add(index)
      selectedIndices.value = new Set(current)
    } else if (index === first - 1) {
      current.add(index)
      selectedIndices.value = new Set(current)
    } else {
      ElMessage.warning('请选择连续的时段')
    }
  } else {
    current.add(index)
    selectedIndices.value = new Set(current)
  }
}

const handleReserve = async () => {
  if (selectedIndices.value.size === 0) {
    ElMessage.warning('请选择时间段')
    return
  }
  const selected = [...selectedIndices.value].sort((a, b) => a - b)
  const start = slots.value[selected[0]].start
  const end = slots.value[selected[selected.length - 1]].end
  submitting.value = true
  try {
    await reservationAPI.create({
      seat_id: parseInt(seatId),
      start_time: `${date.value} ${start}:00`,
      end_time: `${date.value} ${end}:00`
    })
    ElMessage.success('预约成功')
    router.push('/student/history')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchMaxDays()
  fetchSeat()
  fetchAvailability()
})
</script>

<style scoped>
.seat-detail {
  max-width: 1000px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.time-slots {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}
.time-slot {
  padding: 12px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}
.time-slot.free {
  background: #f0f9eb;
  color: #67c23a;
}
.time-slot.free:hover {
  border-color: #409eff;
}
.time-slot.occupied {
  background: #fef0f0;
  color: #f56c6c;
  cursor: not-allowed;
}
.time-slot.selected {
  background: #409eff;
  color: #fff;
  border-color: #409eff;
}
</style>