<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NPopconfirm, NTag } from 'naive-ui'

import api from '@/api'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import { renderIcon } from '@/utils'
import { statusTypeMap } from '../constants'

defineOptions({ name: 'RedbookTaskMapping' })

const $table = ref(null)
const formRef = ref(null)
const queryItems = ref({})
const projectOptions = ref([])
const modalVisible = ref(false)
const modalTitle = ref('')
const saving = ref(false)
const taskIdOptions = ref([])
const taskIdOptionsLoading = ref(false)
const mappingOptions = ref({
  blogger_type: [],
  product_category: [],
})
const mappingOptionsLoading = ref(false)
const form = ref(getDefaultForm())

const rules = {
  project_id: [{ required: true, type: 'number', message: '请选择项目', trigger: ['change'] }],
  order_id: [{ required: true, message: '请输入订单 ID', trigger: ['blur', 'input'] }],
}

const columns = [
  { title: '订单 ID', key: 'order_id', width: 170, ellipsis: { tooltip: true } },
  { title: '任务 ID', key: 'task_id', width: 150, ellipsis: { tooltip: true } },
  { title: '任务名称', key: 'task_name', width: 180, ellipsis: { tooltip: true } },
  { title: '任务类型', key: 'task_type', width: 110, ellipsis: { tooltip: true } },
  { title: '产品', key: 'product_name', width: 130, ellipsis: { tooltip: true } },
  { title: '产品分类', key: 'product_category', width: 120, ellipsis: { tooltip: true } },
  { title: '达人分类', key: 'blogger_type', width: 110, ellipsis: { tooltip: true } },
  { title: '合作模式', key: 'cooperation_mode', width: 110, ellipsis: { tooltip: true } },
  {
    title: '状态',
    key: 'status',
    width: 90,
    render(row) {
      return h(
        NTag,
        { type: statusTypeMap[row.status] || 'default', size: 'small' },
        { default: () => (row.status === 'inactive' ? '停用' : '启用') }
      )
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 170,
    fixed: 'right',
    render(row) {
      return [
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            style: 'margin-right: 8px;',
            onClick: () => openEdit(row),
          },
          { default: () => '编辑', icon: renderIcon('material-symbols:edit', { size: 16 }) }
        ),
        h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete(row.id) },
          {
            trigger: () =>
              h(
                NButton,
                { size: 'small', type: 'error' },
                { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 16 }) }
              ),
            default: () => '确认删除该任务组吗？',
          }
        ),
      ]
    },
  },
]

onMounted(async () => {
  await loadProjects()
  $table.value?.handleSearch()
})

function getDefaultForm() {
  return {
    project_id: null,
    order_id: '',
    task_id: '',
    task_name: '',
    task_type: '',
    product_name: '',
    product_category: '',
    blogger_type: '',
    cooperation_mode: '',
    status: 'active',
  }
}

async function loadProjects() {
  const res = await api.getRedbookProjects({ page: 1, page_size: 9999 })
  projectOptions.value = res.data.map((item) => ({
    label: `${item.project_name}（${item.project_code}）`,
    value: item.id,
  }))
}

function mergeCurrentOption(options = [], value) {
  if (!value || options.some((item) => item.value === value)) return options
  return [{ label: value, value }, ...options]
}

async function loadMappingOptions(projectId, current = {}) {
  mappingOptions.value = { blogger_type: [], product_category: [] }
  if (!projectId) return
  mappingOptionsLoading.value = true
  try {
    const res = await api.getRedbookMappingOptions({ project_id: projectId })
    mappingOptions.value = {
      blogger_type: mergeCurrentOption(res.data?.blogger_type || [], current.blogger_type),
      product_category: mergeCurrentOption(res.data?.product_category || [], current.product_category),
    }
  } finally {
    mappingOptionsLoading.value = false
  }
}

async function loadPgyTaskOptions(projectId, currentTaskId = '') {
  if (!projectId) {
    taskIdOptions.value = []
    return
  }
  taskIdOptionsLoading.value = true
  try {
    const res = await api.getRedbookPgyTaskOptions({ project_id: projectId })
    const options = (res.data || []).map((item) => ({
      label: item.label || item.task_id || item.value,
      value: item.value || item.task_id,
      task_name: item.task_name,
      product_name: item.product_name,
      product_category: item.product_category || item.product_name,
    }))
    if (currentTaskId && !options.some((item) => item.value === currentTaskId)) {
      options.unshift({
        label: `${currentTaskId}（当前值，蒲公英中未找到）`,
        value: currentTaskId,
        task_name: form.value.task_name,
        product_name: form.value.product_name,
        product_category: form.value.product_category,
      })
    }
    taskIdOptions.value = options
  } finally {
    taskIdOptionsLoading.value = false
  }
}

async function handleFormProjectChange(projectId) {
  form.value.task_id = ''
  form.value.task_name = ''
  form.value.product_name = ''
  form.value.product_category = ''
  form.value.blogger_type = ''
  await Promise.all([loadPgyTaskOptions(projectId), loadMappingOptions(projectId)])
}

function handleTaskIdChange(taskId) {
  const selected = taskIdOptions.value.find((item) => item.value === taskId)
  if (!selected) {
    return
  }
  if (!form.value.task_name && selected.task_name) {
    form.value.task_name = selected.task_name
  }
  if (!form.value.product_name && selected.product_name) {
    form.value.product_name = selected.product_name
  }
  if (!form.value.product_category && selected.product_category) {
    form.value.product_category = selected.product_category
  }
}

async function openCreate() {
  form.value = { ...getDefaultForm(), project_id: queryItems.value.project_id || null }
  modalTitle.value = '新建任务组'
  modalVisible.value = true
  await Promise.all([loadPgyTaskOptions(form.value.project_id), loadMappingOptions(form.value.project_id)])
}

async function openEdit(row) {
  form.value = {
    id: row.id,
    project_id: row.project_id,
    order_id: row.order_id,
    task_id: row.task_id,
    task_name: row.task_name,
    task_type: row.task_type,
    product_name: row.product_name,
    product_category: row.product_category,
    blogger_type: row.blogger_type,
    cooperation_mode: row.cooperation_mode,
    status: row.status || 'active',
  }
  modalTitle.value = '编辑任务组'
  modalVisible.value = true
  await Promise.all([loadPgyTaskOptions(row.project_id, row.task_id), loadMappingOptions(row.project_id, row)])
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (form.value.id) {
      await api.updateRedbookTaskMapping(form.value)
    } else {
      await api.createRedbookTaskMapping(form.value)
    }
    window.$message?.success('保存成功')
    modalVisible.value = false
    $table.value?.handleSearch()
  } finally {
    saving.value = false
  }
}

async function handleDelete(id) {
  await api.deleteRedbookTaskMapping({ id })
  window.$message?.success('删除成功')
  $table.value?.handleSearch()
}
</script>

<template>
  <CommonPage show-footer title="任务列表">
    <template #action>
      <NButton type="primary" @click="openCreate">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建任务组
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getRedbookTaskMappings"
      :scroll-x="1350"
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
        <QueryBarItem label="关键字" :label-width="60">
          <NInput
            v-model:value="queryItems.keyword"
            clearable
            placeholder="订单 ID/任务名称/任务类型"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <NModal v-model:show="modalVisible" preset="card" :title="modalTitle" class="max-w-860">
      <NForm ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="90">
        <NGrid :cols="2" :x-gap="16">
          <NFormItemGi label="项目" path="project_id">
            <NSelect
              v-model:value="form.project_id"
              filterable
              :options="projectOptions"
              @update:value="handleFormProjectChange"
            />
          </NFormItemGi>
          <NFormItemGi label="订单 ID" path="order_id">
            <NInput v-model:value="form.order_id" />
          </NFormItemGi>
          <NFormItemGi label="任务 ID" path="task_id">
            <NSelect
              v-model:value="form.task_id"
              filterable
              clearable
              :loading="taskIdOptionsLoading"
              :options="taskIdOptions"
              placeholder="请选择蒲公英任务 ID"
              @update:value="handleTaskIdChange"
            />
          </NFormItemGi>
          <NFormItemGi label="任务名称" path="task_name">
            <NInput v-model:value="form.task_name" />
          </NFormItemGi>
          <NFormItemGi label="任务类型" path="task_type">
            <NInput v-model:value="form.task_type" />
          </NFormItemGi>
          <NFormItemGi label="合作模式" path="cooperation_mode">
            <NInput v-model:value="form.cooperation_mode" />
          </NFormItemGi>
          <NFormItemGi label="产品" path="product_name">
            <NInput v-model:value="form.product_name" />
          </NFormItemGi>
          <NFormItemGi label="产品分类" path="product_category">
            <NSelect
              v-model:value="form.product_category"
              filterable
              clearable
              tag
              :loading="mappingOptionsLoading"
              :options="mappingOptions.product_category"
              placeholder="请选择蒲公英SPU"
            />
          </NFormItemGi>
          <NFormItemGi label="达人分类" path="blogger_type">
            <NSelect
              v-model:value="form.blogger_type"
              filterable
              clearable
              tag
              :loading="mappingOptionsLoading"
              :options="mappingOptions.blogger_type"
              placeholder="请选择达人分类"
            />
          </NFormItemGi>
          <NFormItemGi label="状态" path="status">
            <NSelect
              v-model:value="form.status"
              :options="[
                { label: '启用', value: 'active' },
                { label: '停用', value: 'inactive' },
              ]"
            />
          </NFormItemGi>
        </NGrid>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="modalVisible = false">取消</NButton>
          <NButton type="primary" :loading="saving" @click="handleSave">保存</NButton>
        </NSpace>
      </template>
    </NModal>
  </CommonPage>
</template>
