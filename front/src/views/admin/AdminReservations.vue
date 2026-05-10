<template>
  <div class="admin-reservations">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>预约记录</span>
          <div class="filter-bar">
            <el-input v-model="filterUserId" placeholder="用户ID" clearable style="width:120px" />
            <el-select v-model="filterStatus" placeholder="状态" clearable style="width:120px">
              <el-option label="待签到" value="PENDING" />
              <el-option label="进行中" value="ACTIVE" />
              <el-option label="已完成" value="COMPLETED" />
              <el-option label="已取消" value="CANCELLED" />
              <el-option label="违约" value="VIOLATED" />
            </el-select>
            <el-button type="primary" @click="fetchData">搜索</el-button>
          </div>
        </div>
      </template>
      <el-table :data="reservations" style="width: 100%" v-loading="loading">
        <el-table-column prop="res_id" label="编号" width="80" />
        <el-table-column prop="username" label="用户" />
        <el-table-column prop="room_name" label="自习室" />
        <el-table-column prop="seat_number" label="座位号" width="100" />
        <el-table-column prop="start_time" label="开始时间" width="180" />
        <el-table-column prop="end_time" label="结束时间" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button v-if="row.status === 'PENDING'" size="small" type="danger" @click="handleCancel(row)">取消</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top:16px;text-align:right">
        <el-pagination v-model:current-page="page" v-model:page-size="size" :total="total" layout="total, prev, pager, next" @current-change="fetchData" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reservationAPI } from '../../api'

const loading = ref(false)
const reservations = ref([])
const page = ref(1)
const size = ref(10)
const total = ref(0)
const filterUserId = ref('')
const filterStatus = ref('')

const statusType = (s) => ({ PENDING: 'warning', ACTIVE: 'success', COMPLETED: 'info', CANCELLED: 'info', VIOLATED: 'danger' }[s] || 'info')
const statusText = (s) => ({ PENDING: '待签到', ACTIVE: '进行中', COMPLETED: '已完成', CANCELLED: '已取消', VIOLATED: '违约' }[s] || s)

const fetchData = async () => {
  loading.value = true
  const params = { page: page.value, size: size.value }
  if (filterUserId.value) params.user_id = filterUserId.value
  if (filterStatus.value) params.status = filterStatus.value
  const res = await reservationAPI.getAdminList(params)
  reservations.value = res.data.items
  total.value = res.data.total
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

onMounted(fetchData)
</script>

<style scoped>
.admin-reservations {
  max-width: 1400px;
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
</style>