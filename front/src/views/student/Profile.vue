<template>
  <div class="profile-page">
    <el-card>
      <template #header><span>个人中心</span></template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用户名">{{ user.username }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ user.email || '未设置' }}</el-descriptions-item>
        <el-descriptions-item label="信誉分">
          <el-tag :type="user.credit_score >= 80 ? 'success' : user.credit_score >= 60 ? 'warning' : 'danger'">
            {{ user.credit_score }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag v-for="role in user.roles" :key="role.role_name || role" size="small" style="margin-right:4px">
            {{ role.role_name || role }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ user.created_at }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px;">
        <el-button type="primary" @click="editDialogVisible = true">修改信息</el-button>
        <el-button @click="$router.push('/student/history')">查看历史记录</el-button>
      </div>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header><span>当前预约</span></template>
      <el-table :data="currentReservations" style="width: 100%" v-loading="loading">
        <el-table-column prop="res_id" label="编号" width="80" />
        <el-table-column prop="room_name" label="自习室" />
        <el-table-column prop="seat_number" label="座位号" width="100" />
        <el-table-column prop="start_time" label="开始时间" width="180" />
        <el-table-column prop="end_time" label="结束时间" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button v-if="row.status === 'PENDING'" size="small" type="primary" @click="handleCheckinClick(row)">签到</el-button>
            <el-button v-if="row.status === 'PENDING'" size="small" type="danger" @click="handleCancel(row)">取消</el-button>
            <el-button v-if="row.status === 'ACTIVE'" size="small" type="warning" @click="handleComplete(row)">提前结束</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="editDialogVisible" title="修改个人信息" width="400px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

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
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../stores/auth'
import { authAPI, reservationAPI, systemConfigAPI } from '../../api'

const authStore = useAuthStore()
const user = ref({ ...authStore.user })
const currentReservations = ref([])
const loading = ref(false)
const editDialogVisible = ref(false)
const saving = ref(false)
const editForm = ref({ email: user.value.email || '' })
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

const fetchCurrent = async () => {
  loading.value = true
  try {
    const res = await reservationAPI.getMyList({ status: 'PENDING,ACTIVE', size: 100 })
    currentReservations.value = res.data.items
  } catch (e) {}
  loading.value = false
}

const handleCancel = async (row) => {
  try {
    await ElMessageBox.confirm('确定要取消此预约吗？', '提示', { type: 'warning' })
    await reservationAPI.cancel(row.res_id)
    ElMessage.success('取消成功')
    fetchCurrent()
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
    fetchCurrent()
  } catch (e) {}
  checking.value = false
}

const handleComplete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要提前结束本次使用吗？', '提前结束', { type: 'warning' })
    await reservationAPI.complete(row.res_id)
    ElMessage.success('已提前结束使用')
    fetchCurrent()
  } catch (e) {}
}

const handleSave = async () => {
  saving.value = true
  try {
    await authAPI.updateMe({ email: editForm.value.email })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    await authStore.fetchUser()
    user.value = authStore.user
  } catch (e) {}
  saving.value = false
}

onMounted(() => {
  fetchGraceMinutes()
  fetchCurrent()
  authStore.fetchUser().then(() => { user.value = authStore.user })
})
</script>

<style scoped>
.profile-page {
  max-width: 900px;
  margin: 0 auto;
}
</style>