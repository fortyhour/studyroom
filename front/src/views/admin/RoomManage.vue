<template>
  <div class="room-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>自习室管理</span>
          <el-button type="primary" @click="showAddDialog">添加自习室</el-button>
        </div>
      </template>
      <el-table :data="rooms" style="width: 100%" v-loading="loading">
        <el-table-column prop="room_id" label="ID" width="80" />
        <el-table-column prop="room_name" label="名称" />
        <el-table-column prop="location" label="位置" />
        <el-table-column prop="open_time" label="开放时间" />
        <el-table-column prop="close_time" label="关闭时间" />
        <el-table-column prop="is_available" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_available ? 'success' : 'danger'">{{ row.is_available ? '开放' : '关闭' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="340">
          <template #default="{ row }">
            <el-button size="small" @click="showCodeDialog(row)">签到码</el-button>
            <el-button size="small" @click="$router.push(`/admin/seats?roomId=${row.room_id}`)">座位管理</el-button>
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑自习室' : '添加自习室'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="form.room_name" />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="form.location" />
        </el-form-item>
        <el-form-item label="开放时间">
          <el-time-picker v-model="form.open_time" format="HH:mm" value-format="HH:mm" />
        </el-form-item>
        <el-form-item label="关闭时间">
          <el-time-picker v-model="form.close_time" format="HH:mm" value-format="HH:mm" />
        </el-form-item>
        <el-form-item label="是否开放">
          <el-switch v-model="form.is_available" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="codeDialogVisible" :title="`签到码 - ${currentRoom?.room_name || ''}`" width="400px">
      <div style="text-align:center;">
        <p style="color:#909399;margin-bottom:4px;">今日签到码</p>
        <p style="font-size:32px;font-weight:bold;letter-spacing:8px;font-family:monospace;margin:0;color:#409eff;">{{ checkinCode }}</p>
        <p style="color:#909399;margin-top:12px;">日期：{{ codeDate }}</p>
      </div>
      <template #footer>
        <el-button @click="codeDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="refreshing" @click="handleRefreshCode">刷新签到码</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { studyroomAPI } from '../../api'

const loading = ref(false)
const rooms = ref([])
const dialogVisible = ref(false)
const editing = ref(null)
const saving = ref(false)
const codeDialogVisible = ref(false)
const checkinCode = ref('')
const codeDate = ref('')
const currentRoom = ref(null)
const refreshing = ref(false)
const form = ref({
  room_name: '',
  location: '',
  open_time: '07:00',
  close_time: '22:00',
  is_available: true,
  description: ''
})

const fetchData = async () => {
  loading.value = true
  const res = await studyroomAPI.getList({ size: 100 })
  rooms.value = res.data.items
  loading.value = false
}

const showAddDialog = () => {
  editing.value = null
  form.value = { room_name: '', location: '', open_time: '07:00', close_time: '22:00', is_available: true, description: '' }
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
      await studyroomAPI.update(editing.value.room_id, form.value)
    } else {
      await studyroomAPI.create(form.value)
    }
    ElMessage.success(editing.value ? '更新成功' : '创建成功')
    dialogVisible.value = false
    fetchData()
  } catch (e) {}
  saving.value = false
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该自习室吗？', '提示', { type: 'warning' })
    await studyroomAPI.delete(row.room_id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e) {}
}

const showCodeDialog = async (row) => {
  currentRoom.value = row
  try {
    const res = await studyroomAPI.getCheckinCode(row.room_id)
    checkinCode.value = res.data.checkin_code
    codeDate.value = res.data.code_date
  } catch (e) {
    ElMessage.error('获取签到码失败')
    return
  }
  codeDialogVisible.value = true
}

const handleRefreshCode = async () => {
  refreshing.value = true
  try {
    const res = await studyroomAPI.refreshCheckinCode(currentRoom.value.room_id)
    checkinCode.value = res.data.checkin_code
    ElMessage.success('签到码已刷新')
  } finally {
    refreshing.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.room-manage {
  max-width: 1200px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>