<script setup>
import { h, onMounted, ref } from 'vue'
import { NButton, NSpace, NTag } from 'naive-ui'

import api from '@/api'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import { renderIcon } from '@/utils'
import {
  parseStatusMap,
  parseStatusOptions,
  sourceTypeMap,
  sourceTypeOptions,
  statusTypeMap,
} from '../constants'

defineOptions({ name: 'RedbookParseRecord' })

const $table = ref(null)
const queryItems = ref({})
const projectOptions = ref([])
const reportVisible = ref(false)
const unmatchedVisible = ref(false)
const report = ref({})
const unmatched = ref({ title: '', data: [] })

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
    title: '状态',
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
  { title: '数据行', key: 'data_rows', width: 90 },
  { title: '成功行', key: 'success_rows', width: 90 },
  { title: '失败行', key: 'failed_rows', width: 90 },
  { title: '警告数', key: 'warning_count', width: 90 },
  { title: '解析时间', key: 'parsed_at', width: 170, ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 260,
    fixed: 'right',
    render(row) {
      const actions = [
        h(
          NButton,
          { size: 'small', onClick: () => openReport(row) },
          { default: () => '报告', icon: renderIcon('material-symbols:article-outline', { size: 16 }) }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'primary',
            disabled: row.parsing,
            loading: row.parsing,
            onClick: () => handleReparse(row),
          },
          { default: () => '重解析', icon: renderIcon('material-symbols:refresh', { size: 16 }) }
        ),
        row.source_type === 'juguang' &&
          h(
            NButton,
            {
              size: 'small',
              type: row.unmatched_note_count > 0 ? 'warning' : 'success',
              onClick: () => openUnmatchedNotes(row),
            },
            {
              default: () =>
                row.unmatched_note_count > 0 ? `未匹配笔记(${row.unmatched_note_count})` : '笔记已匹配',
            }
          ),
        row.source_type === 'xiaohongxing_order' &&
          h(
            NButton,
            {
              size: 'small',
              type: row.unmatched_order_count > 0 ? 'warning' : 'success',
              onClick: () => openUnmatchedOrders(row),
            },
            {
              default: () =>
                row.unmatched_order_count > 0 ? `未匹配订单(${row.unmatched_order_count})` : '订单已匹配',
            }
          ),
      ].filter(Boolean)
      return h(NSpace, { size: 8 }, () => actions)
    },
  },
]

const errorColumns = [
  { title: '行号', key: 'row_number', width: 80 },
  { title: '字段', key: 'column_name', width: 140, ellipsis: { tooltip: true } },
  { title: '级别', key: 'error_level', width: 90 },
  { title: '错误码', key: 'error_code', width: 150, ellipsis: { tooltip: true } },
  { title: '说明', key: 'error_message', width: 240, ellipsis: { tooltip: true } },
  { title: '原始值', key: 'raw_value', width: 180, ellipsis: { tooltip: true } },
]

onMounted(async () => {
  await loadProjects()
  $table.value?.handleSearch()
})

async function loadProjects() {
  const res = await api.getRedbookProjects({ page: 1, page_size: 9999 })
  projectOptions.value = res.data.map((item) => ({
    label: `${item.project_name}（${item.project_code}）`,
    value: item.id,
  }))
}

async function openReport(row) {
  const res = await api.getRedbookParseReport({ file_id: row.id })
  report.value = res.data
  reportVisible.value = true
}

async function handleReparse(row) {
  row.parsing = true
  try {
    await api.reparseRedbookFile({ file_id: row.id })
    window.$message?.success('重解析完成')
    $table.value?.handleSearch()
  } finally {
    row.parsing = false
  }
}

async function openUnmatchedNotes(row) {
  const res = await api.getRedbookUnmatchedNotes({ file_id: row.id })
  unmatched.value = { title: '未匹配笔记 ID', data: res.data.note_ids || [] }
  unmatchedVisible.value = true
}

async function openUnmatchedOrders(row) {
  const res = await api.getRedbookUnmatchedOrders({ file_id: row.id })
  unmatched.value = { title: '未匹配订单 ID', data: res.data.order_ids || [] }
  unmatchedVisible.value = true
}
</script>

<template>
  <CommonPage show-footer title="红书解析记录">
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getRedbookFiles"
      :scroll-x="1440"
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

    <NModal v-model:show="reportVisible" preset="card" title="解析报告" class="max-w-920">
      <NDescriptions bordered :column="4" size="small" class="mb-16">
        <NDescriptionsItem label="总行数">{{ report.total_rows || 0 }}</NDescriptionsItem>
        <NDescriptionsItem label="数据行">{{ report.data_rows || 0 }}</NDescriptionsItem>
        <NDescriptionsItem label="成功行">{{ report.success_rows || 0 }}</NDescriptionsItem>
        <NDescriptionsItem label="失败行">{{ report.failed_rows || 0 }}</NDescriptionsItem>
      </NDescriptions>
      <NDataTable
        :columns="errorColumns"
        :data="report.errors || []"
        :pagination="{ pageSize: 10 }"
        :scroll-x="880"
      />
    </NModal>

    <NModal v-model:show="unmatchedVisible" preset="card" :title="unmatched.title" class="max-w-720">
      <NAlert type="warning" class="mb-16">共 {{ unmatched.data.length }} 个未匹配 ID</NAlert>
      <NInput
        type="textarea"
        readonly
        :autosize="{ minRows: 8, maxRows: 16 }"
        :value="unmatched.data.join('\n')"
      />
    </NModal>
  </CommonPage>
</template>
