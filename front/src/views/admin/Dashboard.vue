<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <div class="stat-card">
            <div class="stat-value">{{ overview.today_reservations }}</div>
            <div class="stat-label">今日预约总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div class="stat-card">
            <div class="stat-value danger">{{ overview.today_violations }}</div>
            <div class="stat-label">今日违约数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div class="stat-card">
            <div class="stat-value">{{ overview.room_stats?.length || 0 }}</div>
            <div class="stat-label">自习室数量</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px">
      <template #header><span>自习室占用情况</span></template>
      <el-table :data="overview.room_stats || []" style="width: 100%" v-loading="loading">
        <el-table-column prop="room_name" label="自习室" />
        <el-table-column prop="occupied_seats" label="已占用" />
        <el-table-column prop="total_seats" label="总座位" />
        <el-table-column label="占用率">
          <template #default="{ row }">
            <el-progress :percentage="row.occupancy_rate" :color="row.occupancy_rate > 80 ? '#f56c6c' : row.occupancy_rate > 50 ? '#e6a23c' : '#67c23a'" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { statisticsAPI } from '../../api'

const loading = ref(false)
const overview = ref({})

const fetchData = async () => {
  loading.value = true
  const res = await statisticsAPI.getOverview()
  overview.value = res.data
  loading.value = false
}

onMounted(fetchData)
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}
.stat-card {
  text-align: center;
  padding: 10px;
}
.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #409eff;
}
.stat-value.danger {
  color: #f56c6c;
}
.stat-label {
  color: #909399;
  margin-top: 8px;
}
</style>