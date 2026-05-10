<template>
  <div class="seat-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>座位管理</span>
          <div>
            <el-select v-model="selectedRoomId" placeholder="选择自习室" style="width:200px;margin-right:10px" @change="fetchData">
              <el-option v-for="r in rooms" :key="r.room_id" :label="r.room_name" :value="r.room_id" />
            </el-select>
            <el-button type="primary" :disabled="!selectedRoomId" @click="showAddDialog">添加座位</el-button>
          </div>
        </div>
      </template>
      <el-table :data="seats" style="width: 100%" v-loading="loading">
        <el-table-column prop="seat_id" label="ID" width="80" />
        <el-table-column prop="seat_number" label="座位编号" width="120" />
        <el-table-column prop="has_power" label="插座" width="100">
          <template #default="{ row }">
            <el-tag :type="row.has_power ? 'success' : 'info'">{{ row.has_power ? '有' : '无' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">{{ row.is_active ? '可用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑座位' : '添加座位'" width="400px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="座位编号">
          <el-input-number v-model="form.seat_number" :min="1" :disabled="!!editing" />
        </el-form-item>
        <el-form-item label="插座">
          <el-switch v-model="form.has_power" />
        </el-form-item>
        <el-form-item label="是否可用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { studyroomAPI, seatAPI } from '../../api'

const route = useRoute()
const rooms = ref([])
const seats = ref([])
const selectedRoomId = ref(null)
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const saving = ref(false)
const form = ref({ seat_number: 1, has_power: false, is_active: true })

const fetchRooms = async () => {
  const res = await studyroomAPI.getList({ size: 100 })
  rooms.value = res.data.items
}

const fetchSeats = async () => {
  if (!selectedRoomId.value) { seats.value = []; return }
  loading.value = true
  const res = await seatAPI.getList(selectedRoomId.value)
  seats.value = res.data
  loading.value = false
}

const fetchData = async () => {
  await fetchSeats()
}

const showAddDialog = () => {
  editing.value = null
  form.value = { seat_number: (seats.value.length || 0) + 1, has_power: false, is_active: true }
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  editing.value = row
  form.value = { ...row }
  dialogVisible.value = true
}

const handleSave = async () => {
  saving.value = true
  try {
    if (editing.value) {
      await seatAPI.update(editing.value.seat_id, form.value)
    } else {
      await seatAPI.create(selectedRoomId.value, form.value)
    }
    ElMessage.success(editing.value ? '更新成功' : '创建成功')
    dialogVisible.value = false
    fetchSeats()
  } catch (e) {}
  saving.value = false
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该座位吗？', '提示', { type: 'warning' })
    await seatAPI.delete(row.seat_id)
    ElMessage.success('删除成功')
    fetchSeats()
  } catch (e) {}
}

onMounted(() => {
  fetchRooms()
  const roomIdParam = route.query.roomId
  if (roomIdParam) {
    selectedRoomId.value = parseInt(roomIdParam)
    fetchSeats()
  }
})
</script>

<style scoped>
.seat-manage {
  max-width: 1000px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>