<template>
  <div class="violation-records">
    <el-card>
      <template #header><span>违约记录</span></template>
      <el-table :data="violations" style="width: 100%" v-loading="loading">
        <el-table-column prop="violation_id" label="编号" width="80" />
        <el-table-column prop="username" label="用户" />
        <el-table-column prop="room_name" label="自习室" />
        <el-table-column prop="seat_number" label="座位号" width="100" />
        <el-table-column prop="reason" label="原因" />
        <el-table-column prop="penalty" label="扣分" width="80" />
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>
      <div style="margin-top:16px;text-align:right">
        <el-pagination v-model:current-page="page" v-model:page-size="size" :total="total" layout="total, prev, pager, next" @current-change="fetchData" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { violationAPI } from '../../api'

const loading = ref(false)
const violations = ref([])
const page = ref(1)
const size = ref(10)
const total = ref(0)

const fetchData = async () => {
  loading.value = true
  const res = await violationAPI.getList({ page: page.value, size: size.value })
  violations.value = res.data.items
  total.value = res.data.total
  loading.value = false
}

onMounted(fetchData)
</script>

<style scoped>
.violation-records {
  max-width: 1200px;
  margin: 0 auto;
}
</style>