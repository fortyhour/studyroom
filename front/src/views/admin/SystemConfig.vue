<template>
  <div class="system-config">
    <el-card>
      <template #header><span>系统参数配置</span></template>
      <el-table :data="configs" style="width: 100%" v-loading="loading">
        <el-table-column prop="config_key" label="配置键" />
        <el-table-column prop="config_value" label="当前值" />
        <el-table-column prop="description" label="说明" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">修改</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="修改配置" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="配置键">
          <el-input :value="form.config_key" disabled />
        </el-form-item>
        <el-form-item label="配置值">
          <el-input v-model="form.config_value" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input :value="form.description" disabled />
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
import { ElMessage } from 'element-plus'
import { systemConfigAPI } from '../../api'

const loading = ref(false)
const configs = ref([])
const dialogVisible = ref(false)
const form = ref({})
const saving = ref(false)

const fetchData = async () => {
  loading.value = true
  const res = await systemConfigAPI.getList()
  configs.value = res.data
  loading.value = false
}

const showEditDialog = (row) => {
  form.value = { ...row }
  dialogVisible.value = true
}

const handleSave = async () => {
  saving.value = true
  try {
    await systemConfigAPI.update(form.value.config_key, form.value.config_value)
    ElMessage.success('更新成功')
    dialogVisible.value = false
    fetchData()
  } catch (e) {}
  saving.value = false
}

onMounted(fetchData)
</script>

<style scoped>
.system-config {
  max-width: 900px;
  margin: 0 auto;
}
</style>