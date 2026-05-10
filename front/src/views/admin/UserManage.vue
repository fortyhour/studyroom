<template>
  <div class="user-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-input v-model="keyword" placeholder="搜索学号/工号" clearable style="width:200px" @change="fetchData" />
        </div>
      </template>
      <el-table :data="users" style="width: 100%" v-loading="loading">
        <el-table-column prop="user_id" label="ID" width="80" />
        <el-table-column prop="username" label="学号/工号" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="credit_score" label="信誉分" width="100">
          <template #default="{ row }">
            <el-tag :type="row.credit_score >= 80 ? 'success' : row.credit_score >= 60 ? 'warning' : 'danger'">
              {{ row.credit_score }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="角色">
          <template #default="{ row }">
            <el-tag v-for="r in (row.roles || [])" :key="r" size="small" style="margin-right:4px">{{ r }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" @click="showRoleDialog(row)">分配角色</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top:16px;text-align:right">
        <el-pagination v-model:current-page="page" v-model:page-size="size" :total="total" layout="total, prev, pager, next" @current-change="fetchData" />
      </div>
    </el-card>

    <el-dialog v-model="editDialogVisible" title="编辑用户" width="400px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="信誉分">
          <el-input-number v-model="editForm.credit_score" :min="0" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="roleDialogVisible" title="分配角色" width="400px">
      <el-checkbox-group v-model="selectedRoleIds">
        <el-checkbox v-for="r in allRoles" :key="r.role_id" :value="r.role_id">{{ r.role_name }}</el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="assigning" @click="handleAssignRoles">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userAPI, roleAPI } from '../../api'

const loading = ref(false)
const users = ref([])
const page = ref(1)
const size = ref(10)
const total = ref(0)
const keyword = ref('')
const roleDialogVisible = ref(false)
const allRoles = ref([])
const selectedRoleIds = ref([])
const assigning = ref(false)
const currentUser = ref(null)
const editDialogVisible = ref(false)
const editForm = ref({ user_id: null, email: '', credit_score: 100 })
const saving = ref(false)

const fetchData = async () => {
  loading.value = true
  const res = await userAPI.getList({ page: page.value, size: size.value, keyword: keyword.value })
  users.value = res.data.items
  total.value = res.data.total
  loading.value = false
}

const fetchRoles = async () => {
  const res = await roleAPI.getList()
  allRoles.value = res.data
}

const showEditDialog = (row) => {
  currentUser.value = row
  editForm.value = {
    user_id: row.user_id,
    email: row.email || '',
    credit_score: row.credit_score
  }
  editDialogVisible.value = true
}

const handleSaveEdit = async () => {
  saving.value = true
  try {
    await userAPI.update(editForm.value.user_id, {
      email: editForm.value.email,
      credit_score: editForm.value.credit_score
    })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    fetchData()
  } finally {
    saving.value = false
  }
}

const showRoleDialog = async (row) => {
  currentUser.value = row
  await fetchRoles()
  const detail = await userAPI.getDetail(row.user_id)
  const roleNames = detail.data.roles || []
  selectedRoleIds.value = allRoles.value.filter(r => roleNames.includes(r.role_name)).map(r => r.role_id)
  roleDialogVisible.value = true
}

const handleAssignRoles = async () => {
  assigning.value = true
  try {
    await userAPI.assignRoles(currentUser.value.user_id, selectedRoleIds.value)
    ElMessage.success('角色分配成功')
    roleDialogVisible.value = false
    fetchData()
  } catch (e) {}
  assigning.value = false
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该用户吗？', '提示', { type: 'warning' })
    await userAPI.delete(row.user_id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e) {}
}

onMounted(fetchData)
</script>

<style scoped>
.user-manage {
  max-width: 1200px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>