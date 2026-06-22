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

defineOptions({ name: 'RedbookNoteMapping' })

const $table = ref(null)
const formRef = ref(null)
const queryItems = ref({})
const projectOptions = ref([])
const modalVisible = ref(false)
const modalTitle = ref('')
const saving = ref(false)
const form = ref(getDefaultForm())

const rules = {
  project_id: [{ required: true, type: 'number', message: '请选择项目', trigger: ['change'] }],
  note_id: [{ required: true, message: '请输入 note_id', trigger: ['blur', 'input'] }],
}

const columns = [
  { title: 'note_id', key: 'note_id', width: 170, ellipsis: { tooltip: true } },
  { title: '达人', key: 'blogger_name', width: 130, ellipsis: { tooltip: true } },
  { title: '达人分类', key: 'blogger_type', width: 110, ellipsis: { tooltip: true } },
  { title: '笔记类型', key: 'note_type', width: 110, ellipsis: { tooltip: true } },
  { title: '产品', key: 'product_name', width: 120, ellipsis: { tooltip: true } },
  { title: '产品分类', key: 'product_category', width: 120, ellipsis: { tooltip: true } },
  { title: '内容方向', key: 'content_direction', width: 150, ellipsis: { tooltip: true } },
  { title: '发布日期', key: 'publish_date', width: 110 },
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
            default: () => '确认删除该映射吗？',
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
    note_id: '',
    blogger_name: '',
    blogger_type: '',
    note_type: '',
    product_name: '',
    product_category: '',
    content_direction: '',
    note_url: '',
    publish_date: null,
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

function openCreate() {
  form.value = { ...getDefaultForm(), project_id: queryItems.value.project_id || null }
  modalTitle.value = '新建笔记映射'
  modalVisible.value = true
}

function openEdit(row) {
  form.value = {
    id: row.id,
    project_id: row.project_id,
    note_id: row.note_id,
    blogger_name: row.blogger_name,
    blogger_type: row.blogger_type,
    note_type: row.note_type,
    product_name: row.product_name,
    product_category: row.product_category,
    content_direction: row.content_direction,
    note_url: row.note_url,
    publish_date: row.publish_date,
    status: row.status || 'active',
  }
  modalTitle.value = '编辑笔记映射'
  modalVisible.value = true
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (form.value.id) {
      await api.updateRedbookNoteMapping(form.value)
    } else {
      await api.createRedbookNoteMapping(form.value)
    }
    window.$message?.success('保存成功')
    modalVisible.value = false
    $table.value?.handleSearch()
  } finally {
    saving.value = false
  }
}

async function handleDelete(id) {
  await api.deleteRedbookNoteMapping({ id })
  window.$message?.success('删除成功')
  $table.value?.handleSearch()
}
</script>

<template>
  <CommonPage show-footer title="笔记映射">
    <template #action>
      <NButton type="primary" @click="openCreate">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建映射
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getRedbookNoteMappings"
      :scroll-x="1300"
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
            placeholder="note_id/达人/内容方向"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <NModal v-model:show="modalVisible" preset="card" :title="modalTitle" class="max-w-860">
      <NForm ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="90">
        <NGrid :cols="2" :x-gap="16">
          <NFormItemGi label="项目" path="project_id">
            <NSelect v-model:value="form.project_id" filterable :options="projectOptions" />
          </NFormItemGi>
          <NFormItemGi label="note_id" path="note_id">
            <NInput v-model:value="form.note_id" placeholder="笔记 ID" />
          </NFormItemGi>
          <NFormItemGi label="达人" path="blogger_name">
            <NInput v-model:value="form.blogger_name" />
          </NFormItemGi>
          <NFormItemGi label="达人分类" path="blogger_type">
            <NInput v-model:value="form.blogger_type" />
          </NFormItemGi>
          <NFormItemGi label="笔记类型" path="note_type">
            <NInput v-model:value="form.note_type" />
          </NFormItemGi>
          <NFormItemGi label="发布日期" path="publish_date">
            <NDatePicker v-model:formatted-value="form.publish_date" type="date" value-format="yyyy-MM-dd" clearable />
          </NFormItemGi>
          <NFormItemGi label="产品" path="product_name">
            <NInput v-model:value="form.product_name" />
          </NFormItemGi>
          <NFormItemGi label="产品分类" path="product_category">
            <NInput v-model:value="form.product_category" />
          </NFormItemGi>
          <NFormItemGi label="内容方向" path="content_direction">
            <NInput v-model:value="form.content_direction" />
          </NFormItemGi>
          <NFormItemGi label="笔记链接" path="note_url">
            <NInput v-model:value="form.note_url" />
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
