<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NPopconfirm, NTag } from 'naive-ui'

import api from '@/api'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import { renderIcon } from '@/utils'
import {
  parseStatusMap,
  parseStatusOptions,
  sourceTypeMap,
  sourceTypeOptions,
  statusTypeMap,
} from '../constants'

defineOptions({ name: 'RedbookUpload' })

const $table = ref(null)
const queryItems = ref({})
const projectOptions = ref([])
const uploadLoading = ref(false)
const selectedFile = ref(null)
const fileInputRef = ref(null)
const uploadForm = ref({
  project_id: null,
  source_type: 'juguang',
  parse_now: true,
})

const columns = [
  { title: '文件名', key: 'original_file_name', width: 260, ellipsis: { tooltip: true } },
  {
    title: '数据源',
    key: 'source_type',
    width: 150,
    render(row) {
      return sourceTypeMap[row.source_type] || row.source_type
    },
  },
  {
    title: '解析状态',
    key: 'parse_status',
    width: 110,
    render(row) {
      return h(
        NTag,
        { type: statusTypeMap[row.parse_status] || 'default', size: 'small' },
        { default: () => parseStatusMap[row.parse_status] || row.parse_status }
      )
    },
  },
  { title: '总行数', key: 'total_rows', width: 90 },
  { title: '成功行', key: 'success_rows', width: 90 },
  { title: '失败行', key: 'failed_rows', width: 90 },
  { title: '警告数', key: 'warning_count', width: 90 },
  { title: '上传时间', key: 'upload_time', width: 170, ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    fixed: 'right',
    render(row) {
      return h(
        NPopconfirm,
        { onPositiveClick: () => handleDelete(row) },
        {
          trigger: () =>
            h(
              NButton,
              { size: 'small', type: 'error', disabled: row.deleting, loading: row.deleting },
              { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 16 }) }
            ),
          default: () => '确认删除该数据源文件及其解析数据吗？',
        }
      )
    },
  },
]

onMounted(async () => {
  await loadProjects()
  $table.value?.handleSearch()
})

async function loadProjects() {
  const res = await api.getRedbookProjects({ page: 1, page_size: 9999, status: 'active' })
  projectOptions.value = res.data.map((item) => ({
    label: `${item.project_name}（${item.project_code}）`,
    value: item.id,
  }))
}

async function handleUpload() {
  if (!uploadForm.value.project_id) {
    window.$message?.warning('请选择项目')
    return
  }
  const file = selectedFile.value
  if (!file) {
    fileInputRef.value?.click()
    return
  }
  const data = new FormData()
  data.append('project_id', uploadForm.value.project_id)
  data.append('source_type', uploadForm.value.source_type)
  data.append('parse_now', 'false')
  data.append('file', file)

  uploadLoading.value = true
  try {
    const res = await api.uploadRedbookFile(data)
    const uploadedFile = res.data || {}
    selectedFile.value = null
    queryItems.value.project_id = uploadForm.value.project_id
    $table.value?.handleSearch()

    if (uploadForm.value.parse_now && uploadedFile.id) {
      try {
        await api.parseRedbookFile({ file_id: uploadedFile.id })
        window.$message?.success('上传并解析完成')
      } catch (error) {
        console.error('redbook parse failed', error)
        window.$message?.error('文件已上传，解析失败，请在解析记录中查看错误')
      }
      $table.value?.handleSearch()
      return
    }
    window.$message?.success('上传成功')
  } catch (error) {
    console.error('redbook upload failed', error)
    window.$message?.error(error?.message || '上传失败')
  } finally {
    uploadLoading.value = false
  }
}

async function handleNativeFileChange(event) {
  const file = event.target.files?.[0]
  if (!file) return
  selectedFile.value = file
  event.target.value = ''
  await handleUpload()
}

async function handleDelete(row) {
  row.deleting = true
  try {
    await api.deleteRedbookFile({ file_id: row.id })
    window.$message?.success('删除成功')
    $table.value?.handleSearch()
  } finally {
    row.deleting = false
  }
}
</script>

<template>
  <CommonPage show-footer title="红书数据上传">
    <NGrid :cols="4" :x-gap="16" responsive="screen" class="mb-24">
      <NGi>
        <NFormItem label="项目">
          <NSelect
            v-model:value="uploadForm.project_id"
            filterable
            clearable
            :options="projectOptions"
            placeholder="选择项目"
          />
        </NFormItem>
      </NGi>
      <NGi>
        <NFormItem label="数据源">
          <NSelect v-model:value="uploadForm.source_type" :options="sourceTypeOptions" />
        </NFormItem>
      </NGi>
      <NGi>
        <NFormItem label="解析">
          <NSwitch v-model:value="uploadForm.parse_now">
            <template #checked>立即解析</template>
            <template #unchecked>仅上传</template>
          </NSwitch>
        </NFormItem>
      </NGi>
      <NGi flex items-end>
        <input
          ref="fileInputRef"
          class="hidden-file-input"
          type="file"
          accept=".xlsx,.xls,.csv"
          @change="handleNativeFileChange"
        />
        <NButton type="primary" :loading="uploadLoading" @click="handleUpload">
          <TheIcon icon="material-symbols:upload-file" :size="18" class="mr-5" />上传文件
        </NButton>
      </NGi>
    </NGrid>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getRedbookFiles"
      :scroll-x="1160"
    >
      <template #queryBar>
        <QueryBarItem label="项目" :label-width="50">
          <NSelect
            v-model:value="queryItems.project_id"
            filterable
            clearable
            :options="projectOptions"
            placeholder="全部项目"
          />
        </QueryBarItem>
        <QueryBarItem label="数据源" :label-width="60">
          <NSelect
            v-model:value="queryItems.source_type"
            clearable
            :options="sourceTypeOptions"
            placeholder="全部"
          />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="50">
          <NSelect
            v-model:value="queryItems.parse_status"
            clearable
            :options="parseStatusOptions"
            placeholder="全部"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>

<style scoped>
.hidden-file-input {
  display: none;
}
</style>
