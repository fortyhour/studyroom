<template>
  <div class="history-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>预约历史</span>
          <div>
            <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width:140px" @change="fetchData">
              <el-option label="待签到" value="PENDING" />
              <el-option label="进行中" value="ACTIVE" />
              <el-option label="已完成" value="COMPLETED" />
              <el-option label="已取消" value="CANCELLED" />
              <el-option label="违约" value="VIOLATED" />
            </el-select>
          </div>
        </div>
      </template>
      <el-table :data="reservations" style="width: 100%" v-loading="loading" @row-click="(row) => $router.push(`/student/history/${row.res_id}`)">
        <el-table-column prop="res_id" label="编号" width="80" />
        <el-table-column prop="room_name" label="自习室" />
        <el-table-column prop="seat_number" label="座位号" width="100" />
        <el-table-column prop="start_time" label="开始时间" width="180" />
        <el-table-column prop="end_time" label="结束时间" width="180" />
        <el-table-column prop="created_at" label="预约时间" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <el-button v-if="row.status === 'PENDING'" size="small" type="primary" @click.stop="handleCheckinClick(row)">签到</el-button>
            <el-button v-if="row.status === 'PENDING'" size="small" type="danger" @click.stop="handleCancel(row)">取消</el-button>
            <el-button v-if="row.status === 'ACTIVE'" size="small" type="warning" @click.stop="handleComplete(row)">提前结束</el-button>
            <el-button v-if="row.status === 'COMPLETED' || row.status === 'CANCELLED' || row.status === 'VIOLATED'" size="small" type="success" @click.stop="reReserve(row)">再次预约</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 16px; text-align: right;">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <el-dialog v-model="checkinDialogVisible" title="签到" width="300px">
      <el-input v-model="checkinCode" placeholder="请输入签到码" />
      <template #footer>
        <el-button @click="checkinDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="checking" @click="handleCheckin">确认签到</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reservationAPI, systemConfigAPI, seatAPI, studyroomAPI } from '../../api'

const router = useRouter()

const loading = ref(false)
const reservations = ref([])
const page = ref(1)
const size = ref(10)
const total = ref(0)
const statusFilter = ref('')
const checkinDialogVisible = ref(false)
const checkinCode = ref('')
const checking = ref(false)
const currentCheckinRow = ref(null)
const graceMinutes = ref(15)

const statusType = (s) => ({ PENDING: 'warning', ACTIVE: 'success', COMPLETED: 'info', CANCELLED: 'info', VIOLATED: 'danger' }[s] || 'info')
const statusText = (s) => ({ PENDING: '待签到', ACTIVE: '进行中', COMPLETED: '已完成', CANCELLED: '已取消', VIOLATED: '违约' }[s] || s)

const fetchGraceMinutes = async () => {
  try {
    const res = await systemConfigAPI.getPublicConfigs()
    graceMinutes.value = parseInt(res.data.CHECKIN_GRACE_MINUTES) || 15
  } catch (e) {
    graceMinutes.value = 15
  }
}

const canCheckin = (row) => {
  const now = new Date()
  const startTime = new Date(row.start_time)
  const deadline = new Date(startTime.getTime() + graceMinutes.value * 60 * 1000)
  return now >= startTime && now <= deadline
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (statusFilter.value) params.status = statusFilter.value
    const res = await reservationAPI.getMyList(params)
    reservations.value = res.data.items
    total.value = res.data.total
  } catch (e) {}
  loading.value = false
}

const handleCancel = async (row) => {
  try {
    await ElMessageBox.confirm('确定要取消此预约吗？', '提示', { type: 'warning' })
    await reservationAPI.cancel(row.res_id)
    ElMessage.success('取消成功')
    fetchData()
  } catch (e) {}
}

const handleCheckinClick = (row) => {
  if (!canCheckin(row)) {
    const now = new Date()
    const startTime = new Date(row.start_time)
    if (now < startTime) {
      ElMessage.warning('签到时间未到')
    } else {
      ElMessage.warning('已超过签到宽限时间')
    }
    return
  }
  currentCheckinRow.value = row
  checkinCode.value = ''
  checkinDialogVisible.value = true
}

const handleCheckin = async () => {
  if (!checkinCode.value) {
    ElMessage.warning('请输入签到码')
    return
  }
  checking.value = true
  try {
    await reservationAPI.checkin(currentCheckinRow.value.res_id, checkinCode.value)
    ElMessage.success('签到成功')
    checkinDialogVisible.value = false
    fetchData()
  } catch (e) {}
  checking.value = false
}

const handleComplete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要提前结束本次使用吗？', '提前结束', { type: 'warning' })
    await reservationAPI.complete(row.res_id)
    ElMessage.success('已提前结束使用')
    fetchData()
  } catch (e) {}
}

const reReserve = async (row) => {
  try {
    const seatRes = await seatAPI.getDetail(row.seat_id)
    const seat = seatRes.data
    if (!seat.is_active) {
      ElMessage.warning('该座位已停用，无法再次预约')
      return
    }
    const roomRes = await studyroomAPI.getDetail(seat.room_id)
    if (!roomRes.data.is_available) {
      ElMessage.warning('该自习室已关闭，无法再次预约')
      return
    }
    router.push(`/student/seat/${row.seat_id}`)
  } catch (e) {
    ElMessage.warning('座位信息获取失败')
  }
}

onMounted(() => {
  fetchGraceMinutes()
  fetchData()
})
</script>

<style scoped>
.history-page {
  max-width: 1100px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.el-table {
  cursor: pointer;
}
</style>