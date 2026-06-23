<script setup>
import { computed, h, onMounted, ref } from 'vue'
import { NButton, NPopconfirm, NSwitch, NTag } from 'naive-ui'

import api from '@/api'
import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import { renderIcon } from '@/utils'
import { formatNumber, projectStatusOptions, statusTypeMap } from '../constants'

defineOptions({ name: 'RedbookKpiConfig' })

const $table = ref(null)
const formRef = ref(null)
const queryItems = ref({})
const projectOptions = ref([])
const metrics = ref([])
const modalVisible = ref(false)
const modalTitle = ref('')
const saving = ref(false)
const form = ref(getDefaultForm())

const directionOptions = [
  { label: '越高越好', value: 'higher_better' },
  { label: '越低越好', value: 'lower_better' },
]

const costScopeOptions = [
  { label: '不含服务费', value: 'exclude_service_fee' },
  { label: '含服务费', value: 'include_service_fee' },
]

const rules = {
  project_id: [{ required: true, type: 'number', message: '请选择项目', trigger: ['change'] }],
  period_name: [{ required: true, message: '请输入周期', trigger: ['blur', 'input'] }],
  metric_code: [{ required: true, message: '请选择KPI指标', trigger: ['change'] }],
  kpi_name: [{ required: true, message: '请输入KPI名称', trigger: ['blur', 'input'] }],
}

const directionMap = directionOptions.reduce((map, item) => {
  map[item.value] = item.label
  return map
}, {})

const costScopeMap = costScopeOptions.reduce((map, item) => {
  map[item.value] = item.label
  return map
}, {})

const metricSelectOptions = computed(() =>
  metrics.value.map((item) => ({
    label: `${item.category} / ${item.label}`,
    value: item.code,
  }))
)

const columns = [
  { title: 'KPI名称', key: 'kpi_name', width: 160, ellipsis: { tooltip: true } },
  { title: '周期', key: 'period_name', width: 110, ellipsis: { tooltip: true } },
  {
    title: '系统指标',
    key: 'metric_label',
    width: 160,
    render(row) {
      return h(
        'div',
        { class: 'metric-cell' },
        [
          h('strong', row.metric_label || row.metric_code),
          h('span', row.metric_code),
        ]
      )
    },
  },
  { title: '分类', key: 'category', width: 110 },
  { title: '来源', key: 'source', width: 120 },
  {
    title: '目标值',
    key: 'target_value',
    width: 120,
    render(row) {
      return formatKpiValue(row.target_value, row.unit)
    },
  },
  {
    title: '权重',
    key: 'weight_score',
    width: 90,
    render(row) {
      return formatNumber(row.weight_score, 2)
    },
  },
  {
    title: '方向',
    key: 'direction',
    width: 100,
    render(row) {
      return directionMap[row.direction] || row.direction
    },
  },
  {
    title: '封顶',
    key: 'cap_at_full_score',
    width: 80,
    render(row) {
      return h(NTag, { size: 'small', type: row.cap_at_full_score ? 'success' : 'warning' }, { default: () => (row.cap_at_full_score ? '是' : '否') })
    },
  },
  {
    title: '费用口径',
    key: 'cost_scope',
    width: 110,
    render(row) {
      return costScopeMap[row.cost_scope] || row.cost_scope || '-'
    },
  },
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
            default: () => '确认删除该KPI配置吗？',
          }
        ),
      ]
    },
  },
]

onMounted(async () => {
  await Promise.all([loadProjects(), loadMetrics()])
  $table.value?.handleSearch()
})

function getDefaultForm() {
  return {
    project_id: null,
    period_name: '',
    metric_code: null,
    kpi_name: '',
    target_value: null,
    weight_score: 10,
    unit: '',
    direction: 'higher_better',
    cap_at_full_score: true,
    cost_scope: 'exclude_service_fee',
    status: 'active',
    remark: '',
  }
}

async function loadProjects() {
  const res = await api.getRedbookProjects({ page: 1, page_size: 9999 })
  projectOptions.value = (res.data || []).map((item) => ({
    label: `${item.project_name} (${item.project_code})`,
    value: item.id,
    period_name: item.project_period,
  }))
}

async function loadMetrics() {
  const res = await api.getRedbookKpiMetrics()
  metrics.value = res.data || []
}

function metricMeta(metricCode) {
  return metrics.value.find((item) => item.code === metricCode) || null
}

function projectPeriod(projectId) {
  return projectOptions.value.find((item) => item.value === projectId)?.period_name || '默认周期'
}

function applyProjectPeriod() {
  if (!form.value.project_id) return
  if (!form.value.period_name) form.value.period_name = projectPeriod(form.value.project_id)
}

function applyMetricDefaults(force = false) {
  const metric = metricMeta(form.value.metric_code)
  if (!metric) return
  if (force || !form.value.kpi_name) form.value.kpi_name = metric.label
  if (force || !form.value.unit) form.value.unit = metric.unit || ''
  if (force || !form.value.direction) form.value.direction = metric.default_direction || 'higher_better'
  if (force || !form.value.cost_scope) form.value.cost_scope = metric.default_cost_scope || 'exclude_service_fee'
}

function handleProjectChange() {
  form.value.period_name = projectPeriod(form.value.project_id)
}

function handleMetricChange() {
  applyMetricDefaults(true)
}

function openCreate() {
  form.value = { ...getDefaultForm(), project_id: queryItems.value.project_id || null }
  applyProjectPeriod()
  modalTitle.value = '新建KPI'
  modalVisible.value = true
}

function openEdit(row) {
  form.value = {
    id: row.id,
    project_id: row.project_id,
    period_name: row.period_name || '',
    metric_code: row.metric_code,
    kpi_name: row.kpi_name,
    target_value: Number(row.target_value ?? 0) || null,
    weight_score: Number(row.weight_score ?? 0),
    unit: row.unit || '',
    direction: row.direction || 'higher_better',
    cap_at_full_score: row.cap_at_full_score !== false,
    cost_scope: row.cost_scope || 'exclude_service_fee',
    status: row.status || 'active',
    remark: row.remark || '',
  }
  modalTitle.value = '编辑KPI'
  modalVisible.value = true
}

function normalizePayload() {
  return {
    ...form.value,
    target_value: form.value.target_value === '' ? null : form.value.target_value,
    weight_score: form.value.weight_score === '' || form.value.weight_score === null ? 0 : form.value.weight_score,
  }
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    const payload = normalizePayload()
    if (payload.id) {
      await api.updateRedbookKpiConfig(payload)
    } else {
      await api.createRedbookKpiConfig(payload)
    }
    window.$message?.success('保存成功')
    modalVisible.value = false
    $table.value?.handleSearch()
  } finally {
    saving.value = false
  }
}

async function handleDelete(id) {
  await api.deleteRedbookKpiConfig({ id })
  window.$message?.success('删除成功')
  $table.value?.handleSearch()
}

function formatKpiValue(value, unit = '') {
  if (value === null || value === undefined || value === '') return '-'
  if (unit === '%') return `${formatNumber(Number(value) * 100, 2)}%`
  if (unit === '元') return `¥${formatNumber(value, 2)}`
  return `${formatNumber(value, 2)}${unit ? ` ${unit}` : ''}`
}
</script>

<template>
  <CommonPage show-footer title="KPI配置">
    <template #action>
      <NButton type="primary" @click="openCreate">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建KPI
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getRedbookKpiConfigs"
      :scroll-x="1500"
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
        <QueryBarItem label="周期" :label-width="50">
          <NInput v-model:value="queryItems.period_name" clearable placeholder="如 2026Q1" />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="50">
          <NSelect v-model:value="queryItems.status" clearable :options="projectStatusOptions" placeholder="全部" />
        </QueryBarItem>
        <QueryBarItem label="关键字" :label-width="60">
          <NInput
            v-model:value="queryItems.keyword"
            clearable
            placeholder="KPI名称/指标编码"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <NModal v-model:show="modalVisible" preset="card" :title="modalTitle" class="max-w-860">
      <NForm ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="100">
        <NGrid :cols="2" :x-gap="16">
          <NFormItemGi label="项目" path="project_id">
            <NSelect v-model:value="form.project_id" filterable :options="projectOptions" @update:value="handleProjectChange" />
          </NFormItemGi>
          <NFormItemGi label="周期" path="period_name">
            <NInput v-model:value="form.period_name" placeholder="默认取项目周期" />
          </NFormItemGi>
          <NFormItemGi label="系统指标" path="metric_code">
            <NSelect v-model:value="form.metric_code" filterable :options="metricSelectOptions" @update:value="handleMetricChange" />
          </NFormItemGi>
          <NFormItemGi label="KPI名称" path="kpi_name">
            <NInput v-model:value="form.kpi_name" placeholder="可按业务名称微调" />
          </NFormItemGi>
          <NFormItemGi label="目标值" path="target_value">
            <NInputNumber v-model:value="form.target_value" clearable :precision="6" placeholder="百分比填小数，如 0.15" />
          </NFormItemGi>
          <NFormItemGi label="权重分" path="weight_score">
            <NInputNumber v-model:value="form.weight_score" :min="0" :precision="2" />
          </NFormItemGi>
          <NFormItemGi label="单位" path="unit">
            <NInput v-model:value="form.unit" placeholder="系统自动带出，可微调" />
          </NFormItemGi>
          <NFormItemGi label="方向" path="direction">
            <NSelect v-model:value="form.direction" :options="directionOptions" />
          </NFormItemGi>
          <NFormItemGi label="费用口径" path="cost_scope">
            <NSelect v-model:value="form.cost_scope" :options="costScopeOptions" />
          </NFormItemGi>
          <NFormItemGi label="状态" path="status">
            <NSelect v-model:value="form.status" :options="projectStatusOptions" />
          </NFormItemGi>
          <NFormItemGi label="是否封顶" path="cap_at_full_score">
            <NSwitch v-model:value="form.cap_at_full_score" />
          </NFormItemGi>
          <NFormItemGi label="备注" path="remark">
            <NInput v-model:value="form.remark" type="textarea" placeholder="可记录目标依据或业务说明" />
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

<style scoped>
.metric-cell {
  display: grid;
  gap: 2px;
}

.metric-cell strong {
  font-weight: 600;
}

.metric-cell span {
  color: var(--n-text-color-3);
  font-size: 12px;
}
</style>
