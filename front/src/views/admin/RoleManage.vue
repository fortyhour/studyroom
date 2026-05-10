<template>
  <div class="role-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>角色管理</span>
          <el-button type="primary" @click="showAddDialog">添加角色</el-button>
        </div>
      </template>
      <el-table :data="roles" style="width: 100%" v-loading="loading">
        <el-table-column prop="role_name" label="角色名" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="is_system" label="系统角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_system ? 'warning' : 'info'">{{ row.is_system ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260">
          <template #default="{ row }">
            <el-button size="small" @click="showPermissionDialog(row)">设置权限</el-button>
            <el-button size="small" @click="showEditDialog(row)" :disabled="row.is_system">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)" :disabled="row.is_system">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="permDialogVisible" title="设置权限" width="700px">
      <el-checkbox-group v-model="selectedPermIds" class="perm-checkbox-grid">
        <el-checkbox v-for="p in allPermissions" :key="p.perm_id" :value="p.perm_id">
          {{ p.perm_name }} ({{ p.perm_code }})
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="permDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="settingPerms" @click="handleSetPermissions">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑角色' : '添加角色'" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="角色名">
          <el-input v-model="form.role_name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" />
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { roleAPI, permissionAPI } from '../../api'

const loading = ref(false)
const roles = ref([])
const allPermissions = ref([])
const dialogVisible = ref(false)
const editing = ref(null)
const saving = ref(false)
const form = ref({ role_name: '', description: '' })
const permDialogVisible = ref(false)
const selectedPermIds = ref([])
const settingPerms = ref(false)
const currentRole = ref(null)

const fetchData = async () => {
  loading.value = true
  const res = await roleAPI.getList()
  roles.value = res.data
  loading.value = false
}

const fetchPermissions = async () => {
  const res = await permissionAPI.getList()
  allPermissions.value = res.data
}

const showAddDialog = () => {
  editing.value = null
  form.value = { role_name: '', description: '' }
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  editing.value = row
  form.value = { role_name: row.role_name, description: row.description }
  dialogVisible.value = true
}

const handleSave = async () => {
  saving.value = true
  try {
    if (editing.value) {
      await roleAPI.update(editing.value.role_id, form.value)
    } else {
      await roleAPI.create(form.value)
    }
    ElMessage.success(editing.value ? '更新成功' : '创建成功')
    dialogVisible.value = false
    fetchData()
  } catch (e) {}
  saving.value = false
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该角色吗？', '提示', { type: 'warning' })
    await roleAPI.delete(row.role_id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e) {}
}

const showPermissionDialog = async (row) => {
  currentRole.value = row
  await fetchPermissions()
  const res = await roleAPI.getPermissions(row.role_id)
  selectedPermIds.value = res.data.map(p => p.perm_id)
  permDialogVisible.value = true
}

const handleSetPermissions = async () => {
  settingPerms.value = true
  try {
    await roleAPI.setPermissions(currentRole.value.role_id, selectedPermIds.value)
    ElMessage.success('权限设置成功')
    permDialogVisible.value = false
    fetchData()
  } catch (e) {}
  settingPerms.value = false
}

onMounted(fetchData)
</script>

<style scoped>
.role-manage {
  max-width: 1000px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.perm-checkbox-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 16px;
}
.perm-checkbox-grid .el-checkbox {
  margin-right: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>