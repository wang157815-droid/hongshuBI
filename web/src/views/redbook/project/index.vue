<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NPopconfirm, NTag } from 'naive-ui'

import api from '@/api'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import { renderIcon } from '@/utils'
import { projectStatusOptions, statusTypeMap } from '../constants'

defineOptions({ name: 'RedbookProject' })

const $table = ref(null)
const formRef = ref(null)
const queryItems = ref({})
const modalVisible = ref(false)
const modalTitle = ref('')
const saving = ref(false)
const form = ref(getDefaultForm())

const rules = {
  project_code: [{ required: true, message: '请输入项目编码', trigger: ['blur', 'input'] }],
  project_name: [{ required: true, message: '请输入项目名称', trigger: ['blur', 'input'] }],
}

const columns = [
  { title: '项目编码', key: 'project_code', width: 130, ellipsis: { tooltip: true } },
  { title: '项目名称', key: 'project_name', width: 180, ellipsis: { tooltip: true } },
  { title: '品牌', key: 'brand_name', width: 120, ellipsis: { tooltip: true } },
  { title: '项目周期', key: 'project_period', width: 130, ellipsis: { tooltip: true } },
  { title: '开始日期', key: 'start_date', width: 110 },
  { title: '结束日期', key: 'end_date', width: 110 },
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
            default: () => '确认删除该项目吗？',
          }
        ),
      ]
    },
  },
]

onMounted(() => {
  $table.value?.handleSearch()
})

function getDefaultForm() {
  return {
    project_code: '',
    project_name: '',
    brand_name: '',
    project_period: '',
    start_date: null,
    end_date: null,
    status: 'active',
    remark: '',
  }
}

function openCreate() {
  form.value = getDefaultForm()
  modalTitle.value = '新建红书项目'
  modalVisible.value = true
}

function openEdit(row) {
  form.value = {
    id: row.id,
    project_code: row.project_code,
    project_name: row.project_name,
    brand_name: row.brand_name,
    project_period: row.project_period,
    start_date: row.start_date,
    end_date: row.end_date,
    status: row.status || 'active',
    remark: row.remark,
  }
  modalTitle.value = '编辑红书项目'
  modalVisible.value = true
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (form.value.id) {
      await api.updateRedbookProject(form.value)
    } else {
      await api.createRedbookProject(form.value)
    }
    window.$message?.success('保存成功')
    modalVisible.value = false
    $table.value?.handleSearch()
  } finally {
    saving.value = false
  }
}

async function handleDelete(projectId) {
  await api.deleteRedbookProject({ project_id: projectId })
  window.$message?.success('删除成功')
  $table.value?.handleSearch()
}
</script>

<template>
  <CommonPage show-footer title="红书项目">
    <template #action>
      <NButton type="primary" @click="openCreate">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建项目
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getRedbookProjects"
      :scroll-x="950"
    >
      <template #queryBar>
        <QueryBarItem label="关键字" :label-width="60">
          <NInput
            v-model:value="queryItems.keyword"
            clearable
            placeholder="项目编码/名称/品牌"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="50">
          <NSelect
            v-model:value="queryItems.status"
            clearable
            :options="projectStatusOptions"
            placeholder="全部"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <NModal v-model:show="modalVisible" preset="card" :title="modalTitle" class="max-w-720">
      <NForm ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="90">
        <NGrid :cols="2" :x-gap="16">
          <NFormItemGi label="项目编码" path="project_code">
            <NInput v-model:value="form.project_code" placeholder="如 MANLA-2026Q2" />
          </NFormItemGi>
          <NFormItemGi label="项目名称" path="project_name">
            <NInput v-model:value="form.project_name" placeholder="如 缦拉2026Q2种草投流" />
          </NFormItemGi>
          <NFormItemGi label="品牌" path="brand_name">
            <NInput v-model:value="form.brand_name" placeholder="品牌名称" />
          </NFormItemGi>
          <NFormItemGi label="周期" path="project_period">
            <NInput v-model:value="form.project_period" placeholder="如 2026Q2" />
          </NFormItemGi>
          <NFormItemGi label="开始日期" path="start_date">
            <NDatePicker v-model:formatted-value="form.start_date" type="date" value-format="yyyy-MM-dd" clearable />
          </NFormItemGi>
          <NFormItemGi label="结束日期" path="end_date">
            <NDatePicker v-model:formatted-value="form.end_date" type="date" value-format="yyyy-MM-dd" clearable />
          </NFormItemGi>
          <NFormItemGi label="状态" path="status">
            <NSelect v-model:value="form.status" :options="projectStatusOptions" />
          </NFormItemGi>
          <NFormItemGi label="备注" path="remark">
            <NInput v-model:value="form.remark" placeholder="可选" />
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
