<template>
  <div class="reservation-detail">
    <el-page-header @back="$router.push('/student/history')">
      <template #content><span>预约详情 #{{ reservation.res_id }}</span></template>
    </el-page-header>

    <el-card style="margin-top: 20px" v-loading="loading">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="自习室">{{ reservation.room_name }}</el-descriptions-item>
        <el-descriptions-item label="座位号">{{ reservation.seat_number }}号</el-descriptions-item>
        <el-descriptions-item label="预约开始">{{ reservation.start_time }}</el-descriptions-item>
        <el-descriptions-item label="预约结束">{{ reservation.end_time }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ reservation.created_at }}</el-descriptions-item>
        <el-descriptions-item label="签到时间">{{ reservation.actual_check_in || '未签到' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(reservation.status)">{{ statusText(reservation.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="位置">{{ reservation.location }}</el-descriptions-item>
        <el-descriptions-item label="插座">
          <el-tag :type="reservation.has_power ? 'success' : 'info'">{{ reservation.has_power ? '有' : '无' }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px;">
        <el-button v-if="reservation.status === 'PENDING'" type="danger" @click="handleCancel">取消预约</el-button>
        <el-button v-if="reservation.status === 'COMPLETED' || reservation.status === 'CANCELLED' || reservation.status === 'VIOLATED'" type="primary" @click="reReserve">再次预约该座位</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reservationAPI, seatAPI, studyroomAPI } from '../../api'

const route = useRoute()
const router = useRouter()
const resId = route.params.resId
const reservation = ref({})
const loading = ref(false)

const statusType = (s) => ({ PENDING: 'warning', ACTIVE: 'success', COMPLETED: 'info', CANCELLED: 'info', VIOLATED: 'danger' }[s] || 'info')
const statusText = (s) => ({ PENDING: '待签到', ACTIVE: '进行中', COMPLETED: '已完成', CANCELLED: '已取消', VIOLATED: '违约' }[s] || s)

const fetchDetail = async () => {
  loading.value = true
  try {
    const res = await reservationAPI.getDetail(resId)
    reservation.value = res.data
  } catch (e) {}
  loading.value = false
}

const handleCancel = async () => {
  try {
    await ElMessageBox.confirm('确定要取消此预约吗？', '提示', { type: 'warning' })
    await reservationAPI.cancel(resId)
    ElMessage.success('取消成功')
    fetchDetail()
  } catch (e) {}
}

const reReserve = async () => {
  const seatId = reservation.value.seat_id
  try {
    const seatRes = await seatAPI.getDetail(seatId)
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
    router.push(`/student/seat/${seatId}`)
  } catch (e) {
    ElMessage.warning('座位信息获取失败')
  }
}

onMounted(fetchDetail)
</script>

<style scoped>
.reservation-detail {
  max-width: 800px;
  margin: 0 auto;
}
</style>