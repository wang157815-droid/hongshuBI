<script setup>
import { computed, h, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { NButton, NTag } from 'naive-ui'

import api from '@/api'
import CommonPage from '@/components/page/CommonPage.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import { formatMoney, formatNumber } from '../../constants'

defineOptions({ name: 'RedbookDashboardOverview' })

const DASHBOARD_FILTER_STORAGE_KEY = 'redbook-dashboard-overview-filters'
const DASHBOARD_TABS = new Set(['keyword-search', 'xiaohongxing', 'planting', 'kpi', 'combined'])
let restoringDashboardFilters = false

const activeTab = ref('combined')
const projectOptions = ref([])
const projectId = ref(null)
const productOptions = ref([])
const productCategories = ref([])
const productLoading = ref(false)
const taskGroupOptions = ref([])
const taskGroupId = ref(null)
const taskGroupLoading = ref(false)
const dateRange = ref(null)
const loading = ref(false)
const rebuilding = ref(false)
const totals = ref({})
const xiaohongxing = ref(defaultXiaohongxing())
const keywordSearch = ref(defaultKeywordSearch())
const planting = ref(defaultPlanting())
const kpiProgress = ref(defaultKpiProgress())
const plantingCostGranularity = ref('day')
const adEfficiencyTab = ref('cost-trend')
const adVolumeMode = ref('clicks')
const overviewTrendMode = ref('search')
const keywordSelectionReady = ref(false)
const keywordFilters = ref({
  selected_keywords: [],
  keyword: '',
})
const plantingFilters = ref({
  product_category: null,
  blogger_type: null,
  note_type: null,
  content_direction: null,
  keyword: '',
})

const xhxTaskSumFields = [
  'order_count',
  'read_play_uv',
  'like_uv',
  'collect_uv',
  'comment_uv',
  'share_uv',
  'interaction_uv',
  'search_exposure_uv',
  'search_visit_uv',
  'shop_visit_uv',
  'product_collect_uv',
  'product_cart_uv',
  'shop_follow_uv',
  'shop_member_uv',
  'new_customer_visit_uv',
  'new_customer_deal_uv',
  'deal_uv',
  'merchant_gmv',
  'order_product_gmv',
  'order_product_new_customer_gmv',
  'non_order_product_gmv',
  'collect_cart_uv',
  'total_cost',
  'note_fee',
  'ad_cost',
  'note_count',
  'content_exposure',
]

const xhxDailySumFields = [
  'read_play_uv',
  'like_uv',
  'collect_uv',
  'comment_uv',
  'share_uv',
  'interaction_uv',
  'search_exposure_uv',
  'search_visit_uv',
  'shop_visit_uv',
  'new_customer_visit_uv',
  'product_collect_uv',
  'product_cart_uv',
  'shop_follow_uv',
  'shop_member_uv',
  'deal_uv',
  'merchant_gmv',
  'order_product_gmv',
  'order_product_new_customer_gmv',
  'non_order_product_gmv',
  'new_customer_deal_uv',
  'total_cost',
  'note_fee',
  'ad_cost',
  'content_exposure',
]

const xhxSummary = computed(() => xiaohongxing.value.summary || {})
const xhxCards = computed(() => [
  { label: '阅读/播放 UV', value: formatNumber(xhxSummary.value.read_play_uv), sub: `互动率 ${formatPercent(xhxSummary.value.interaction_rate, 2)}` },
  { label: '互动 UV', value: formatNumber(xhxSummary.value.interaction_uv), sub: `赞藏评转 ${formatNumber(toNumber(xhxSummary.value.like_uv) + toNumber(xhxSummary.value.collect_uv) + toNumber(xhxSummary.value.comment_uv) + toNumber(xhxSummary.value.share_uv))}` },
  { label: '搜索曝光 UV', value: formatNumber(xhxSummary.value.search_exposure_uv), sub: `搜索进店 ${formatNumber(xhxSummary.value.search_visit_uv)}` },
  { label: '进店 UV', value: formatNumber(xhxSummary.value.shop_visit_uv), sub: `收藏/加购 ${formatNumber(xhxSummary.value.collect_cart_uv)}` },
  { label: 'GMV', value: formatMoney(xhxSummary.value.merchant_gmv), sub: `成交UV ${formatNumber(xhxSummary.value.deal_uv)}` },
  { label: 'ROI', value: formatNumber(xhxSummary.value.roi, 4), sub: `UV价值 ${formatMoney(xhxSummary.value.gmv_per_read_uv)}` },
  { label: '聚光搜索组件', value: formatNumber(xhxSummary.value.search_component_clicks), sub: `成本 ${formatMoney(xhxSummary.value.search_component_cost)}` },
  { label: '新客成交 GMV', value: formatMoney(xhxSummary.value.order_product_new_customer_gmv), sub: `新客成交UV ${formatNumber(xhxSummary.value.new_customer_deal_uv)}` },
])

const xhxSearchTrend = computed(() => xiaohongxing.value.search_trend || [])
const xhxGmvTrend = computed(() => xiaohongxing.value.gmv_trend || [])
const xhxDailyRows = computed(() => xiaohongxing.value.daily_rows || [])
const xhxDailyRowsWithTotal = computed(() => {
  const rows = xhxDailyRows.value || []
  if (!rows.length) return []
  return [buildDailyTotalRow(rows), ...rows]
})
const xhxTaskGroups = computed(() => xiaohongxing.value.task_groups || [])
const xhxTaskGroupsWithTotal = computed(() => {
  const rows = xhxTaskGroups.value || []
  if (!rows.length) return []
  return [buildTaskGroupTotalRow(rows), ...rows]
})
const xhxDetailGroups = computed(() => buildXhxDetailGroups(xhxSummary.value, xhxTaskGroupsWithTotal.value[0] || {}))
const xhxDetailActiveTab = ref('内容规划')
const xhxSourceStatus = computed(() => xiaohongxing.value.source_status || [])
const selectedProject = computed(() => projectOptions.value.find((item) => item.value === projectId.value) || null)
const kpiCards = computed(() => [
  { label: 'KPI总分', value: kpiProgress.value.total_score === null ? '-' : formatNumber(kpiProgress.value.total_score, 2), sub: `可得权重 ${formatNumber(kpiProgress.value.total_weight, 2)}` },
  { label: '配置项', value: formatNumber(kpiProgress.value.configured_count), sub: `周期 ${kpiProgress.value.period_name || selectedProject.value?.period_name || '-'}` },
  { label: '已达标', value: formatNumber(kpiProgress.value.achieved_count), sub: `未达标 ${formatNumber(kpiProgress.value.failed_count)}` },
  { label: '未计分', value: formatNumber(kpiProgress.value.missing_count), sub: '无目标或数据缺失' },
])
const kpiWeakItems = computed(() => kpiProgress.value.weak_items || [])
const xhxMissingMappings = computed(() => xiaohongxing.value.missing_mappings || {})
const xhxSearchMax = computed(() =>
  Math.max(
    ...xhxSearchTrend.value.flatMap((item) => [
      toNumber(item.search_exposure_uv),
      toNumber(item.search_visit_uv),
      toNumber(item.shop_visit_uv),
    ]),
    1
  )
)
const xhxGmvMax = computed(() => Math.max(...xhxGmvTrend.value.map((item) => toNumber(item.merchant_gmv)), 1))

const keywordSummary = computed(() => keywordSearch.value.summary || {})
const keywordTrend = computed(() => keywordSearch.value.trend || [])
const keywordRows = computed(() => keywordSearch.value.keywords || [])
const keywordFilterOptions = computed(() => {
  const filters = keywordSearch.value.filters || {}
  return {
    keyword: toOptions(filters.keyword),
  }
})
const selectedKeywordList = computed(() => keywordSearch.value.filters?.selected_keywords || keywordFilters.value.selected_keywords || [])
const keywordPalette = ['#e11d48', '#f97316', '#0ea5e9', '#7c3aed', '#16a34a', '#2563eb', '#dc2626', '#0891b2']
const keywordTrendChart = computed(() => buildKeywordTrendChart(keywordTrend.value, selectedKeywordList.value))
const keywordCards = computed(() => [
  { label: '已选关键词', value: formatNumber(keywordSummary.value.selected_keyword_count), sub: `可选 ${formatNumber(keywordSummary.value.available_keyword_count)} 个` },
  { label: '已选红搜指数', value: formatNumber(keywordSummary.value.search_index), sub: `日期 ${formatNumber(keywordSummary.value.date_count)} 天` },
  { label: '平均指数', value: formatNumber(keywordSummary.value.avg_search_index, 1), sub: `有效记录 ${formatNumber(keywordSummary.value.known_value_count)}` },
  { label: '<100 记录', value: formatNumber(keywordSummary.value.less_than_threshold_count), sub: '保留原始值，不参与数值汇总' },
])

const plantingCards = computed(() => [
  { label: '总费用', value: formatMoney(planting.value.totals.total_cost), sub: `笔记 ${formatMoney(planting.value.totals.note_fee)} / 投流 ${formatMoney(planting.value.totals.ad_cost)}` },
  { label: '投流消耗', value: formatMoney(planting.value.totals.ad_cost), sub: `服务费 ${formatMoney(planting.value.totals.service_fee)}` },
  { label: '曝光', value: formatNumber(planting.value.totals.impressions), sub: `点击 ${formatNumber(planting.value.totals.clicks)}` },
  { label: '互动', value: formatNumber(planting.value.totals.interactions), sub: `CPE ${formatMoney(planting.value.totals.cpe)}` },
  { label: '搜索组件点击', value: formatNumber(planting.value.totals.search_component_clicks), sub: `成本 ${formatMoney(planting.value.totals.search_component_cost)}` },
  { label: '站外活跃 UV', value: formatNumber(planting.value.totals.offsite_active_uv_30d), sub: `成本 ${formatMoney(planting.value.totals.offsite_active_cost)}` },
  { label: '笔记数', value: formatNumber(planting.value.totals.note_count), sub: `达人 ${formatNumber(planting.value.totals.blogger_count)}` },
  { label: '蒲公英阅读', value: formatNumber(planting.value.totals.pgy_read_count), sub: `互动 ${formatNumber(planting.value.totals.pgy_interaction_count)}` },
])

const adCostMetricDefinitions = [
  { label: 'CPC', key: 'cpc', color: '#0ea5e9', desc: '单次点击成本' },
  { label: 'CPM', key: 'cpm', color: '#2563eb', desc: '千次展现成本' },
  { label: 'CPE', key: 'cpe', color: '#16a34a', desc: '单次互动成本' },
  { label: '搜索组件成本', key: 'search_component_cost', color: '#7c3aed', desc: '单次搜索组件点击成本' },
  { label: '站外活跃成本', key: 'offsite_active_cost', color: '#f97316', desc: '30日归因站外活跃成本' },
]

const adVolumeModes = [
  { label: '点击效率', value: 'clicks', volumeKey: 'clicks', volumeLabel: '点击量', unitCostKey: 'cpc', unitCostLabel: 'CPC', color: '#0ea5e9' },
  { label: '互动效率', value: 'interactions', volumeKey: 'interactions', volumeLabel: '互动量', unitCostKey: 'cpe', unitCostLabel: 'CPE', color: '#16a34a' },
  { label: '搜索组件效率', value: 'search_component', volumeKey: 'search_component_clicks', volumeLabel: '搜索组件点击', unitCostKey: 'search_component_cost', unitCostLabel: '搜索组件成本', color: '#7c3aed' },
]

const overviewTrendModes = [
  { label: '红搜指数', value: 'search', resultKey: 'search_index', resultLabel: '红搜指数', color: '#e11d48', formatter: formatNumber },
  { label: '进店 UV', value: 'shop_visit', resultKey: 'shop_visit_uv', resultLabel: '进店 UV', color: '#16a34a', formatter: formatNumber },
  { label: 'GMV', value: 'gmv', resultKey: 'merchant_gmv', resultLabel: 'GMV', color: '#dc2626', formatter: formatMoney },
]

const plantingFilterOptions = computed(() => {
  const filters = planting.value.filters || {}
  return {
    product_category: toOptions(filters.product_category),
    blogger_type: toOptions(filters.blogger_type),
    note_type: toOptions(filters.note_type),
    content_direction: toOptions(filters.content_direction),
  }
})

const plantingTrend = computed(() => planting.value.trend || [])
const plantingNotes = computed(() => planting.value.notes || [])
const plantingCostTrend = computed(() => aggregateCostTrend(plantingTrend.value, plantingCostGranularity.value))
const plantingCostSummary = computed(() => buildCostTrendSummary(plantingCostTrend.value, plantingCostGranularity.value))
const plantingCostChart = computed(() => buildCostTrendChart(plantingCostTrend.value))
const adCostMetricCharts = computed(() => adCostMetricDefinitions.map((item) => buildAdCostMetricChart(plantingTrend.value, item)))
const activeAdVolumeMode = computed(() => adVolumeModes.find((item) => item.value === adVolumeMode.value) || adVolumeModes[0])
const adVolumeChart = computed(() => buildAdVolumeChart(plantingTrend.value, activeAdVolumeMode.value))
const adVolumeSummary = computed(() => buildAdVolumeSummary(plantingTrend.value, activeAdVolumeMode.value))
const highCostNotes = computed(() => topNotesByMetric(plantingNotes.value, 'ad_cost', 8))
const highCpeNotes = computed(() => topNotesByMetric(plantingNotes.value.filter((row) => toNumber(row.cpe) > 0), 'cpe', 8))
const highCostNoteMax = computed(() => Math.max(...highCostNotes.value.map((row) => toNumber(row.ad_cost)), 1))
const highCpeNoteMax = computed(() => Math.max(...highCpeNotes.value.map((row) => toNumber(row.cpe)), 1))
const overviewCoreCards = computed(() => buildOverviewCoreCards())
const overviewFunnelItems = computed(() => buildOverviewFunnelItems())
const overviewTrendRows = computed(() => buildOverviewTrendRows(plantingTrend.value, keywordTrend.value, xhxDailyRows.value))
const activeOverviewTrendMode = computed(() => overviewTrendModes.find((item) => item.value === overviewTrendMode.value) || overviewTrendModes[0])
const overviewTrendChart = computed(() => buildOverviewTrendChart(overviewTrendRows.value, activeOverviewTrendMode.value))
const overviewTrendSummary = computed(() => buildOverviewTrendSummary(overviewTrendRows.value, activeOverviewTrendMode.value))
const overviewSourceCards = computed(() => buildOverviewSourceCards(xhxSourceStatus.value, xhxMissingMappings.value, keywordSummary.value))
const overviewDiagnostics = computed(() => buildOverviewDiagnostics())
const productMax = computed(() => breakdownMax(planting.value.breakdowns.product_category))
const bloggerMax = computed(() => breakdownMax(planting.value.breakdowns.blogger_type))
const directionMax = computed(() => breakdownMax(planting.value.breakdowns.content_direction))

const dailyColumns = [
  { title: '日期', key: 'stat_date', width: 110 },
  { title: '总费用', key: 'total_cost', width: 120, render: (row) => formatMoney(row.total_cost) },
  { title: '笔记费用', key: 'note_fee', width: 120, render: (row) => formatMoney(row.note_fee) },
  { title: '投流消耗', key: 'ad_cost', width: 120, render: (row) => formatMoney(row.ad_cost) },
  { title: '曝光', key: 'impressions', width: 110, render: (row) => formatNumber(row.impressions) },
  { title: '点击', key: 'clicks', width: 100, render: (row) => formatNumber(row.clicks) },
  { title: '互动', key: 'interactions', width: 100, render: (row) => formatNumber(row.interactions) },
  { title: '搜索组件点击', key: 'search_component_clicks', width: 130, render: (row) => formatNumber(row.search_component_clicks) },
  { title: 'CTR', key: 'ctr', width: 90, render: (row) => formatPercent(row.ctr, 2) },
  { title: 'CPC', key: 'cpc', width: 100, render: (row) => formatMoney(row.cpc) },
  { title: 'CPM', key: 'cpm', width: 100, render: (row) => formatMoney(row.cpm) },
  { title: 'CPE', key: 'cpe', width: 100, render: (row) => formatMoney(row.cpe) },
]

const noteColumns = [
  { title: '笔记 ID', key: 'note_id', width: 190, ellipsis: { tooltip: true } },
  { title: '达人', key: 'blogger_name', width: 120, ellipsis: { tooltip: true } },
  { title: '产品', key: 'product_category', width: 100 },
  { title: '达人类型', key: 'blogger_type', width: 90 },
  { title: '笔记类型', key: 'note_type', width: 90 },
  { title: '内容方向', key: 'content_direction', width: 130, ellipsis: { tooltip: true } },
  { title: '发布时间', key: 'publish_date', width: 110 },
  { title: '总费用', key: 'total_cost', width: 120, render: (row) => formatMoney(row.total_cost) },
  { title: '笔记费用', key: 'note_fee', width: 120, render: (row) => formatMoney(row.note_fee) },
  { title: '投流消耗', key: 'ad_cost', width: 120, render: (row) => formatMoney(row.ad_cost) },
  { title: '曝光', key: 'impressions', width: 110, render: (row) => formatNumber(row.impressions) },
  { title: '点击', key: 'clicks', width: 100, render: (row) => formatNumber(row.clicks) },
  { title: '互动', key: 'interactions', width: 100, render: (row) => formatNumber(row.interactions) },
  { title: '搜索组件点击', key: 'search_component_clicks', width: 130, render: (row) => formatNumber(row.search_component_clicks) },
  { title: 'CPE', key: 'cpe', width: 100, render: (row) => formatMoney(row.cpe) },
  { title: '蒲公英阅读', key: 'pgy_read_count', width: 120, render: (row) => formatNumber(row.pgy_read_count) },
]

const xhxDailyColumns = [
  { title: '日期', key: 'stat_date', width: 110, render: (row) => row.stat_date || '合计' },
  { title: '阅读/播放UV', key: 'read_play_uv', width: 130, render: (row) => formatNumber(row.read_play_uv) },
  { title: '点赞UV', key: 'like_uv', width: 100, render: (row) => formatNumber(row.like_uv) },
  { title: '收藏UV', key: 'collect_uv', width: 100, render: (row) => formatNumber(row.collect_uv) },
  { title: '评论UV', key: 'comment_uv', width: 100, render: (row) => formatNumber(row.comment_uv) },
  { title: '转发UV', key: 'share_uv', width: 100, render: (row) => formatNumber(row.share_uv) },
  { title: '互动UV', key: 'interaction_uv', width: 110, render: (row) => formatNumber(row.interaction_uv) },
  { title: '内容互动率', key: 'interaction_rate', width: 110, render: (row) => formatPercent(row.interaction_rate, 2) },
  { title: '手淘搜索曝光UV', key: 'search_exposure_uv', width: 140, render: (row) => formatNumber(row.search_exposure_uv) },
  { title: '手淘搜索进店UV', key: 'search_visit_uv', width: 140, render: (row) => formatNumber(row.search_visit_uv) },
  { title: '进店UV', key: 'shop_visit_uv', width: 110, render: (row) => formatNumber(row.shop_visit_uv) },
  { title: '引流率', key: 'shop_visit_rate', width: 100, render: (row) => formatPercent(row.shop_visit_rate, 2) },
  { title: '店铺新访客', key: 'new_customer_visit_uv', width: 120, render: (row) => formatNumber(row.new_customer_visit_uv) },
  { title: '店铺新访客率', key: 'new_customer_visit_rate', width: 120, render: (row) => formatPercent(rateValue(row, 'new_customer_visit_rate', 'new_customer_visit_uv', 'shop_visit_uv'), 2) },
  { title: '店铺收藏UV', key: 'product_collect_uv', width: 120, render: (row) => formatNumber(row.product_collect_uv) },
  { title: '加购UV', key: 'product_cart_uv', width: 100, render: (row) => formatNumber(row.product_cart_uv) },
  { title: '收藏加购率', key: 'collect_cart_rate', width: 110, render: (row) => formatPercent(row.collect_cart_rate, 2) },
  { title: '关注店铺UV', key: 'shop_follow_uv', width: 120, render: (row) => formatNumber(row.shop_follow_uv) },
  { title: '店铺会员UV', key: 'shop_member_uv', width: 120, render: (row) => formatNumber(row.shop_member_uv) },
  { title: '全店成交UV', key: 'deal_uv', width: 120, render: (row) => formatNumber(row.deal_uv) },
  { title: '全店成交GMV', key: 'merchant_gmv', width: 130, render: (row) => formatMoney(row.merchant_gmv) },
  { title: '任务商品成交GMV', key: 'order_product_gmv', width: 150, render: (row) => formatMoney(row.order_product_gmv) },
  { title: '任务商品新客成交GMV', key: 'order_product_new_customer_gmv', width: 170, render: (row) => formatMoney(row.order_product_new_customer_gmv) },
  { title: '非任务商品成交GMV', key: 'non_order_product_gmv', width: 160, render: (row) => formatMoney(row.non_order_product_gmv) },
  { title: '转化率', key: 'deal_conversion_rate', width: 100, render: (row) => formatPercent(row.deal_conversion_rate, 2) },
  { title: '店铺新客UV', key: 'new_customer_deal_uv', width: 120, render: (row) => formatNumber(row.new_customer_deal_uv) },
  { title: '店铺新客率', key: 'new_customer_deal_rate', width: 120, render: (row) => formatPercent(rateValue(row, 'new_customer_deal_rate', 'new_customer_deal_uv', 'deal_uv'), 2) },
  { title: '总花费', key: 'total_cost', width: 120, render: (row) => formatMoney(row.total_cost) },
  { title: '笔记费用', key: 'note_fee', width: 120, render: (row) => formatMoney(row.note_fee) },
  { title: '投流费用', key: 'ad_cost', width: 120, render: (row) => formatMoney(row.ad_cost) },
  { title: '内容曝光', key: 'content_exposure', width: 120, render: (row) => formatNumber(row.content_exposure) },
  { title: 'ROI', key: 'roi', width: 100, render: (row) => formatNumber(row.roi, 4) },
]

const xhxTaskColumns = [
  { title: '任务ID', key: 'task_id', width: 160, ellipsis: { tooltip: true }, render: (row) => row.task_id || '未归类' },
  { title: '任务名称', key: 'task_name', width: 180, ellipsis: { tooltip: true } },
  { title: '订单数', key: 'order_count', width: 90, render: (row) => formatNumber(row.order_count) },
  { title: '阅读/播放UV', key: 'read_play_uv', width: 130, render: (row) => formatNumber(row.read_play_uv) },
  { title: '点赞UV', key: 'like_uv', width: 100, render: (row) => formatNumber(row.like_uv) },
  { title: '收藏UV', key: 'collect_uv', width: 100, render: (row) => formatNumber(row.collect_uv) },
  { title: '评论UV', key: 'comment_uv', width: 100, render: (row) => formatNumber(row.comment_uv) },
  { title: '转发UV', key: 'share_uv', width: 100, render: (row) => formatNumber(row.share_uv) },
  { title: '互动UV', key: 'interaction_uv', width: 110, render: (row) => formatNumber(row.interaction_uv) },
  { title: '手淘搜索曝光UV', key: 'search_exposure_uv', width: 140, render: (row) => formatNumber(row.search_exposure_uv) },
  { title: '手淘搜索进店UV', key: 'search_visit_uv', width: 140, render: (row) => formatNumber(row.search_visit_uv) },
  { title: '进店UV', key: 'shop_visit_uv', width: 100, render: (row) => formatNumber(row.shop_visit_uv) },
  { title: '店铺收藏UV', key: 'product_collect_uv', width: 120, render: (row) => formatNumber(row.product_collect_uv) },
  { title: '加购UV', key: 'product_cart_uv', width: 100, render: (row) => formatNumber(row.product_cart_uv) },
  { title: '关注店铺UV', key: 'shop_follow_uv', width: 120, render: (row) => formatNumber(row.shop_follow_uv) },
  { title: '店铺会员UV', key: 'shop_member_uv', width: 120, render: (row) => formatNumber(row.shop_member_uv) },
  { title: '店铺新访客', key: 'new_customer_visit_uv', width: 120, render: (row) => formatNumber(row.new_customer_visit_uv) },
  { title: '店铺新客UV', key: 'new_customer_deal_uv', width: 120, render: (row) => formatNumber(row.new_customer_deal_uv) },
  { title: '全店成交UV', key: 'deal_uv', width: 120, render: (row) => formatNumber(row.deal_uv) },
  { title: '全店成交GMV', key: 'merchant_gmv', width: 130, render: (row) => formatMoney(row.merchant_gmv) },
  { title: '任务商品成交GMV', key: 'order_product_gmv', width: 150, render: (row) => formatMoney(row.order_product_gmv) },
  { title: '任务商品新客成交GMV', key: 'order_product_new_customer_gmv', width: 170, render: (row) => formatMoney(row.order_product_new_customer_gmv) },
  { title: '非任务商品成交GMV', key: 'non_order_product_gmv', width: 160, render: (row) => formatMoney(row.non_order_product_gmv) },
  { title: '总互动量', key: 'total_interaction', width: 110, render: (row) => formatNumber(row.total_interaction) },
  { title: '店铺-收藏加购UV', key: 'collect_cart_uv', width: 140, render: (row) => formatNumber(row.collect_cart_uv) },
  { title: '总花费', key: 'total_cost', width: 120, render: (row) => formatMoney(row.total_cost) },
  { title: '笔记费用', key: 'note_fee', width: 120, render: (row) => formatMoney(row.note_fee) },
  { title: '投流费用', key: 'ad_cost', width: 120, render: (row) => formatMoney(row.ad_cost) },
  { title: '笔记条数', key: 'note_count', width: 100, render: (row) => formatNumber(row.note_count) },
  { title: '内容-曝光量', key: 'content_exposure', width: 130, render: (row) => formatNumber(row.content_exposure) },
  { title: '互动率', key: 'interaction_rate', width: 100, render: (row) => formatPercent(row.interaction_rate, 2) },
  { title: '篇均互动数', key: 'avg_interaction_per_note', width: 120, render: (row) => formatNumber(row.avg_interaction_per_note, 2) },
  { title: 'CPM', key: 'cpm', width: 100, render: (row) => formatMoney(row.cpm) },
  { title: 'CPV', key: 'cpv', width: 100, render: (row) => formatMoney(row.cpv) },
  { title: 'CPE', key: 'cpe', width: 100, render: (row) => formatMoney(row.cpe) },
  { title: '手淘搜索进店率', key: 'search_visit_rate', width: 130, render: (row) => formatPercent(row.search_visit_rate, 2) },
  { title: '进店UV收藏加购率', key: 'collect_cart_rate', width: 150, render: (row) => formatPercent(row.collect_cart_rate, 2) },
  { title: '互动进店率', key: 'interaction_visit_rate', width: 120, render: (row) => formatPercent(row.interaction_visit_rate, 2) },
  { title: '阅读进店率', key: 'read_visit_rate', width: 120, render: (row) => formatPercent(row.read_visit_rate, 2) },
  { title: '阅读搜索曝光率', key: 'read_search_exposure_rate', width: 130, render: (row) => formatPercent(row.read_search_exposure_rate, 2) },
  { title: '互动搜索曝光率', key: 'interaction_search_exposure_rate', width: 140, render: (row) => formatPercent(row.interaction_search_exposure_rate, 2) },
  { title: '进店UV成本', key: 'visit_uv_cost', width: 120, render: (row) => formatMoney(row.visit_uv_cost) },
  { title: '小红星UV成交转化率', key: 'deal_conversion_rate', width: 160, render: (row) => formatPercent(row.deal_conversion_rate, 2) },
  { title: '全店成交ROI', key: 'full_shop_roi', width: 120, render: (row) => formatNumber(row.full_shop_roi, 4) },
]

const xhxSourceColumns = [
  { title: '数据源', key: 'label', width: 180 },
  { title: '状态', key: 'latest_parse_status', width: 110, render: (row) => sourceStatusLabel(row.latest_parse_status) },
  { title: '数据行', key: 'data_rows', width: 100, render: (row) => formatNumber(row.data_rows) },
  { title: '文件数', key: 'file_count', width: 90, render: (row) => formatNumber(row.file_count) },
  { title: '最近文件', key: 'latest_file_name', minWidth: 220, ellipsis: { tooltip: true }, render: (row) => row.latest_file_name || '-' },
]

const kpiDetailColumns = [
  { title: 'KPI', key: 'kpi_name', width: 160, ellipsis: { tooltip: true } },
  { title: '分类', key: 'category', width: 100 },
  { title: '来源', key: 'source', width: 120 },
  { title: '实际值', key: 'actual_value', width: 120, render: (row) => formatKpiDisplay(row.actual_value, row.unit) },
  { title: '目标值', key: 'target_value', width: 120, render: (row) => formatKpiDisplay(row.target_value, row.unit) },
  { title: '达成率', key: 'achievement_rate', width: 110, render: (row) => formatPercent(row.achievement_rate, 1) },
  { title: '权重', key: 'weight_score', width: 90, render: (row) => formatNumber(row.weight_score, 2) },
  { title: '得分', key: 'actual_score', width: 90, render: (row) => formatNumber(row.actual_score, 2) },
  { title: '方向', key: 'direction', width: 100, render: (row) => kpiDirectionLabel(row.direction) },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      return h(NTag, { type: kpiStatusType(row.status), size: 'small' }, { default: () => row.status_label || '-' })
    },
  },
  { title: '说明', key: 'description', minWidth: 220, ellipsis: { tooltip: true } },
]

const keywordColumns = [
  { title: '关键词', key: 'keyword', width: 160, ellipsis: { tooltip: true } },
  {
    title: '统计',
    key: 'selected',
    width: 90,
    render(row) {
      return row.selected ? h(NTag, { type: 'success', size: 'small' }, { default: () => '已选' }) : '-'
    },
  },
  { title: '累计指数', key: 'search_index', width: 120, render: (row) => formatNumber(row.search_index) },
  { title: '平均指数', key: 'avg_search_index', width: 120, render: (row) => formatNumber(row.avg_search_index, 1) },
  { title: '最新日期', key: 'latest_date', width: 110 },
  { title: '最新值', key: 'latest_raw_value', width: 100, render: (row) => row.latest_raw_value || '-' },
  { title: '<100次数', key: 'less_than_threshold_count', width: 110, render: (row) => formatNumber(row.less_than_threshold_count) },
  { title: '有效天数', key: 'known_value_count', width: 100, render: (row) => formatNumber(row.known_value_count) },
]

onMounted(async () => {
  await restoreDashboardFilters()
  await handleSearch()
})

onBeforeUnmount(persistDashboardFilters)

watch(projectId, async () => {
  if (restoringDashboardFilters) return
  productCategories.value = []
  taskGroupId.value = null
  taskGroupOptions.value = []
  await loadProductOptions()
  keywordSelectionReady.value = false
  keywordFilters.value.selected_keywords = []
  persistDashboardFilters()
})

watch(productCategories, async () => {
  if (restoringDashboardFilters) return
  taskGroupId.value = null
  await loadTaskGroupOptions()
  persistDashboardFilters()
}, { deep: true })

watch(activeTab, persistDashboardFilters)
watch(taskGroupId, persistDashboardFilters)
watch(dateRange, persistDashboardFilters, { deep: true })
watch(keywordFilters, persistDashboardFilters, { deep: true })
watch(plantingFilters, persistDashboardFilters, { deep: true })

function readDashboardFilters() {
  try {
    return JSON.parse(window.sessionStorage.getItem(DASHBOARD_FILTER_STORAGE_KEY) || 'null')
  } catch {
    window.sessionStorage.removeItem(DASHBOARD_FILTER_STORAGE_KEY)
    return null
  }
}

function persistDashboardFilters() {
  if (restoringDashboardFilters) return
  try {
    window.sessionStorage.setItem(DASHBOARD_FILTER_STORAGE_KEY, JSON.stringify({
      active_tab: activeTab.value,
      project_id: projectId.value,
      product_categories: [...productCategories.value],
      task_group_id: taskGroupId.value,
      date_range: dateRange.value ? [...dateRange.value] : null,
      keyword_selection_ready: keywordSelectionReady.value,
      keyword_filters: {
        selected_keywords: [...(keywordFilters.value.selected_keywords || [])],
        keyword: keywordFilters.value.keyword || '',
      },
      planting_filters: { ...plantingFilters.value },
    }))
  } catch {
    // Keep the dashboard usable when browser storage is unavailable.
  }
}

async function restoreDashboardFilters() {
  const saved = readDashboardFilters()
  restoringDashboardFilters = true
  try {
    await loadProjects(saved?.project_id)
    await loadProductOptions()

    const availableProducts = new Set(productOptions.value.map((item) => item.value))
    const savedProducts = Array.isArray(saved?.product_categories) ? saved.product_categories : []
    productCategories.value = savedProducts.filter((value) => availableProducts.has(value))
    await loadTaskGroupOptions()

    const availableTaskGroups = new Set(taskGroupOptions.value.map((item) => item.value))
    taskGroupId.value = availableTaskGroups.has(saved?.task_group_id) ? saved.task_group_id : null
    dateRange.value = Array.isArray(saved?.date_range) && saved.date_range.length === 2 ? [...saved.date_range] : null
    activeTab.value = DASHBOARD_TABS.has(saved?.active_tab) ? saved.active_tab : 'combined'
    keywordSelectionReady.value = Boolean(saved?.keyword_selection_ready)
    keywordFilters.value = {
      selected_keywords: Array.isArray(saved?.keyword_filters?.selected_keywords)
        ? [...saved.keyword_filters.selected_keywords]
        : [],
      keyword: saved?.keyword_filters?.keyword || '',
    }
    plantingFilters.value = {
      product_category: saved?.planting_filters?.product_category || null,
      blogger_type: saved?.planting_filters?.blogger_type || null,
      note_type: saved?.planting_filters?.note_type || null,
      content_direction: saved?.planting_filters?.content_direction || null,
      keyword: saved?.planting_filters?.keyword || '',
    }
  } finally {
    restoringDashboardFilters = false
  }
  persistDashboardFilters()
}

function defaultXiaohongxing() {
  return {
    summary: {},
    cost_trend: [],
    search_trend: [],
    gmv_trend: [],
    daily_rows: [],
    task_groups: [],
    source_status: [],
    missing_mappings: {},
    kpis: {
      configured: false,
      items: [],
      total_score: null,
    },
  }
}

function defaultKeywordSearch() {
  return {
    summary: {},
    trend: [],
    keywords: [],
    filters: {},
  }
}

function defaultPlanting() {
  return {
    totals: {},
    trend: [],
    breakdowns: {
      product_category: [],
      blogger_type: [],
      note_type: [],
      content_direction: [],
    },
    notes: [],
    filters: {},
  }
}

function defaultKpiProgress() {
  return {
    configured: false,
    period_name: '',
    items: [],
    weak_items: [],
    configured_count: 0,
    scored_count: 0,
    achieved_count: 0,
    failed_count: 0,
    missing_count: 0,
    total_weight: 0,
    configured_weight: 0,
    total_score: null,
    score_rate: null,
  }
}

async function loadProjects(preferredProjectId = null) {
  const res = await api.getRedbookProjects({ page: 1, page_size: 9999, status: 'active' })
  projectOptions.value = res.data.map((item) => ({
    label: `${item.project_name} (${item.project_code})`,
    value: item.id,
    period_name: item.project_period,
  }))
  projectId.value = projectOptions.value.some((item) => item.value === preferredProjectId)
    ? preferredProjectId
    : (projectOptions.value[0]?.value || null)
}

async function loadProductOptions() {
  productOptions.value = []
  if (!projectId.value) return
  productLoading.value = true
  try {
    const res = await api.getRedbookProductOptions({ project_id: projectId.value })
    productOptions.value = (res.data || []).map((item) => ({
      label: item.label,
      value: item.value,
    }))
  } finally {
    productLoading.value = false
  }
}

async function loadTaskGroupOptions() {
  taskGroupOptions.value = []
  if (!projectId.value || !productCategories.value.length) return
  taskGroupLoading.value = true
  try {
    const res = await api.getRedbookTaskGroupOptions({
      project_id: projectId.value,
      product_categories: productCategories.value,
    })
    taskGroupOptions.value = (res.data || []).map((item) => ({
      label: item.task_name || item.label,
      value: item.task_id || item.value,
    }))
  } finally {
    taskGroupLoading.value = false
  }
}

function queryParams(extra = {}) {
  const params = { project_id: projectId.value, ...extra }
  if (productCategories.value.length) {
    delete params.product_category
    params.product_categories = productCategories.value
  }
  if (taskGroupId.value) {
    params.task_id = taskGroupId.value
  }
  if (dateRange.value?.length === 2) {
    params.date_start = dateRange.value[0]
    params.date_end = dateRange.value[1]
  }
  Object.keys(params).forEach((key) => {
    if (params[key] === null || params[key] === undefined || params[key] === '') delete params[key]
  })
  return params
}

function plantingParams() {
  return queryParams({ ...plantingFilters.value })
}

function keywordSearchParams() {
  const selectedKeywords = keywordFilters.value.selected_keywords || []
  return queryParams({
    selected_keywords: selectedKeywords.join(','),
    keyword: keywordFilters.value.keyword,
    use_default_keywords: !keywordSelectionReady.value && !selectedKeywords.length ? true : null,
  })
}

function kpiProgressParams() {
  const selectedKeywords = keywordFilters.value.selected_keywords || []
  return queryParams({
    period_name: selectedProject.value?.period_name || '',
    selected_keywords: selectedKeywords.join(','),
    keyword: keywordFilters.value.keyword,
    use_default_keywords: !keywordSelectionReady.value && !selectedKeywords.length ? true : null,
  })
}

function syncKeywordDefaultSelection() {
  if (keywordSelectionReady.value) return
  const selected = keywordSearch.value.filters?.selected_keywords || []
  if (!selected.length) return
  keywordFilters.value.selected_keywords = [...selected]
  keywordSelectionReady.value = true
}

async function handleSearch() {
  if (!projectId.value) return
  loading.value = true
  try {
    const [overviewRes, plantingRes, xhxRes, keywordRes, kpiRes] = await Promise.all([
      api.getRedbookDashboardOverview(queryParams()),
      api.getRedbookAdsEfficiency(plantingParams()),
      api.getRedbookXiaohongxingDashboard(queryParams()),
      api.getRedbookKeywordSearchDashboard(keywordSearchParams()),
      api.getRedbookKpiProgress(kpiProgressParams()),
    ])
    totals.value = overviewRes.data.totals || {}
    planting.value = { ...defaultPlanting(), ...(plantingRes.data || {}) }
    xiaohongxing.value = { ...defaultXiaohongxing(), ...(xhxRes.data || {}) }
    keywordSearch.value = { ...defaultKeywordSearch(), ...(keywordRes.data || {}) }
    kpiProgress.value = { ...defaultKpiProgress(), ...(kpiRes.data || {}) }
    syncKeywordDefaultSelection()
  } finally {
    loading.value = false
  }
}

async function handleRebuild() {
  if (!projectId.value) {
    window.$message?.warning('请选择项目')
    return
  }
  rebuilding.value = true
  try {
    await api.rebuildRedbookAll({
      project_id: projectId.value,
      date_start: dateRange.value?.[0] || null,
      date_end: dateRange.value?.[1] || null,
      build_note_daily: true,
      build_task_daily: true,
      build_project_daily: true,
    })
    window.$message?.success('重算完成')
    await handleSearch()
  } finally {
    rebuilding.value = false
  }
}

function resetPlantingFilters() {
  plantingFilters.value = {
    product_category: null,
    blogger_type: null,
    note_type: null,
    content_direction: null,
    keyword: '',
  }
}

function resetKeywordFilters() {
  keywordSelectionReady.value = false
  keywordFilters.value = {
    selected_keywords: [],
    keyword: '',
  }
}

function toNumber(value) {
  const number = Number(value || 0)
  return Number.isFinite(number) ? number : 0
}

function safeRatio(numerator, denominator, multiplier = 1) {
  const divisor = toNumber(denominator)
  if (!divisor) return null
  return (toNumber(numerator) / divisor) * multiplier
}

function pickValue(...values) {
  return values.find((value) => value !== null && value !== undefined && value !== '') ?? 0
}

function parseStatDate(value) {
  if (!value) return null
  const date = new Date(`${value}T00:00:00`)
  return Number.isNaN(date.getTime()) ? null : date
}

function formatDateKey(date) {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatMonthDay(date) {
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${month}-${day}`
}

function addDays(date, days) {
  const next = new Date(date)
  next.setDate(next.getDate() + days)
  return next
}

function weekStartOf(date) {
  const start = new Date(date)
  const day = start.getDay() || 7
  start.setDate(start.getDate() - day + 1)
  return start
}

function costGranularityUnit(granularity) {
  if (granularity === 'week') return '周'
  if (granularity === 'month') return '月'
  return '天'
}

function costPeriodMeta(row, granularity) {
  const date = parseStatDate(row.stat_date)
  if (!date) {
    return { key: row.stat_date || '未知日期', label: row.stat_date || '未知日期', sort: row.stat_date || '' }
  }
  if (granularity === 'week') {
    const start = weekStartOf(date)
    const end = addDays(start, 6)
    return {
      key: formatDateKey(start),
      label: `${formatMonthDay(start)}-${formatMonthDay(end)}`,
      sort: formatDateKey(start),
    }
  }
  if (granularity === 'month') {
    const key = `${date.getFullYear()}-${`${date.getMonth() + 1}`.padStart(2, '0')}`
    return { key, label: key, sort: `${key}-01` }
  }
  return { key: formatDateKey(date), label: formatMonthDay(date), sort: formatDateKey(date) }
}

function aggregateCostTrend(rows = [], granularity = 'day') {
  const grouped = new Map()
  rows.forEach((row) => {
    const meta = costPeriodMeta(row, granularity)
    if (!grouped.has(meta.key)) {
      grouped.set(meta.key, {
        key: meta.key,
        label: meta.label,
        sort: meta.sort,
        note_fee: 0,
        ad_cost: 0,
        total_cost: 0,
      })
    }
    const target = grouped.get(meta.key)
    target.note_fee += toNumber(row.note_fee)
    target.ad_cost += toNumber(row.ad_cost)
    target.total_cost = target.note_fee + target.ad_cost
  })
  return Array.from(grouped.values()).sort((a, b) => String(a.sort).localeCompare(String(b.sort)))
}

function buildCostTrendSummary(rows = [], granularity = 'day') {
  const total = rows.reduce(
    (acc, row) => {
      acc.note_fee += toNumber(row.note_fee)
      acc.ad_cost += toNumber(row.ad_cost)
      acc.total_cost += toNumber(row.total_cost)
      return acc
    },
    { note_fee: 0, ad_cost: 0, total_cost: 0 }
  )
  const peak = rows.reduce((current, row) => (toNumber(row.total_cost) > toNumber(current?.total_cost) ? row : current), null)
  const unit = costGranularityUnit(granularity)
  return [
    { label: '当前总花费', value: formatMoney(total.total_cost), sub: `${rows.length} 个${unit}周期` },
    { label: '笔记花费占比', value: formatPercent(safeRatio(total.note_fee, total.total_cost), 1), sub: formatMoney(total.note_fee) },
    { label: '投流花费占比', value: formatPercent(safeRatio(total.ad_cost, total.total_cost), 1), sub: formatMoney(total.ad_cost) },
    { label: `最高花费${unit}`, value: peak ? formatMoney(peak.total_cost) : '-', sub: peak?.label || '-' },
  ]
}

function compactMoney(value, maxValue = value) {
  const number = toNumber(value)
  const maxNumber = Math.abs(toNumber(maxValue))
  if (!number) return '¥0'
  if (maxNumber >= 100000000) return `¥${formatNumber(number / 100000000, 1)}亿`
  if (maxNumber >= 10000) return `¥${formatNumber(number / 10000, 1)}万`
  return `¥${formatNumber(number, 0)}`
}

function buildCostTrendChart(rows = []) {
  const width = 960
  const height = 320
  const left = 72
  const right = 22
  const top = 24
  const bottom = 48
  const plotWidth = width - left - right
  const plotHeight = height - top - bottom
  const maxTotal = Math.max(...rows.map((row) => toNumber(row.total_cost)), 1)
  const step = rows.length ? plotWidth / rows.length : plotWidth
  const barWidth = Math.max(5, Math.min(30, step * 0.56))
  const labelEvery = Math.max(1, Math.ceil(rows.length / 9))
  const baseline = height - bottom
  const bars = rows.map((row, index) => {
    const noteHeight = (toNumber(row.note_fee) / maxTotal) * plotHeight
    const adHeight = (toNumber(row.ad_cost) / maxTotal) * plotHeight
    const totalHeight = noteHeight + adHeight
    const x = left + index * step + (step - barWidth) / 2
    return {
      ...row,
      x,
      barWidth,
      noteY: baseline - noteHeight,
      noteHeight,
      adY: baseline - totalHeight,
      adHeight,
      totalX: x + barWidth / 2,
      totalY: baseline - totalHeight,
      showLabel: index % labelEvery === 0 || index === rows.length - 1,
      title: `${row.label} 总花费 ${formatMoney(row.total_cost)}，笔记 ${formatMoney(row.note_fee)}，投流 ${formatMoney(row.ad_cost)}`,
    }
  })
  const totalLine = bars.map((bar) => `${bar.totalX.toFixed(1)},${bar.totalY.toFixed(1)}`).join(' ')
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
    const value = maxTotal * ratio
    return {
      y: baseline - plotHeight * ratio,
      label: compactMoney(value, maxTotal),
    }
  })
  return { width, height, left, right, top, bottom, baseline, bars, ticks, totalLine }
}

function compactIndex(value, maxValue = value) {
  const number = toNumber(value)
  const maxNumber = Math.abs(toNumber(maxValue))
  if (!number) return '0'
  if (maxNumber >= 10000) return `${formatNumber(number / 10000, 1)}万`
  return formatNumber(number, 0)
}

function keywordTrendValue(row, keyword) {
  const item = (row.keyword_values || []).find((keywordItem) => keywordItem.keyword === keyword)
  return toNumber(item?.search_index)
}

function keywordDateLabel(value) {
  const date = parseStatDate(value)
  return date ? formatMonthDay(date) : value || '-'
}

function buildKeywordTrendChart(rows = [], keywords = []) {
  const width = 960
  const height = 340
  const left = 58
  const right = 26
  const top = 24
  const bottom = 60
  const plotWidth = width - left - right
  const plotHeight = height - top - bottom
  const baseline = height - bottom
  const keywordList = keywords.length
    ? keywords
    : Array.from(new Set(rows.flatMap((row) => (row.keyword_values || []).map((item) => item.keyword)))).slice(0, 5)
  if (!rows.length || !keywordList.length) {
    return { width, height, left, right, top, bottom, baseline, series: [], ticks: [], labels: [] }
  }
  const maxValue = Math.max(
    ...rows.flatMap((row) => keywordList.map((keyword) => keywordTrendValue(row, keyword))),
    1
  )
  const step = rows.length > 1 ? plotWidth / (rows.length - 1) : plotWidth
  const labelEvery = Math.max(1, Math.ceil(rows.length / 7))
  const series = keywordList.map((keyword, index) => {
    const points = rows.map((row, rowIndex) => {
      const value = keywordTrendValue(row, keyword)
      const x = left + rowIndex * step
      const y = baseline - (value / maxValue) * plotHeight
      return {
        x,
        y,
        value,
        stat_date: row.stat_date,
        title: `${row.stat_date} ${keyword}：${formatNumber(value)}`,
      }
    })
    return {
      keyword,
      color: keywordColor(index),
      points,
      pointString: points.map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(' '),
    }
  })
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
    y: baseline - plotHeight * ratio,
    label: compactIndex(maxValue * ratio, maxValue),
  }))
  const labels = rows
    .map((row, index) => ({
      x: left + index * step,
      label: keywordDateLabel(row.stat_date),
      show: index % labelEvery === 0 || index === rows.length - 1,
    }))
    .filter((item) => item.show)
  return { width, height, left, right, top, bottom, baseline, series, ticks, labels }
}

function metricAverage(rows = [], key) {
  const values = rows.map((row) => toNumber(row[key])).filter((value) => value > 0)
  if (!values.length) return 0
  return values.reduce((sum, value) => sum + value, 0) / values.length
}

function metricLatest(rows = [], key) {
  for (let index = rows.length - 1; index >= 0; index -= 1) {
    const value = toNumber(rows[index]?.[key])
    if (value > 0) return value
  }
  return 0
}

function buildAdCostMetricChart(rows = [], metric) {
  const width = 220
  const height = 86
  const left = 8
  const right = 8
  const top = 8
  const bottom = 12
  const plotWidth = width - left - right
  const plotHeight = height - top - bottom
  const baseline = height - bottom
  const values = rows.map((row) => toNumber(row[metric.key]))
  const actualMax = Math.max(...values, 0)
  const scaleMax = Math.max(actualMax, 1)
  const step = rows.length > 1 ? plotWidth / (rows.length - 1) : plotWidth
  const points = rows.map((row, index) => {
    const value = toNumber(row[metric.key])
    const x = left + index * step
    const y = baseline - (value / scaleMax) * plotHeight
    return {
      x,
      y,
      value,
      title: `${row.stat_date} ${metric.label}：${formatMoney(value)}`,
    }
  })
  return {
    ...metric,
    latest: metricLatest(rows, metric.key),
    avg: metricAverage(rows, metric.key),
    max: actualMax,
    width,
    height,
    baseline,
    points,
    pointString: points.map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(' '),
  }
}

function sumMetric(rows = [], key) {
  return rows.reduce((sum, row) => sum + toNumber(row[key]), 0)
}

function buildAdVolumeSummary(rows = [], mode) {
  const adCost = sumMetric(rows, 'ad_cost')
  const volume = sumMetric(rows, mode.volumeKey)
  const unitCost = safeRatio(adCost, volume)
  const peak = rows.reduce((current, row) => (toNumber(row[mode.volumeKey]) > toNumber(current?.[mode.volumeKey]) ? row : current), null)
  const summary = [
    { label: '投流消耗', value: formatMoney(adCost), sub: `${rows.length} 天` },
    { label: mode.volumeLabel, value: formatNumber(volume), sub: '当前筛选汇总' },
  ]
  if (mode.value === 'clicks') {
    summary.push({
      label: '点击率',
      value: formatPercent(safeRatio(volume, sumMetric(rows, 'impressions')), 2),
      sub: '点击量 / 曝光量',
    })
  }
  summary.push(
    { label: mode.unitCostLabel, value: formatMoney(unitCost), sub: `${mode.label}成本` },
    { label: '峰值日期', value: peak?.stat_date || '-', sub: peak ? formatNumber(peak[mode.volumeKey]) : '-' },
  )
  return summary
}

function buildAdVolumeChart(rows = [], mode) {
  const width = 960
  const height = 330
  const left = 66
  const right = 74
  const top = 24
  const bottom = 48
  const plotWidth = width - left - right
  const plotHeight = height - top - bottom
  const baseline = height - bottom
  if (!rows.length) {
    return { width, height, left, right, top, bottom, baseline, bars: [], linePoints: '', ticks: [], volumeTicks: [], labels: [] }
  }
  const maxCost = Math.max(...rows.map((row) => toNumber(row.ad_cost)), 1)
  const maxVolume = Math.max(...rows.map((row) => toNumber(row[mode.volumeKey])), 1)
  const step = rows.length ? plotWidth / rows.length : plotWidth
  const barWidth = Math.max(5, Math.min(24, step * 0.52))
  const labelEvery = Math.max(1, Math.ceil(rows.length / 8))
  const bars = rows.map((row, index) => {
    const adCost = toNumber(row.ad_cost)
    const volume = toNumber(row[mode.volumeKey])
    const barHeight = (adCost / maxCost) * plotHeight
    const x = left + index * step + (step - barWidth) / 2
    const lineX = left + index * step + step / 2
    const lineY = baseline - (volume / maxVolume) * plotHeight
    return {
      key: row.stat_date,
      x,
      width: barWidth,
      y: baseline - barHeight,
      height: barHeight,
      lineX,
      lineY,
      label: keywordDateLabel(row.stat_date),
      showLabel: index % labelEvery === 0 || index === rows.length - 1,
      title: `${row.stat_date} 投流消耗 ${formatMoney(adCost)}，${mode.volumeLabel} ${formatNumber(volume)}，${mode.unitCostLabel} ${formatMoney(row[mode.unitCostKey])}`,
    }
  })
  const linePoints = bars.map((bar) => `${bar.lineX.toFixed(1)},${bar.lineY.toFixed(1)}`).join(' ')
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
    y: baseline - plotHeight * ratio,
    label: compactMoney(maxCost * ratio, maxCost),
  }))
  const volumeTicks = [0, 0.5, 1].map((ratio) => ({
    y: baseline - plotHeight * ratio,
    label: compactIndex(maxVolume * ratio, maxVolume),
  }))
  const labels = bars.filter((bar) => bar.showLabel)
  return { width, height, left, right, top, bottom, baseline, bars, linePoints, ticks, volumeTicks, labels, color: mode.color }
}

function topNotesByMetric(rows = [], key, limit = 8) {
  return [...rows]
    .filter((row) => toNumber(row[key]) > 0)
    .sort((a, b) => toNumber(b[key]) - toNumber(a[key]))
    .slice(0, limit)
}

function noteDisplayName(row) {
  return row.blogger_name || row.note_id || '-'
}

function noteDisplaySub(row) {
  return [row.product_category, row.content_direction].filter(Boolean).join(' / ') || row.note_id || '-'
}

function overviewTotalCost() {
  return pickValue(planting.value.totals.total_cost, totals.value.total_cost, xhxSummary.value.total_cost)
}

function overviewNoteFee() {
  return pickValue(planting.value.totals.note_fee, totals.value.note_fee, xhxSummary.value.note_fee)
}

function overviewAdCost() {
  return pickValue(planting.value.totals.ad_cost, totals.value.ad_cost, xhxSummary.value.ad_cost)
}

function overviewContentExposure() {
  return pickValue(xhxSummary.value.content_exposure, planting.value.totals.pgy_exposure, planting.value.totals.impressions, totals.value.impressions)
}

function overviewReadPlayUv() {
  return pickValue(xhxSummary.value.read_play_uv, planting.value.totals.pgy_read_count)
}

function overviewInteractionUv() {
  return pickValue(xhxSummary.value.interaction_uv, planting.value.totals.interactions, totals.value.interactions)
}

function overviewRoi() {
  return safeRatio(xhxSummary.value.merchant_gmv, overviewTotalCost())
}

function buildOverviewCoreCards() {
  const totalCost = overviewTotalCost()
  const noteFee = overviewNoteFee()
  const adCost = overviewAdCost()
  const readPlayUv = overviewReadPlayUv()
  const interactionUv = overviewInteractionUv()
  const searchVisitUv = toNumber(xhxSummary.value.search_visit_uv)
  const shopVisitUv = toNumber(xhxSummary.value.shop_visit_uv)
  const dealUv = toNumber(xhxSummary.value.deal_uv)
  const merchantGmv = toNumber(xhxSummary.value.merchant_gmv)
  return [
    { label: '总花费', value: formatMoney(totalCost), sub: `笔记 ${formatMoney(noteFee)} / 投流 ${formatMoney(adCost)}`, tone: 'cost' },
    { label: '内容曝光', value: formatNumber(overviewContentExposure()), sub: `点击 ${formatNumber(planting.value.totals.clicks)}`, tone: 'content' },
    { label: '阅读/播放 UV', value: formatNumber(readPlayUv), sub: `互动率 ${formatPercent(safeRatio(interactionUv, readPlayUv), 2)}`, tone: 'content' },
    { label: '互动 UV', value: formatNumber(interactionUv), sub: `互动成本 ${formatMoney(safeRatio(totalCost, interactionUv))}`, tone: 'content' },
    { label: '红搜指数', value: formatNumber(keywordSummary.value.search_index), sub: `已选 ${formatNumber(keywordSummary.value.selected_keyword_count)} 个关键词`, tone: 'search' },
    { label: '搜索进店 / 进店', value: `${formatNumber(searchVisitUv)} / ${formatNumber(shopVisitUv)}`, sub: `收藏加购 ${formatNumber(xhxSummary.value.collect_cart_uv)}`, tone: 'visit' },
    { label: 'GMV', value: formatMoney(merchantGmv), sub: `成交 UV ${formatNumber(dealUv)}`, tone: 'gmv' },
    { label: 'ROI', value: formatNumber(overviewRoi(), 4), sub: 'GMV / 总花费', tone: 'gmv' },
  ]
}

function funnelRate(label, numerator, denominator) {
  const ratio = safeRatio(numerator, denominator)
  return ratio === null ? label : `${label} ${formatPercent(ratio, 2)}`
}

function buildOverviewFunnelItems() {
  const contentExposure = overviewContentExposure()
  const readPlayUv = overviewReadPlayUv()
  const interactionUv = overviewInteractionUv()
  const searchExposureUv = toNumber(xhxSummary.value.search_exposure_uv)
  const searchVisitUv = toNumber(xhxSummary.value.search_visit_uv)
  const shopVisitUv = toNumber(xhxSummary.value.shop_visit_uv)
  const collectCartUv = toNumber(xhxSummary.value.collect_cart_uv)
  const dealUv = toNumber(xhxSummary.value.deal_uv)
  const merchantGmv = toNumber(xhxSummary.value.merchant_gmv)
  return [
    { label: '内容曝光', value: formatNumber(contentExposure), sub: '前端触达', source: '蒲公英/聚光', tone: 'content' },
    { label: '阅读/播放', value: formatNumber(readPlayUv), sub: funnelRate('阅读率', readPlayUv, contentExposure), source: '蒲公英/小红星', tone: 'content' },
    { label: '互动', value: formatNumber(interactionUv), sub: funnelRate('互动率', interactionUv, readPlayUv), source: '聚光/小红星', tone: 'content' },
    { label: '红搜指数', value: formatNumber(keywordSummary.value.search_index), sub: '搜索声量', source: '搜索日报', tone: 'search' },
    { label: '搜索进店', value: formatNumber(searchVisitUv), sub: funnelRate('搜索进店率', searchVisitUv, searchExposureUv), source: '小红星', tone: 'visit' },
    { label: '进店 UV', value: formatNumber(shopVisitUv), sub: funnelRate('引流率', shopVisitUv, readPlayUv), source: '小红星', tone: 'visit' },
    { label: '收藏/加购', value: formatNumber(collectCartUv), sub: funnelRate('收藏加购率', collectCartUv, shopVisitUv), source: '小红星', tone: 'visit' },
    { label: '成交 UV', value: formatNumber(dealUv), sub: funnelRate('成交转化率', dealUv, shopVisitUv), source: '小红星', tone: 'deal' },
    { label: 'GMV', value: formatMoney(merchantGmv), sub: `ROI ${formatNumber(overviewRoi(), 4)}`, source: '小红星', tone: 'deal' },
  ]
}

function ensureOverviewTrendRow(map, dateKey) {
  if (!map.has(dateKey)) {
    map.set(dateKey, {
      stat_date: dateKey,
      note_fee: 0,
      ad_cost: 0,
      total_cost: 0,
      search_index: 0,
      shop_visit_uv: 0,
      merchant_gmv: 0,
    })
  }
  return map.get(dateKey)
}

function buildOverviewTrendRows(costRows = [], searchRows = [], xhxRows = []) {
  const grouped = new Map()
  costRows.forEach((row) => {
    if (!row.stat_date) return
    const target = ensureOverviewTrendRow(grouped, row.stat_date)
    target.note_fee += toNumber(row.note_fee)
    target.ad_cost += toNumber(row.ad_cost)
    target.total_cost += toNumber(row.total_cost || toNumber(row.note_fee) + toNumber(row.ad_cost))
  })
  searchRows.forEach((row) => {
    if (!row.stat_date) return
    ensureOverviewTrendRow(grouped, row.stat_date).search_index += toNumber(row.search_index)
  })
  xhxRows.forEach((row) => {
    if (!row.stat_date) return
    const target = ensureOverviewTrendRow(grouped, row.stat_date)
    target.shop_visit_uv += toNumber(row.shop_visit_uv)
    target.merchant_gmv += toNumber(row.merchant_gmv)
  })
  return Array.from(grouped.values()).sort((a, b) => String(a.stat_date).localeCompare(String(b.stat_date)))
}

function formatOverviewTrendValue(mode, value) {
  return mode.formatter ? mode.formatter(value) : formatNumber(value)
}

function compactOverviewResult(value, maxValue, mode) {
  if (mode.value === 'gmv') return compactMoney(value, maxValue)
  return compactIndex(value, maxValue)
}

function buildOverviewTrendSummary(rows = [], mode) {
  const totalCost = sumMetric(rows, 'total_cost')
  const resultTotal = sumMetric(rows, mode.resultKey)
  const peakCost = rows.reduce((current, row) => (toNumber(row.total_cost) > toNumber(current?.total_cost) ? row : current), null)
  const peakResult = rows.reduce((current, row) => (toNumber(row[mode.resultKey]) > toNumber(current?.[mode.resultKey]) ? row : current), null)
  return [
    { label: '投放花费', value: formatMoney(totalCost), sub: `${rows.length} 天` },
    { label: mode.resultLabel, value: formatOverviewTrendValue(mode, resultTotal), sub: '当前结果指标汇总' },
    { label: '最高花费日', value: peakCost?.stat_date || '-', sub: peakCost ? formatMoney(peakCost.total_cost) : '-' },
    { label: `最高${mode.resultLabel}`, value: peakResult?.stat_date || '-', sub: peakResult ? formatOverviewTrendValue(mode, peakResult[mode.resultKey]) : '-' },
  ]
}

function buildOverviewTrendChart(rows = [], mode) {
  const width = 960
  const height = 330
  const left = 72
  const right = 74
  const top = 24
  const bottom = 48
  const plotWidth = width - left - right
  const plotHeight = height - top - bottom
  const baseline = height - bottom
  if (!rows.length) {
    return { width, height, left, right, top, bottom, baseline, bars: [], ticks: [], resultTicks: [], labels: [], resultLine: '' }
  }
  const maxCost = Math.max(...rows.map((row) => toNumber(row.total_cost)), 1)
  const maxResult = Math.max(...rows.map((row) => toNumber(row[mode.resultKey])), 1)
  const step = rows.length ? plotWidth / rows.length : plotWidth
  const barWidth = Math.max(5, Math.min(26, step * 0.52))
  const labelEvery = Math.max(1, Math.ceil(rows.length / 8))
  const bars = rows.map((row, index) => {
    const noteHeight = (toNumber(row.note_fee) / maxCost) * plotHeight
    const adHeight = (toNumber(row.ad_cost) / maxCost) * plotHeight
    const totalHeight = noteHeight + adHeight
    const x = left + index * step + (step - barWidth) / 2
    const lineX = left + index * step + step / 2
    const lineY = baseline - (toNumber(row[mode.resultKey]) / maxResult) * plotHeight
    return {
      ...row,
      x,
      width: barWidth,
      noteY: baseline - noteHeight,
      noteHeight,
      adY: baseline - totalHeight,
      adHeight,
      lineX,
      lineY,
      label: keywordDateLabel(row.stat_date),
      showLabel: index % labelEvery === 0 || index === rows.length - 1,
      title: `${row.stat_date} 花费 ${formatMoney(row.total_cost)}，${mode.resultLabel} ${formatOverviewTrendValue(mode, row[mode.resultKey])}`,
    }
  })
  const resultLine = bars.map((bar) => `${bar.lineX.toFixed(1)},${bar.lineY.toFixed(1)}`).join(' ')
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
    y: baseline - plotHeight * ratio,
    label: compactMoney(maxCost * ratio, maxCost),
  }))
  const resultTicks = [0, 0.5, 1].map((ratio) => ({
    y: baseline - plotHeight * ratio,
    label: compactOverviewResult(maxResult * ratio, maxResult, mode),
  }))
  return { width, height, left, right, top, bottom, baseline, bars, ticks, resultTicks, labels: bars.filter((bar) => bar.showLabel), resultLine }
}

function statusTone(status) {
  if (status === 'success') return 'ok'
  if (status === 'partial_success' || status === 'pending') return 'warn'
  return 'bad'
}

function buildOverviewSourceCards(rows = [], missing = {}, keyword = {}) {
  return rows.map((row) => {
    const tone = statusTone(row.latest_parse_status)
    let sub = `数据行 ${formatNumber(row.data_rows)} · 文件 ${formatNumber(row.file_count)}`
    if (row.source_type === 'keyword_search') {
      sub = `关键词 ${formatNumber(keyword.available_keyword_count)} · 已选 ${formatNumber(keyword.selected_keyword_count)}`
    }
    if (row.source_type === 'note_mapping') {
      sub = `映射 ${formatNumber(row.data_rows)} · 未匹配笔记 ${formatNumber(missing.unmatched_note_count)}`
    }
    if (row.source_type === 'task_mapping') {
      sub = `映射 ${formatNumber(row.data_rows)} · 未匹配订单 ${formatNumber(missing.unmatched_order_count)}`
    }
    return {
      label: row.label,
      status: sourceStatusLabel(row.latest_parse_status),
      tone,
      sub,
      file: row.latest_file_name || '暂无文件',
    }
  })
}

function trendChange(rows = [], key) {
  const values = rows.map((row) => toNumber(row[key])).filter((value) => value > 0)
  if (values.length < 2) return null
  const first = values[0]
  const last = values[values.length - 1]
  return safeRatio(last - first, first)
}

function buildOverviewDiagnostics() {
  const totalCost = overviewTotalCost()
  const noteFee = overviewNoteFee()
  const adCost = overviewAdCost()
  const noteRatio = safeRatio(noteFee, totalCost)
  const adRatio = safeRatio(adCost, totalCost)
  const searchChange = trendChange(keywordTrend.value, 'search_index')
  const readPlayUv = overviewReadPlayUv()
  const shopVisitUv = toNumber(xhxSummary.value.shop_visit_uv)
  const dealUv = toNumber(xhxSummary.value.deal_uv)
  const merchantGmv = toNumber(xhxSummary.value.merchant_gmv)
  const unmatchedOrders = toNumber(xhxMissingMappings.value.unmatched_order_count)
  const unmatchedNotes = toNumber(xhxMissingMappings.value.unmatched_note_count)
  return [
    {
      title: '花费结构',
      tone: adRatio !== null && adRatio > 0.7 ? 'warn' : 'ok',
      value: totalCost ? `笔记 ${formatPercent(noteRatio, 1)} / 投流 ${formatPercent(adRatio, 1)}` : '暂无花费',
      desc: totalCost ? '用于判断费用是否过度偏向单一投入方式。' : '请先上传蒲公英和聚光数据。',
      target: 'planting',
      action: '查看种草投流',
    },
    {
      title: '搜索声量',
      tone: searchChange === null ? 'warn' : searchChange < -0.15 ? 'warn' : 'ok',
      value: searchChange === null ? '趋势不足' : `${searchChange >= 0 ? '增长' : '下降'} ${formatPercent(Math.abs(searchChange), 1)}`,
      desc: '红搜趋势反映种草内容带来的搜索声量变化。',
      target: 'keyword-search',
      action: '查看红搜',
    },
    {
      title: '承接效率',
      tone: shopVisitUv && !dealUv ? 'warn' : 'ok',
      value: `进店 ${formatNumber(shopVisitUv)} · 成交 ${formatNumber(dealUv)}`,
      desc: readPlayUv ? `阅读到进店率 ${formatPercent(safeRatio(shopVisitUv, readPlayUv), 2)}。` : '暂无阅读数据，暂无法判断承接效率。',
      target: 'xiaohongxing',
      action: '查看小红星',
    },
    {
      title: '成交结果',
      tone: merchantGmv > 0 ? 'ok' : 'warn',
      value: `${formatMoney(merchantGmv)} · ROI ${formatNumber(overviewRoi(), 4)}`,
      desc: '用于判断投放后的后链路成交规模和投入产出。',
      target: 'xiaohongxing',
      action: '查看成交',
    },
    {
      title: '映射健康',
      tone: unmatchedOrders || unmatchedNotes ? 'warn' : 'ok',
      value: `订单 ${formatNumber(unmatchedOrders)} · 笔记 ${formatNumber(unmatchedNotes)}`,
      desc: unmatchedOrders || unmatchedNotes ? '存在未匹配数据，会影响任务组或笔记维度下钻。' : '当前未发现未匹配订单或笔记。',
      target: 'xiaohongxing',
      action: '查看映射影响',
    },
  ]
}

function pickMetric(summary, fallback, key) {
  return summary?.[key] ?? fallback?.[key]
}

function detailMetric(label, value, type = 'number', definition = '', digits = null) {
  return { label, value, type, definition, digits }
}

function formatDetailValue(item) {
  if (item.value === null || item.value === undefined || item.value === '') return '-'
  if (item.type === 'money') return formatMoney(item.value)
  if (item.type === 'percent') return formatPercent(item.value, item.digits ?? 2)
  if (item.type === 'decimal') return formatNumber(item.value, item.digits ?? 2)
  return formatNumber(item.value, item.digits ?? 0)
}

function detailPrimaryCount(group) {
  if (!group?.items?.length) return 0
  if (group.title === '店铺成交') return 4
  return Math.min(3, group.items.length)
}

function detailPrimaryItems(group) {
  return (group.items || []).slice(0, detailPrimaryCount(group))
}

function detailSecondaryItems(group) {
  return (group.items || []).slice(detailPrimaryCount(group))
}

function buildXhxDetailGroups(summary, fallback = {}) {
  const value = (key) => pickMetric(summary, fallback, key)
  const totalCost = value('total_cost')
  const noteFee = value('note_fee')
  const adCost = value('ad_cost')
  const serviceFee = value('service_fee')
  const noteCount = value('note_count')
  const contentExposure = value('content_exposure')
  const readPlayUv = value('read_play_uv')
  const interactionUv = value('interaction_uv')
  const searchExposureUv = value('search_exposure_uv')
  const searchVisitUv = value('search_visit_uv')
  const shopVisitUv = value('shop_visit_uv')
  const collectCartUv = value('collect_cart_uv')
  const newCustomerVisitUv = value('new_customer_visit_uv')
  const newCustomerDealUv = value('new_customer_deal_uv')
  const dealUv = value('deal_uv')
  const merchantGmv = value('merchant_gmv')
  const orderProductGmv = value('order_product_gmv')
  const orderProductNewCustomerGmv = value('order_product_new_customer_gmv')
  const nonOrderProductGmv = value('non_order_product_gmv')
  const newCustomerAov = safeRatio(orderProductNewCustomerGmv, newCustomerDealUv)
  const dealAov = safeRatio(merchantGmv, dealUv)

  return [
    {
      title: '内容规划',
      note: '费用结构与报备规模',
      items: [
        detailMetric('总花费', totalCost, 'money'),
        detailMetric('笔记费用', noteFee, 'money', '蒲公英费用'),
        detailMetric('投流费用', adCost, 'money', '投流/广告费用'),
        detailMetric('服务费', serviceFee, 'money', '当前按蒲公英服务费汇总展示'),
        detailMetric('报备笔记篇数', noteCount, 'number'),
        detailMetric('笔记费用率', safeRatio(noteFee, totalCost), 'percent'),
        detailMetric('投流费用率', safeRatio(adCost, totalCost), 'percent'),
        detailMetric('服务费率', safeRatio(serviceFee, totalCost), 'percent'),
        detailMetric('笔记篇均成本', safeRatio(totalCost, noteCount), 'money'),
      ],
    },
    {
      title: '社区数据',
      note: '内容侧曝光、阅读与互动效率',
      items: [
        detailMetric('内容-曝光量', contentExposure, 'number', '内容投放总曝光数'),
        detailMetric('阅读/播放UV', readPlayUv, 'number', '内容阅读数'),
        detailMetric('互动UV', interactionUv, 'number', '内容投放产生的互动数'),
        detailMetric('互动率', safeRatio(interactionUv, readPlayUv), 'percent'),
        detailMetric('篇均互动数', safeRatio(interactionUv, noteCount), 'decimal', '平均每篇笔记的互动数', 2),
        detailMetric('CPM', safeRatio(totalCost, contentExposure, 1000), 'money', '千次展现成本'),
        detailMetric('CPV', safeRatio(totalCost, readPlayUv), 'money', '平均单次阅读成本'),
        detailMetric('CPE', safeRatio(totalCost, interactionUv), 'money', '平均单次互动成本'),
      ],
    },
    {
      title: '阅读流转效率',
      note: '阅读人群向搜索、进店和成交的流转',
      items: [
        detailMetric('阅读搜索曝光率', safeRatio(searchExposureUv, readPlayUv), 'percent'),
        detailMetric('阅读搜索进店率', safeRatio(searchVisitUv, readPlayUv), 'percent'),
        detailMetric('阅读进店率', safeRatio(shopVisitUv, readPlayUv), 'percent'),
        detailMetric('阅读成交转化率', safeRatio(dealUv, readPlayUv), 'percent'),
        detailMetric('阅读收藏加购率', safeRatio(collectCartUv, readPlayUv), 'percent'),
      ],
    },
    {
      title: '互动流转效率',
      note: '互动人群向搜索、进店和成交的流转',
      items: [
        detailMetric('互动搜索曝光率', safeRatio(searchExposureUv, interactionUv), 'percent'),
        detailMetric('互动搜索进店率', safeRatio(searchVisitUv, interactionUv), 'percent'),
        detailMetric('互动进店率', safeRatio(shopVisitUv, interactionUv), 'percent'),
        detailMetric('互动成交转化率', safeRatio(dealUv, interactionUv), 'percent'),
        detailMetric('互动收藏加购率', safeRatio(collectCartUv, interactionUv), 'percent'),
      ],
    },
    {
      title: '进店动作',
      note: '淘系承接动作与进店质量',
      items: [
        detailMetric('手淘搜索曝光UV', searchExposureUv, 'number'),
        detailMetric('手淘搜索进店UV', searchVisitUv, 'number'),
        detailMetric('进店UV', shopVisitUv, 'number'),
        detailMetric('店铺-收藏加购UV', collectCartUv, 'number'),
        detailMetric('店铺新访客', newCustomerVisitUv, 'number'),
        detailMetric('店铺新客UV', newCustomerDealUv, 'number'),
        detailMetric('手淘搜索进店率', safeRatio(searchVisitUv, searchExposureUv), 'percent'),
        detailMetric('进店UV收藏加购率', safeRatio(collectCartUv, shopVisitUv), 'percent'),
      ],
    },
    {
      title: '成本核算',
      note: '关键承接动作的获客成本',
      items: [
        detailMetric('成交新客成本', safeRatio(totalCost, newCustomerDealUv), 'money'),
        detailMetric('手淘搜索曝光UV成本', safeRatio(totalCost, searchExposureUv), 'money'),
        detailMetric('手淘搜索进店UV成本', safeRatio(totalCost, searchVisitUv), 'money'),
        detailMetric('进店UV成本', safeRatio(totalCost, shopVisitUv), 'money'),
        detailMetric('收藏加购成本', safeRatio(totalCost, collectCartUv), 'money'),
        detailMetric('新访客成本', safeRatio(totalCost, newCustomerVisitUv), 'money'),
        detailMetric('成交UV成本', safeRatio(totalCost, dealUv), 'money'),
      ],
    },
    {
      title: '店铺成交',
      note: '成交规模、商品结构与新客质量',
      items: [
        detailMetric('非任务商品成交GMV', nonOrderProductGmv, 'money'),
        detailMetric('全店成交UV', dealUv, 'number'),
        detailMetric('全店成交GMV', merchantGmv, 'money'),
        detailMetric('任务商品成交GMV', orderProductGmv, 'money'),
        detailMetric('任务商品新客成交GMV', orderProductNewCustomerGmv, 'money'),
        detailMetric('新客成交客单价（任务商品）', newCustomerAov, 'money'),
        detailMetric('任务商品成交占比', safeRatio(orderProductGmv, merchantGmv), 'percent'),
        detailMetric('新访客占比', safeRatio(newCustomerVisitUv, shopVisitUv), 'percent'),
        detailMetric('新客成交GMV占比（任务商品）', safeRatio(orderProductNewCustomerGmv, orderProductGmv), 'percent'),
        detailMetric('小红星UV成交转化率', safeRatio(dealUv, shopVisitUv), 'percent'),
        detailMetric('小红星UV价值', safeRatio(merchantGmv, shopVisitUv), 'money'),
        detailMetric('成交客单价', dealAov, 'money'),
        detailMetric('店铺淘系成交占比', null, 'percent', '缺少店铺淘系总成交数据，暂不计算'),
        detailMetric('新客购买力', safeRatio(newCustomerAov, dealAov), 'decimal', '新客成交客单价 / 全店成交客单价', 2),
        detailMetric('全店成交ROI', safeRatio(merchantGmv, totalCost), 'decimal', '全店成交GMV / 总花费', 4),
        detailMetric('品牌淘系成交ROI', null, 'decimal', '缺少店铺淘系成交占比，暂不计算', 4),
      ],
    },
  ]
}

function rateValue(row, rateKey, numeratorKey, denominatorKey) {
  return row?.[rateKey] ?? safeRatio(row?.[numeratorKey], row?.[denominatorKey])
}

function buildDailyTotalRow(rows) {
  const total = {
    is_total: true,
    stat_date: '合计',
  }
  xhxDailySumFields.forEach((field) => {
    total[field] = rows.reduce((sum, row) => sum + toNumber(row[field]), 0)
  })
  total.collect_cart_uv = total.product_collect_uv + total.product_cart_uv
  total.interaction_rate = safeRatio(total.interaction_uv, total.read_play_uv)
  total.shop_visit_rate = safeRatio(total.shop_visit_uv, total.read_play_uv)
  total.new_customer_visit_rate = safeRatio(total.new_customer_visit_uv, total.shop_visit_uv)
  total.collect_cart_rate = safeRatio(total.collect_cart_uv, total.shop_visit_uv)
  total.deal_conversion_rate = safeRatio(total.deal_uv, total.shop_visit_uv)
  total.new_customer_deal_rate = safeRatio(total.new_customer_deal_uv, total.deal_uv)
  total.roi = safeRatio(total.merchant_gmv, total.total_cost)
  return total
}

function buildTaskGroupTotalRow(rows) {
  const total = {
    is_total: true,
    task_id: '合计',
    task_name: '全部任务组',
  }
  xhxTaskSumFields.forEach((field) => {
    total[field] = rows.reduce((sum, row) => sum + toNumber(row[field]), 0)
  })
  total.total_interaction = total.like_uv + total.collect_uv + total.comment_uv
  total.collect_cart_uv = total.product_collect_uv + total.product_cart_uv
  total.full_shop_gmv = total.merchant_gmv
  total.interaction_rate = safeRatio(total.interaction_uv, total.read_play_uv)
  total.avg_interaction_per_note = safeRatio(total.interaction_uv, total.note_count)
  total.cpm = safeRatio(total.total_cost, total.content_exposure, 1000)
  total.cpv = safeRatio(total.total_cost, total.read_play_uv)
  total.cpe = safeRatio(total.total_cost, total.interaction_uv)
  total.search_visit_rate = safeRatio(total.search_visit_uv, total.search_exposure_uv)
  total.collect_cart_rate = safeRatio(total.collect_cart_uv, total.shop_visit_uv)
  total.interaction_visit_rate = safeRatio(total.shop_visit_uv, total.interaction_uv)
  total.read_visit_rate = safeRatio(total.shop_visit_uv, total.read_play_uv)
  total.read_search_exposure_rate = safeRatio(total.search_exposure_uv, total.read_play_uv)
  total.interaction_search_exposure_rate = safeRatio(total.search_exposure_uv, total.interaction_uv)
  total.visit_uv_cost = safeRatio(total.total_cost, total.shop_visit_uv)
  total.deal_conversion_rate = safeRatio(total.deal_uv, total.shop_visit_uv)
  total.roi = safeRatio(total.merchant_gmv, total.total_cost)
  total.full_shop_roi = total.roi
  return total
}

function taskRowClassName(row) {
  return row?.is_total ? 'task-total-row' : ''
}

function formatPercent(value, digits = 1) {
  if (value === null || value === undefined || value === '') return '-'
  return `${(toNumber(value) * 100).toFixed(digits)}%`
}

function formatKpiDisplay(value, unit = '') {
  if (value === null || value === undefined || value === '') return '-'
  if (unit === '%') return formatPercent(value, 2)
  if (unit === '元') return formatMoney(value)
  return `${formatNumber(value, 2)}${unit ? ` ${unit}` : ''}`
}

function kpiStatusType(status) {
  if (status === 'achieved') return 'success'
  if (status === 'below_target') return 'warning'
  if (status === 'no_target') return 'default'
  return 'error'
}

function kpiDirectionLabel(direction) {
  return direction === 'lower_better' ? '越低越好' : '越高越好'
}

function toOptions(values = []) {
  return values.map((value) => ({ label: value, value }))
}

function sourceStatusLabel(status) {
  const labels = {
    success: '解析成功',
    partial_success: '部分成功',
    failed: '解析失败',
    pending: '待解析',
    missing: '未上传',
  }
  return labels[status] || status || '-'
}

function barWidth(value, max) {
  if (!max) return 0
  return Math.min(100, Math.round((toNumber(value) / max) * 100))
}

function keywordColor(index) {
  return keywordPalette[index % keywordPalette.length]
}

function breakdownMax(rows = []) {
  return Math.max(...rows.map((item) => toNumber(item.total_cost)), 1)
}
</script>

<template>
  <CommonPage show-footer title="红书数据看板">
    <div class="toolbar">
      <NSelect
        v-model:value="projectId"
        filterable
        :options="projectOptions"
        placeholder="选择项目"
        class="toolbar-project"
      />
      <NSelect
        v-model:value="productCategories"
        multiple
        filterable
        clearable
        :max-tag-count="1"
        :loading="productLoading"
        :options="productOptions"
        placeholder="全部产品"
        class="toolbar-product"
      />
      <NSelect
        v-model:value="taskGroupId"
        filterable
        clearable
        :disabled="!productCategories.length"
        :loading="taskGroupLoading"
        :options="taskGroupOptions"
        :placeholder="productCategories.length ? '全部任务组' : '请先选择产品'"
        class="toolbar-task-group"
      />
      <NDatePicker
        v-model:formatted-value="dateRange"
        type="daterange"
        value-format="yyyy-MM-dd"
        clearable
        class="toolbar-date"
      />
      <NButton type="primary" :loading="loading" @click="handleSearch">
        <TheIcon icon="material-symbols:search" :size="18" class="mr-5" />查询
      </NButton>
      <NButton type="warning" :loading="rebuilding" @click="handleRebuild">
        <TheIcon icon="material-symbols:sync" :size="18" class="mr-5" />重算
      </NButton>
    </div>

    <NTabs v-model:value="activeTab" type="line" animated>
      <NTabPane name="keyword-search" tab="红搜看板">
        <div class="filter-strip">
          <NSelect
            v-model:value="keywordFilters.selected_keywords"
            class="keyword-select"
            multiple
            filterable
            clearable
            :max-tag-count="3"
            :options="keywordFilterOptions.keyword"
            placeholder="选择参与统计的关键词"
          />
          <NInput v-model:value="keywordFilters.keyword" clearable placeholder="搜索关键词列表" />
          <NButton :loading="loading" @click="handleSearch">
            <TheIcon icon="material-symbols:filter-alt-outline" :size="18" class="mr-5" />筛选
          </NButton>
          <NButton quaternary @click="resetKeywordFilters">重置</NButton>
        </div>

        <NGrid :cols="4" :x-gap="12" :y-gap="12" responsive="screen" class="mb-16">
          <NGi v-for="item in keywordCards" :key="item.label">
            <div class="metric">
              <div class="metric-label">{{ item.label }}</div>
              <div class="metric-value">{{ item.value }}</div>
              <div class="metric-sub">{{ item.sub }}</div>
            </div>
          </NGi>
        </NGrid>

        <section class="panel mb-16">
          <div class="panel-head keyword-chart-head">
            <div>
              <h3>红搜趋势</h3>
              <span class="panel-note">按当前选择的关键词展示搜索指数走势</span>
            </div>
            <div class="legend selected-keyword-legend">
              <span v-for="(keywordItem, index) in selectedKeywordList" :key="keywordItem">
                <i class="dot" :style="{ background: keywordColor(index) }" />{{ keywordItem }}
              </span>
            </div>
          </div>
          <div v-if="!selectedKeywordList.length" class="empty-hint">请选择关键词后查看搜索趋势。</div>
          <div v-else-if="!keywordTrendChart.series.length" class="empty-chart">暂无红搜趋势数据</div>
          <div v-else class="keyword-chart-wrap">
            <svg class="keyword-chart" :viewBox="`0 0 ${keywordTrendChart.width} ${keywordTrendChart.height}`" role="img" aria-label="红搜趋势图">
              <g class="keyword-chart-grid">
                <g v-for="tick in keywordTrendChart.ticks" :key="tick.y">
                  <line :x1="keywordTrendChart.left" :x2="keywordTrendChart.width - keywordTrendChart.right" :y1="tick.y" :y2="tick.y" />
                  <text :x="keywordTrendChart.left - 8" :y="tick.y + 4">{{ tick.label }}</text>
                </g>
              </g>
              <g>
                <polyline
                  v-for="series in keywordTrendChart.series"
                  :key="series.keyword"
                  class="keyword-line"
                  :points="series.pointString"
                  :stroke="series.color"
                />
              </g>
              <g>
                <g v-for="series in keywordTrendChart.series" :key="`${series.keyword}-hit-points`">
                  <circle
                    v-for="(point, pointIndex) in series.points"
                    :key="`${series.keyword}-${point.stat_date}-${pointIndex}`"
                    class="keyword-hit-point"
                    :cx="point.x"
                    :cy="point.y"
                    r="6"
                  >
                    <title>{{ point.title }}</title>
                  </circle>
                </g>
              </g>
              <g>
                <text
                  v-for="label in keywordTrendChart.labels"
                  :key="label.x"
                  class="keyword-axis-label"
                  :x="label.x"
                  :y="keywordTrendChart.height - 20"
                >
                  {{ label.label }}
                </text>
              </g>
            </svg>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <h3>关键词排行</h3>
          </div>
          <NDataTable
            :loading="loading"
            :columns="keywordColumns"
            :data="keywordRows"
            :pagination="{ pageSize: 12 }"
            :scroll-x="1000"
          />
        </section>
      </NTabPane>

      <NTabPane name="xiaohongxing" tab="小红星看板">
        <NGrid :cols="4" :x-gap="12" :y-gap="12" responsive="screen" class="mb-16">
          <NGi v-for="item in xhxCards" :key="item.label">
            <div class="metric">
              <div class="metric-label">{{ item.label }}</div>
              <div class="metric-value">{{ item.value }}</div>
              <div class="metric-sub">{{ item.sub }}</div>
            </div>
          </NGi>
        </NGrid>

        <section class="panel mb-16">
          <div class="panel-head">
            <h3>详细指标</h3>
            <span class="panel-note">按原表“小红星-详细看板”指标分类重组，展示系统重算实际值</span>
          </div>
          <NTabs v-model:value="xhxDetailActiveTab" type="segment" animated class="detail-tabs">
            <NTabPane v-for="group in xhxDetailGroups" :key="group.title" :name="group.title" :tab="group.title">
              <div class="detail-tab-layout">
                <div class="detail-tab-head">
                  <strong>{{ group.title }}</strong>
                  <span>{{ group.note }}</span>
                </div>

                <div class="detail-focus-grid">
                  <div v-for="item in detailPrimaryItems(group)" :key="item.label" class="detail-focus-item">
                    <span class="detail-focus-label">{{ item.label }}</span>
                    <strong class="detail-focus-value">{{ formatDetailValue(item) }}</strong>
                    <em v-if="item.definition" class="detail-focus-note" :title="item.definition">{{ item.definition }}</em>
                  </div>
                </div>

                <div v-if="detailSecondaryItems(group).length" class="detail-table">
                  <div v-for="item in detailSecondaryItems(group)" :key="item.label" class="detail-table-row">
                    <div class="detail-label">
                      <strong>{{ item.label }}</strong>
                      <em v-if="item.definition" :title="item.definition">{{ item.definition }}</em>
                    </div>
                    <span class="detail-value">{{ formatDetailValue(item) }}</span>
                  </div>
                </div>
              </div>
            </NTabPane>
          </NTabs>
        </section>

        <div
          v-if="xhxMissingMappings.unmatched_order_count || xhxMissingMappings.unmatched_note_count"
          class="mapping-alert mb-16"
        >
          未匹配订单 {{ formatNumber(xhxMissingMappings.unmatched_order_count) }} 个，未匹配笔记
          {{ formatNumber(xhxMissingMappings.unmatched_note_count) }} 个；未匹配数据已保留在未归类分组，不会被强行分摊。
        </div>

        <div class="dashboard-grid mb-16">
          <section class="panel">
            <div class="panel-head">
              <h3>搜索承接趋势</h3>
            </div>
            <div class="trend-bars">
              <div v-for="row in xhxSearchTrend" :key="row.stat_date" class="trend-row">
                <div class="trend-date">{{ row.stat_date }}</div>
                <div class="trend-track">
                  <div class="trend-bar search" :style="{ width: `${barWidth(row.search_exposure_uv, xhxSearchMax)}%` }" />
                  <div class="trend-bar visit" :style="{ width: `${barWidth(row.search_visit_uv, xhxSearchMax)}%` }" />
                  <div class="trend-bar shop" :style="{ width: `${barWidth(row.shop_visit_uv, xhxSearchMax)}%` }" />
                </div>
                <div class="trend-value">{{ formatNumber(row.shop_visit_uv) }}</div>
              </div>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <h3>成交趋势</h3>
            </div>
            <div class="trend-bars">
              <div v-for="row in xhxGmvTrend" :key="row.stat_date" class="trend-row">
                <div class="trend-date">{{ row.stat_date }}</div>
                <div class="trend-track">
                  <div class="trend-bar gmv" :style="{ width: `${barWidth(row.merchant_gmv, xhxGmvMax)}%` }" />
                </div>
                <div class="trend-value">{{ formatMoney(row.merchant_gmv) }}</div>
              </div>
            </div>
          </section>
        </div>

        <section class="panel mb-16">
          <div class="panel-head">
            <h3>数据源状态</h3>
          </div>
          <NDataTable
            :columns="xhxSourceColumns"
            :data="xhxSourceStatus"
            :pagination="false"
            :scroll-x="700"
          />
        </section>

        <section class="panel mb-16">
          <div class="panel-head">
            <h3>小红星分日数据</h3>
          </div>
          <NDataTable
            :loading="loading"
            :columns="xhxDailyColumns"
            :data="xhxDailyRowsWithTotal"
            :pagination="{ pageSize: 10 }"
            :row-class-name="taskRowClassName"
            :scroll-x="3900"
          />
        </section>

        <section class="panel">
          <div class="panel-head">
            <h3>任务组数据</h3>
          </div>
          <NDataTable
            :loading="loading"
            :columns="xhxTaskColumns"
            :data="xhxTaskGroupsWithTotal"
            :pagination="{ pageSize: 10 }"
            :row-class-name="taskRowClassName"
            :scroll-x="5600"
          />
        </section>
      </NTabPane>

      <NTabPane name="planting" tab="种草投流">
        <div class="filter-strip">
          <NSelect
            v-model:value="plantingFilters.product_category"
            clearable
            :disabled="productCategories.length > 0"
            :options="plantingFilterOptions.product_category"
            :placeholder="productCategories.length ? '已使用顶部产品筛选' : '产品'"
          />
          <NSelect v-model:value="plantingFilters.blogger_type" clearable :options="plantingFilterOptions.blogger_type" placeholder="达人类型" />
          <NSelect v-model:value="plantingFilters.note_type" clearable :options="plantingFilterOptions.note_type" placeholder="笔记类型" />
          <NSelect v-model:value="plantingFilters.content_direction" clearable :options="plantingFilterOptions.content_direction" placeholder="内容方向" />
          <NInput v-model:value="plantingFilters.keyword" clearable placeholder="搜索笔记 ID / 达人 / 内容" />
          <NButton :loading="loading" @click="handleSearch">
            <TheIcon icon="material-symbols:filter-alt-outline" :size="18" class="mr-5" />筛选
          </NButton>
          <NButton quaternary @click="resetPlantingFilters">重置</NButton>
        </div>

        <NGrid :cols="4" :x-gap="12" :y-gap="12" responsive="screen" class="mb-16">
          <NGi v-for="item in plantingCards" :key="item.label">
            <div class="metric">
              <div class="metric-label">{{ item.label }}</div>
              <div class="metric-value">{{ item.value }}</div>
              <div class="metric-sub">{{ item.sub }}</div>
            </div>
          </NGi>
        </NGrid>

        <section class="panel mb-16">
          <div class="panel-head cost-chart-head">
            <div>
              <h3>花费拆分趋势</h3>
              <span class="panel-note">总花费 = 笔记花费 + 投流花费，按当前筛选条件重新聚合</span>
            </div>
            <div class="cost-chart-actions">
              <NButtonGroup>
                <NButton
                  v-for="item in [
                    { label: '分日', value: 'day' },
                    { label: '分周', value: 'week' },
                    { label: '分月', value: 'month' },
                  ]"
                  :key="item.value"
                  size="small"
                  :type="plantingCostGranularity === item.value ? 'primary' : 'default'"
                  @click="plantingCostGranularity = item.value"
                >
                  {{ item.label }}
                </NButton>
              </NButtonGroup>
            </div>
          </div>

          <div class="cost-summary-grid">
            <div v-for="item in plantingCostSummary" :key="item.label" class="cost-summary-item">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <em>{{ item.sub }}</em>
            </div>
          </div>

          <div class="cost-chart-wrap">
            <div v-if="!plantingCostChart.bars.length" class="empty-chart">暂无费用趋势数据</div>
            <svg v-else class="cost-chart" :viewBox="`0 0 ${plantingCostChart.width} ${plantingCostChart.height}`" role="img" aria-label="花费拆分趋势图">
              <g class="cost-chart-grid">
                <g v-for="tick in plantingCostChart.ticks" :key="tick.y">
                  <line :x1="plantingCostChart.left" :x2="plantingCostChart.width - plantingCostChart.right" :y1="tick.y" :y2="tick.y" />
                  <text :x="plantingCostChart.left - 8" :y="tick.y + 4">{{ tick.label }}</text>
                </g>
              </g>
              <g>
                <g v-for="bar in plantingCostChart.bars" :key="bar.key">
                  <title>{{ bar.title }}</title>
                  <rect class="cost-bar-note" :x="bar.x" :y="bar.noteY" :width="bar.barWidth" :height="bar.noteHeight" rx="4" />
                  <rect class="cost-bar-ad" :x="bar.x" :y="bar.adY" :width="bar.barWidth" :height="bar.adHeight" rx="4" />
                  <text v-if="bar.showLabel" class="cost-axis-label" :x="bar.totalX" :y="plantingCostChart.height - 16">{{ bar.label }}</text>
                </g>
              </g>
              <polyline v-if="plantingCostChart.totalLine" class="cost-total-line" :points="plantingCostChart.totalLine" />
            </svg>
          </div>

          <div class="legend cost-chart-legend">
            <span><i class="dot note" />笔记花费</span>
            <span><i class="dot ad" />投流花费</span>
            <span><i class="dot total" />总花费走势</span>
          </div>
        </section>

        <section class="panel mb-16">
          <div class="panel-head">
            <div>
              <h3>投流成本效率</h3>
              <span class="panel-note">跟踪 CPC / CPM / CPE 等成本指标，并定位高消耗与低效率笔记</span>
            </div>
          </div>
          <NTabs v-model:value="adEfficiencyTab" type="segment" animated class="ad-efficiency-tabs">
            <NTabPane name="cost-trend" tab="成本趋势">
              <div class="ad-mini-grid">
                <div v-for="chart in adCostMetricCharts" :key="chart.key" class="ad-mini-card">
                  <div class="ad-mini-head">
                    <div>
                      <span>{{ chart.label }}</span>
                      <em>{{ chart.desc }}</em>
                    </div>
                    <strong>{{ formatMoney(chart.latest) }}</strong>
                  </div>
                  <svg class="ad-mini-chart" :viewBox="`0 0 ${chart.width} ${chart.height}`" role="img" :aria-label="`${chart.label}趋势`">
                    <line class="ad-mini-baseline" :x1="0" :x2="chart.width" :y1="chart.baseline" :y2="chart.baseline" />
                    <polyline v-if="chart.pointString" class="ad-mini-line" :points="chart.pointString" :stroke="chart.color" />
                  </svg>
                  <div class="ad-mini-foot">
                    <span>均值 {{ formatMoney(chart.avg) }}</span>
                    <span>峰值 {{ formatMoney(chart.max) }}</span>
                  </div>
                </div>
              </div>
            </NTabPane>

            <NTabPane name="volume" tab="量效关系">
              <div class="ad-volume-head">
                <NButtonGroup>
                  <NButton
                    v-for="item in adVolumeModes"
                    :key="item.value"
                    size="small"
                    :type="adVolumeMode === item.value ? 'primary' : 'default'"
                    @click="adVolumeMode = item.value"
                  >
                    {{ item.label }}
                  </NButton>
                </NButtonGroup>
              </div>
              <div class="ad-volume-summary">
                <div v-for="item in adVolumeSummary" :key="item.label" class="ad-volume-summary-item">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                  <em>{{ item.sub }}</em>
                </div>
              </div>
              <div class="ad-volume-chart-wrap">
                <div v-if="!adVolumeChart.bars.length" class="empty-chart">暂无投流量效数据</div>
                <svg v-else class="ad-volume-chart" :viewBox="`0 0 ${adVolumeChart.width} ${adVolumeChart.height}`" role="img" aria-label="投流量效关系图">
                  <g class="ad-volume-grid">
                    <g v-for="tick in adVolumeChart.ticks" :key="tick.y">
                      <line :x1="adVolumeChart.left" :x2="adVolumeChart.width - adVolumeChart.right" :y1="tick.y" :y2="tick.y" />
                      <text class="ad-volume-cost-tick" :x="adVolumeChart.left - 8" :y="tick.y + 4">{{ tick.label }}</text>
                    </g>
                    <g v-for="tick in adVolumeChart.volumeTicks" :key="`v-${tick.y}`">
                      <text class="ad-volume-count-tick" :x="adVolumeChart.width - adVolumeChart.right + 8" :y="tick.y + 4">{{ tick.label }}</text>
                    </g>
                  </g>
                  <g>
                    <g v-for="bar in adVolumeChart.bars" :key="bar.key">
                      <title>{{ bar.title }}</title>
                      <rect class="ad-volume-bar" :x="bar.x" :y="bar.y" :width="bar.width" :height="bar.height" rx="4" />
                      <text v-if="bar.showLabel" class="ad-volume-axis-label" :x="bar.lineX" :y="adVolumeChart.height - 16">{{ bar.label }}</text>
                    </g>
                  </g>
                  <polyline class="ad-volume-line" :points="adVolumeChart.linePoints" :stroke="adVolumeChart.color" />
                </svg>
              </div>
              <div class="legend cost-chart-legend">
                <span><i class="dot ad" />投流消耗</span>
                <span><i class="dot" :style="{ background: activeAdVolumeMode.color }" />{{ activeAdVolumeMode.volumeLabel }}</span>
              </div>
            </NTabPane>

            <NTabPane name="ranking" tab="笔记效率排行">
              <div class="ad-rank-grid">
                <div class="ad-rank-panel">
                  <div class="ad-rank-head">
                    <strong>高消耗笔记</strong>
                    <span>按投流消耗排序</span>
                  </div>
                  <div v-if="!highCostNotes.length" class="empty-hint">暂无投流消耗笔记。</div>
                  <div v-else class="ad-rank-list">
                    <div v-for="row in highCostNotes" :key="row.note_id" class="ad-rank-row">
                      <div class="ad-rank-main">
                        <strong>{{ noteDisplayName(row) }}</strong>
                        <span>{{ noteDisplaySub(row) }}</span>
                      </div>
                      <div class="ad-rank-value">{{ formatMoney(row.ad_cost) }}</div>
                      <div class="ad-rank-progress"><i :style="{ width: `${barWidth(row.ad_cost, highCostNoteMax)}%` }" /></div>
                      <div class="ad-rank-sub">曝光 {{ formatNumber(row.impressions) }} · 点击 {{ formatNumber(row.clicks) }} · 互动 {{ formatNumber(row.interactions) }}</div>
                    </div>
                  </div>
                </div>

                <div class="ad-rank-panel">
                  <div class="ad-rank-head">
                    <strong>CPE偏高笔记</strong>
                    <span>按单次互动成本排序</span>
                  </div>
                  <div v-if="!highCpeNotes.length" class="empty-hint">暂无可计算 CPE 的笔记。</div>
                  <div v-else class="ad-rank-list">
                    <div v-for="row in highCpeNotes" :key="row.note_id" class="ad-rank-row">
                      <div class="ad-rank-main">
                        <strong>{{ noteDisplayName(row) }}</strong>
                        <span>{{ noteDisplaySub(row) }}</span>
                      </div>
                      <div class="ad-rank-value">{{ formatMoney(row.cpe) }}</div>
                      <div class="ad-rank-progress warning"><i :style="{ width: `${barWidth(row.cpe, highCpeNoteMax)}%` }" /></div>
                      <div class="ad-rank-sub">消耗 {{ formatMoney(row.ad_cost) }} · 互动 {{ formatNumber(row.interactions) }} · 搜索组件 {{ formatNumber(row.search_component_clicks) }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </NTabPane>
          </NTabs>
        </section>

        <div class="dashboard-grid mb-16">
          <section class="panel">
            <div class="panel-head">
              <h3>产品透视</h3>
            </div>
            <div class="breakdown-list">
              <div v-for="row in planting.breakdowns.product_category" :key="row.name" class="breakdown-row">
                <div class="breakdown-top">
                  <span>{{ row.name }}</span>
                  <strong>{{ formatMoney(row.total_cost) }}</strong>
                </div>
                <div class="progress"><i :style="{ width: `${barWidth(row.total_cost, productMax)}%` }" /></div>
                <div class="breakdown-sub">曝光 {{ formatNumber(row.impressions) }} · 互动 {{ formatNumber(row.interactions) }}</div>
              </div>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <h3>达人类型透视</h3>
            </div>
            <div class="breakdown-list">
              <div v-for="row in planting.breakdowns.blogger_type" :key="row.name" class="breakdown-row">
                <div class="breakdown-top">
                  <span>{{ row.name }}</span>
                  <strong>{{ formatMoney(row.total_cost) }}</strong>
                </div>
                <div class="progress green"><i :style="{ width: `${barWidth(row.total_cost, bloggerMax)}%` }" /></div>
                <div class="breakdown-sub">笔记 {{ formatNumber(row.note_count) }} · CPE {{ formatMoney(row.cpe) }}</div>
              </div>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <h3>内容方向透视</h3>
            </div>
            <div class="breakdown-list compact">
              <div v-for="row in planting.breakdowns.content_direction" :key="row.name" class="breakdown-row">
                <div class="breakdown-top">
                  <span>{{ row.name }}</span>
                  <strong>{{ formatMoney(row.total_cost) }}</strong>
                </div>
                <div class="progress amber"><i :style="{ width: `${barWidth(row.total_cost, directionMax)}%` }" /></div>
              </div>
            </div>
          </section>
        </div>

        <section class="panel mb-16">
          <div class="panel-head">
            <h3>分日数据</h3>
          </div>
          <NDataTable
            :loading="loading"
            :columns="dailyColumns"
            :data="plantingTrend"
            :pagination="{ pageSize: 10 }"
            :scroll-x="1360"
          />
        </section>

        <section class="panel">
          <div class="panel-head">
            <h3>笔记明细</h3>
          </div>
          <NDataTable
            :loading="loading"
            :columns="noteColumns"
            :data="plantingNotes"
            :pagination="{ pageSize: 10 }"
            :scroll-x="1900"
          />
        </section>
      </NTabPane>

      <NTabPane name="kpi" tab="KPI看板">
        <NGrid :cols="4" :x-gap="12" :y-gap="12" responsive="screen" class="mb-16">
          <NGi v-for="item in kpiCards" :key="item.label">
            <div class="metric">
              <div class="metric-label">{{ item.label }}</div>
              <div class="metric-value">{{ item.value }}</div>
              <div class="metric-sub">{{ item.sub }}</div>
            </div>
          </NGi>
        </NGrid>

        <div v-if="!kpiProgress.configured" class="empty-hint mb-16">
          当前项目周期未配置 KPI。请先在左侧“KPI配置”中选择系统指标并设置目标值、权重和方向。
        </div>

        <div v-else class="kpi-layout">
          <section class="panel">
            <div class="panel-head">
              <div>
                <h3>KPI达成概览</h3>
                <span class="panel-note">按当前项目、周期和日期筛选实时计算</span>
              </div>
              <span class="score-text">达成率 {{ formatPercent(kpiProgress.score_rate, 1) }}</span>
            </div>
            <div class="kpi-score-card">
              <div class="kpi-score-main">
                <span>当前得分</span>
                <strong>{{ formatNumber(kpiProgress.total_score, 2) }}</strong>
                <em>可得权重 {{ formatNumber(kpiProgress.total_weight, 2) }} / 配置权重 {{ formatNumber(kpiProgress.configured_weight, 2) }}</em>
              </div>
              <div class="kpi-score-track">
                <i :style="{ width: `${barWidth(kpiProgress.total_score, kpiProgress.total_weight)}%` }" />
              </div>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <h3>短板项</h3>
                <span class="panel-note">按分值缺口排序，优先处理未达标指标</span>
              </div>
            </div>
            <div v-if="!kpiWeakItems.length" class="empty-chart">暂无未达标 KPI</div>
            <div v-else class="kpi-weak-list">
              <div v-for="item in kpiWeakItems" :key="item.id" class="kpi-weak-item">
                <div>
                  <strong>{{ item.kpi_name }}</strong>
                  <span>{{ item.source }} / {{ item.category }}</span>
                </div>
                <em>缺口 {{ formatNumber(item.score_gap, 2) }} 分</em>
                <i>实际 {{ formatKpiDisplay(item.actual_value, item.unit) }} / 目标 {{ formatKpiDisplay(item.target_value, item.unit) }}</i>
              </div>
            </div>
          </section>

          <section class="panel kpi-detail-panel">
            <div class="panel-head">
              <div>
                <h3>KPI明细</h3>
                <span class="panel-note">实际值来自当前已完成的种草投流、小红星、红搜和融合总览看板口径</span>
              </div>
            </div>
            <NDataTable
              :loading="loading"
              :columns="kpiDetailColumns"
              :data="kpiProgress.items"
              :pagination="{ pageSize: 10 }"
              :scroll-x="1400"
            />
          </section>
        </div>
      </NTabPane>

      <NTabPane name="combined" tab="融合总览">
        <NGrid :cols="4" :x-gap="12" :y-gap="12" responsive="screen" class="mb-16">
          <NGi v-for="item in overviewCoreCards" :key="item.label">
            <div class="metric overview-metric" :class="`overview-metric-${item.tone}`">
              <div class="metric-label">{{ item.label }}</div>
              <div class="metric-value">{{ item.value }}</div>
              <div class="metric-sub">{{ item.sub }}</div>
            </div>
          </NGi>
        </NGrid>

        <section class="panel mb-16">
          <div class="panel-head">
            <div>
              <h3>全链路漏斗</h3>
              <span class="panel-note">从内容触达到搜索声量、淘系承接和成交结果的融合视角</span>
            </div>
          </div>
          <div class="overview-funnel">
            <div v-for="(item, index) in overviewFunnelItems" :key="item.label" class="overview-funnel-step" :class="`overview-funnel-${item.tone}`">
              <div class="overview-funnel-index">{{ index + 1 }}</div>
              <div class="overview-funnel-body">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
                <em>{{ item.sub }}</em>
                <i>{{ item.source }}</i>
              </div>
            </div>
          </div>
        </section>

        <section class="panel mb-16">
          <div class="panel-head overview-trend-head">
            <div>
              <h3>费用与结果趋势</h3>
              <span class="panel-note">柱状为笔记/投流花费，折线为当前选择的结果指标</span>
            </div>
            <NButtonGroup>
              <NButton
                v-for="item in overviewTrendModes"
                :key="item.value"
                size="small"
                :type="overviewTrendMode === item.value ? 'primary' : 'default'"
                @click="overviewTrendMode = item.value"
              >
                {{ item.label }}
              </NButton>
            </NButtonGroup>
          </div>

          <div class="overview-trend-summary">
            <div v-for="item in overviewTrendSummary" :key="item.label" class="overview-trend-summary-item">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <em>{{ item.sub }}</em>
            </div>
          </div>

          <div class="overview-chart-wrap">
            <div v-if="!overviewTrendChart.bars.length" class="empty-chart">暂无总览趋势数据</div>
            <svg v-else class="overview-chart" :viewBox="`0 0 ${overviewTrendChart.width} ${overviewTrendChart.height}`" role="img" aria-label="费用与结果趋势图">
              <g class="overview-chart-grid">
                <g v-for="tick in overviewTrendChart.ticks" :key="tick.y">
                  <line :x1="overviewTrendChart.left" :x2="overviewTrendChart.width - overviewTrendChart.right" :y1="tick.y" :y2="tick.y" />
                  <text class="overview-cost-tick" :x="overviewTrendChart.left - 8" :y="tick.y + 4">{{ tick.label }}</text>
                </g>
                <g v-for="tick in overviewTrendChart.resultTicks" :key="`r-${tick.y}`">
                  <text class="overview-result-tick" :x="overviewTrendChart.width - overviewTrendChart.right + 8" :y="tick.y + 4">{{ tick.label }}</text>
                </g>
              </g>
              <g>
                <g v-for="bar in overviewTrendChart.bars" :key="bar.stat_date">
                  <title>{{ bar.title }}</title>
                  <rect class="cost-bar-note" :x="bar.x" :y="bar.noteY" :width="bar.width" :height="bar.noteHeight" rx="4" />
                  <rect class="cost-bar-ad" :x="bar.x" :y="bar.adY" :width="bar.width" :height="bar.adHeight" rx="4" />
                  <text v-if="bar.showLabel" class="overview-axis-label" :x="bar.lineX" :y="overviewTrendChart.height - 16">{{ bar.label }}</text>
                </g>
              </g>
              <polyline class="overview-result-line" :points="overviewTrendChart.resultLine" :stroke="activeOverviewTrendMode.color" />
            </svg>
          </div>
          <div class="legend cost-chart-legend">
            <span><i class="dot note" />笔记费用</span>
            <span><i class="dot ad" />投流费用</span>
            <span><i class="dot" :style="{ background: activeOverviewTrendMode.color }" />{{ activeOverviewTrendMode.resultLabel }}</span>
          </div>
        </section>

        <div class="overview-bottom-grid">
          <section class="panel">
            <div class="panel-head">
              <div>
                <h3>数据健康状态</h3>
                <span class="panel-note">判断当前总览数据是否具备可信基础</span>
              </div>
            </div>
            <div class="overview-source-grid">
              <div v-for="item in overviewSourceCards" :key="item.label" class="overview-source-card" :class="`overview-source-${item.tone}`">
                <div class="overview-source-head">
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.status }}</span>
                </div>
                <em>{{ item.sub }}</em>
                <i :title="item.file">{{ item.file }}</i>
              </div>
            </div>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div>
                <h3>关键诊断</h3>
                <span class="panel-note">不替代 KPI，仅提示当前数据事实和下钻方向</span>
              </div>
            </div>
            <div class="overview-diagnosis-list">
              <div v-for="item in overviewDiagnostics" :key="item.title" class="overview-diagnosis-card" :class="`overview-diagnosis-${item.tone}`">
                <div class="overview-diagnosis-main">
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.value }}</span>
                  <em>{{ item.desc }}</em>
                </div>
                <NButton v-if="item.target" size="tiny" text type="primary" @click="activeTab = item.target">
                  {{ item.action }}
                </NButton>
              </div>
            </div>
          </section>
        </div>
      </NTabPane>
    </NTabs>
  </CommonPage>
</template>

<style scoped>
.toolbar,
.filter-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.toolbar-project {
  width: 320px;
}

.toolbar-product {
  width: 220px;
}

.toolbar-task-group {
  width: 220px;
}

.toolbar-date {
  width: 260px;
}

.filter-strip :deep(.n-select) {
  width: 160px;
}

.filter-strip .keyword-select {
  width: min(420px, 100%);
  min-width: 320px;
}

.filter-strip :deep(.n-input) {
  width: 240px;
}

@media (max-width: 720px) {
  .filter-strip .keyword-select,
  .filter-strip :deep(.n-input) {
    width: 100%;
    min-width: 0;
  }
}

:deep(.task-total-row td) {
  font-weight: 600;
  background: #fff7ed;
}

.metric {
  min-height: 92px;
  padding: 14px 16px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background: var(--n-color);
}

.metric-label,
.funnel-label,
.metric-sub,
.breakdown-sub {
  font-size: 13px;
  color: var(--n-text-color-3);
}

.metric-value {
  margin-top: 8px;
  font-size: 24px;
  font-weight: 700;
  color: var(--n-text-color-1);
}

.metric-sub {
  margin-top: 6px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(320px, .6fr);
  gap: 12px;
}

.dashboard-grid:has(.panel:nth-child(3)) {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.panel {
  min-width: 0;
  padding: 14px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background: var(--n-color);
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.panel-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.panel-note {
  color: var(--n-text-color-3);
  font-size: 12px;
}

.overview-metric {
  position: relative;
  overflow: hidden;
}

.overview-metric::before {
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  content: '';
  background: #64748b;
}

.overview-metric-cost::before {
  background: #f97316;
}

.overview-metric-content::before {
  background: #2563eb;
}

.overview-metric-search::before {
  background: #e11d48;
}

.overview-metric-visit::before {
  background: #16a34a;
}

.overview-metric-gmv::before {
  background: #dc2626;
}

.overview-funnel {
  display: grid;
  grid-template-columns: repeat(9, minmax(132px, 1fr));
  gap: 10px;
  overflow-x: auto;
}

.overview-funnel-step {
  position: relative;
  min-width: 0;
  min-height: 132px;
  padding: 12px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background: rgba(100, 116, 139, .05);
}

.overview-funnel-index {
  display: grid;
  width: 24px;
  height: 24px;
  margin-bottom: 10px;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  background: #64748b;
}

.overview-funnel-content .overview-funnel-index {
  background: #2563eb;
}

.overview-funnel-search .overview-funnel-index {
  background: #e11d48;
}

.overview-funnel-visit .overview-funnel-index {
  background: #16a34a;
}

.overview-funnel-deal .overview-funnel-index {
  background: #dc2626;
}

.overview-funnel-body span,
.overview-funnel-body em,
.overview-funnel-body i,
.overview-trend-summary-item span,
.overview-trend-summary-item em,
.overview-source-card em,
.overview-source-card i,
.overview-diagnosis-card em {
  display: block;
  color: var(--n-text-color-3);
  font-size: 12px;
  font-style: normal;
}

.overview-funnel-body strong {
  display: block;
  margin: 7px 0 5px;
  color: var(--n-text-color-1);
  font-size: 19px;
  font-weight: 700;
  line-height: 1.2;
}

.overview-trend-head {
  align-items: flex-start;
}

.overview-trend-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.overview-trend-summary-item {
  min-height: 74px;
  padding: 10px 12px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background: rgba(100, 116, 139, .06);
}

.overview-trend-summary-item strong {
  display: block;
  margin: 7px 0 5px;
  color: var(--n-text-color-1);
  font-size: 20px;
  font-weight: 700;
}

.overview-chart-wrap {
  min-height: 300px;
  overflow-x: auto;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(248, 250, 252, .9), rgba(255, 255, 255, .98));
}

.overview-chart {
  display: block;
  width: 100%;
  min-width: 760px;
  height: auto;
}

.overview-chart-grid line {
  stroke: rgba(148, 163, 184, .28);
  stroke-width: 1;
}

.overview-chart-grid text {
  fill: var(--n-text-color-3);
  font-size: 12px;
}

.overview-cost-tick {
  text-anchor: end;
}

.overview-result-tick {
  text-anchor: start;
}

.overview-result-line {
  fill: none;
  stroke-width: 2.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.overview-axis-label {
  fill: var(--n-text-color-3);
  font-size: 12px;
  text-anchor: middle;
}

.overview-bottom-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(360px, .92fr);
  gap: 12px;
}

.overview-source-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.overview-source-card {
  min-width: 0;
  min-height: 92px;
  padding: 10px 12px;
  border: 1px solid var(--n-border-color);
  border-left-width: 4px;
  border-radius: 8px;
}

.overview-source-ok {
  border-left-color: #16a34a;
}

.overview-source-warn {
  border-left-color: #f59e0b;
}

.overview-source-bad {
  border-left-color: #dc2626;
}

.overview-source-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.overview-source-head strong {
  min-width: 0;
  overflow: hidden;
  color: var(--n-text-color-1);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.overview-source-head span {
  flex: 0 0 auto;
  color: var(--n-text-color-2);
  font-size: 12px;
}

.overview-source-card i {
  margin-top: 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.overview-diagnosis-list {
  display: grid;
  gap: 10px;
}

.overview-diagnosis-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 84px;
  padding: 10px 12px;
  border: 1px solid var(--n-border-color);
  border-left-width: 4px;
  border-radius: 8px;
}

.overview-diagnosis-ok {
  border-left-color: #16a34a;
}

.overview-diagnosis-warn {
  border-left-color: #f59e0b;
}

.overview-diagnosis-bad {
  border-left-color: #dc2626;
}

.overview-diagnosis-main {
  min-width: 0;
}

.overview-diagnosis-card strong,
.overview-diagnosis-card span {
  display: block;
}

.overview-diagnosis-card strong {
  color: var(--n-text-color-1);
  font-size: 13px;
}

.overview-diagnosis-card span {
  margin: 5px 0 3px;
  color: var(--n-text-color-1);
  font-size: 16px;
  font-weight: 700;
}

.kpi-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, .9fr);
  gap: 12px;
}

.kpi-detail-panel {
  grid-column: 1 / -1;
}

.kpi-score-card {
  display: grid;
  gap: 14px;
  min-height: 154px;
  padding: 16px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background: rgba(14, 165, 233, .06);
}

.kpi-score-main {
  display: grid;
  gap: 6px;
}

.kpi-score-main span,
.kpi-score-main em {
  color: var(--n-text-color-2);
  font-size: 13px;
}

.kpi-score-main strong {
  color: var(--n-text-color-1);
  font-size: 34px;
  font-weight: 750;
  line-height: 1;
}

.kpi-score-track {
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(100, 116, 139, .16);
}

.kpi-score-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #0ea5e9, #16a34a);
}

.kpi-weak-list {
  display: grid;
  gap: 10px;
  max-height: 300px;
  overflow: auto;
}

.kpi-weak-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 4px 12px;
  padding: 10px 12px;
  border: 1px solid rgba(245, 158, 11, .28);
  border-radius: 8px;
  background: rgba(245, 158, 11, .06);
}

.kpi-weak-item strong,
.kpi-weak-item span,
.kpi-weak-item em,
.kpi-weak-item i {
  display: block;
}

.kpi-weak-item strong {
  overflow: hidden;
  color: var(--n-text-color-1);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kpi-weak-item span,
.kpi-weak-item i {
  color: var(--n-text-color-2);
  font-size: 12px;
}

.kpi-weak-item em {
  color: #d97706;
  font-size: 13px;
  font-style: normal;
  font-weight: 700;
  white-space: nowrap;
}

.kpi-weak-item i {
  grid-column: 1 / -1;
  font-style: normal;
}

.cost-chart-head {
  align-items: flex-start;
}

.cost-chart-actions {
  flex: 0 0 auto;
}

.cost-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.cost-summary-item {
  min-width: 0;
  min-height: 76px;
  padding: 10px 12px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background: rgba(100, 116, 139, .06);
}

.cost-summary-item span,
.cost-summary-item em {
  display: block;
  color: var(--n-text-color-3);
  font-size: 12px;
  font-style: normal;
}

.cost-summary-item strong {
  display: block;
  margin: 7px 0 5px;
  color: var(--n-text-color-1);
  font-size: 20px;
  font-weight: 700;
}

.cost-chart-wrap {
  min-height: 280px;
  overflow-x: auto;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(248, 250, 252, .9), rgba(255, 255, 255, .98));
}

.cost-chart {
  display: block;
  width: 100%;
  min-width: 720px;
  height: auto;
}

.cost-chart-grid line {
  stroke: rgba(148, 163, 184, .28);
  stroke-width: 1;
}

.cost-chart-grid text {
  fill: var(--n-text-color-3);
  font-size: 12px;
  text-anchor: end;
}

.cost-bar-note {
  fill: #f97316;
}

.cost-bar-ad {
  fill: #2563eb;
}

.cost-total-line {
  fill: none;
  stroke: #111827;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  opacity: .72;
}

.cost-axis-label {
  fill: var(--n-text-color-3);
  font-size: 12px;
  text-anchor: middle;
}

.cost-chart-legend {
  justify-content: flex-end;
  margin-top: 10px;
}

.empty-chart {
  display: grid;
  min-height: 280px;
  place-items: center;
  color: var(--n-text-color-3);
  font-size: 13px;
}

.keyword-chart-head {
  align-items: flex-start;
}

.selected-keyword-legend {
  justify-content: flex-end;
  max-width: 62%;
}

.keyword-chart-wrap {
  min-height: 300px;
  overflow-x: auto;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(248, 250, 252, .9), rgba(255, 255, 255, .98));
}

.keyword-chart {
  display: block;
  width: 100%;
  min-width: 760px;
  height: auto;
}

.keyword-chart-grid line {
  stroke: rgba(148, 163, 184, .28);
  stroke-width: 1;
}

.keyword-chart-grid text {
  fill: var(--n-text-color-3);
  font-size: 12px;
  text-anchor: end;
}

.keyword-line {
  fill: none;
  stroke-width: 2.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.keyword-hit-point {
  fill: transparent;
  stroke: transparent;
  pointer-events: all;
}

.keyword-axis-label {
  fill: var(--n-text-color-3);
  font-size: 12px;
  text-anchor: middle;
}

.ad-efficiency-tabs :deep(.n-tabs-nav) {
  margin-bottom: 12px;
}

.ad-mini-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.ad-mini-card {
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background: rgba(100, 116, 139, .05);
}

.ad-mini-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.ad-mini-head span,
.ad-mini-head em,
.ad-mini-foot,
.ad-volume-summary-item span,
.ad-volume-summary-item em,
.ad-rank-head span,
.ad-rank-main span,
.ad-rank-sub {
  color: var(--n-text-color-3);
  font-size: 12px;
  font-style: normal;
}

.ad-mini-head span,
.ad-mini-head em {
  display: block;
}

.ad-mini-head strong {
  color: var(--n-text-color-1);
  font-size: 16px;
  white-space: nowrap;
}

.ad-mini-chart {
  display: block;
  width: 100%;
  height: 72px;
  margin: 8px 0;
}

.ad-mini-baseline {
  stroke: rgba(148, 163, 184, .28);
  stroke-width: 1;
}

.ad-mini-line {
  fill: none;
  stroke-width: 2.4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.ad-mini-foot {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.ad-volume-head {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}

.ad-volume-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.ad-volume-summary-item {
  min-height: 74px;
  padding: 10px 12px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background: rgba(37, 99, 235, .06);
}

.ad-volume-summary-item span,
.ad-volume-summary-item em {
  display: block;
}

.ad-volume-summary-item strong {
  display: block;
  margin: 7px 0 5px;
  color: var(--n-text-color-1);
  font-size: 20px;
  font-weight: 700;
}

.ad-volume-chart-wrap {
  min-height: 300px;
  overflow-x: auto;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(248, 250, 252, .9), rgba(255, 255, 255, .98));
}

.ad-volume-chart {
  display: block;
  width: 100%;
  min-width: 760px;
  height: auto;
}

.ad-volume-grid line {
  stroke: rgba(148, 163, 184, .28);
  stroke-width: 1;
}

.ad-volume-grid text {
  fill: var(--n-text-color-3);
  font-size: 12px;
}

.ad-volume-cost-tick {
  text-anchor: end;
}

.ad-volume-count-tick {
  text-anchor: start;
}

.ad-volume-bar {
  fill: #2563eb;
  opacity: .72;
}

.ad-volume-line {
  fill: none;
  stroke-width: 2.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.ad-volume-axis-label {
  fill: var(--n-text-color-3);
  font-size: 12px;
  text-anchor: middle;
}

.ad-rank-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.ad-rank-panel {
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
}

.ad-rank-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.ad-rank-head strong,
.ad-rank-main strong {
  color: var(--n-text-color-1);
  font-size: 13px;
}

.ad-rank-list {
  display: grid;
  gap: 10px;
}

.ad-rank-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 6px 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--n-border-color);
}

.ad-rank-row:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.ad-rank-main {
  min-width: 0;
}

.ad-rank-main strong,
.ad-rank-main span {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ad-rank-value {
  color: var(--n-text-color-1);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.ad-rank-progress {
  grid-column: 1 / -1;
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(100, 116, 139, .16);
}

.ad-rank-progress i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #2563eb;
}

.ad-rank-progress.warning i {
  background: #f97316;
}

.ad-rank-sub {
  grid-column: 1 / -1;
}

.detail-tabs {
  min-width: 0;
}

.detail-tabs :deep(.n-tabs-nav) {
  margin-bottom: 12px;
}

.detail-tab-layout {
  display: grid;
  gap: 12px;
}

.detail-tab-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background: rgba(100, 116, 139, .06);
}

.detail-tab-head strong {
  color: var(--n-text-color-1);
  font-size: 15px;
  font-weight: 700;
}

.detail-tab-head span {
  color: var(--n-text-color-3);
  font-size: 12px;
  white-space: nowrap;
}

.detail-focus-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.detail-focus-item {
  min-width: 0;
  min-height: 86px;
  padding: 12px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background: var(--n-color);
}

.detail-focus-label,
.detail-focus-note {
  display: block;
  color: var(--n-text-color-3);
  font-size: 12px;
  font-style: normal;
}

.detail-focus-value {
  display: block;
  margin: 8px 0 4px;
  color: var(--n-text-color-1);
  font-size: 22px;
  font-weight: 700;
  line-height: 1.2;
}

.detail-focus-note {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-table {
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  overflow: hidden;
}

.detail-table-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(120px, auto);
  align-items: center;
  gap: 14px;
  min-height: 46px;
  padding: 8px 12px;
}

.detail-table-row + .detail-table-row {
  border-top: 1px solid var(--n-border-color);
}

.detail-label {
  min-width: 0;
}

.detail-label strong {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--n-text-color-1);
}

.detail-label em {
  display: block;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--n-text-color-3);
  font-style: normal;
  font-size: 12px;
}

.detail-value {
  font-weight: 700;
  color: var(--n-text-color-1);
  white-space: nowrap;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  color: var(--n-text-color-3);
  font-size: 12px;
}

.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 5px;
  border-radius: 50%;
}

.dot.note {
  background: #f97316;
}

.dot.ad {
  background: #2563eb;
}

.dot.total {
  background: #111827;
}

.dot.service {
  background: #64748b;
}

.dot.brand {
  background: #e11d48;
}

.dot.product {
  background: #f97316;
}

.dot.category {
  background: #0ea5e9;
}

.dot.competitor {
  background: #7c3aed;
}

.trend-bars {
  display: grid;
  gap: 8px;
  max-height: 340px;
  overflow: auto;
}

.trend-row {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr) 108px;
  gap: 10px;
  align-items: center;
  font-size: 12px;
}

.trend-track {
  display: grid;
  gap: 3px;
}

.trend-bar {
  height: 8px;
  min-width: 0;
  border-radius: 999px;
}

.trend-bar.note {
  background: #f97316;
}

.trend-bar.ad {
  background: #2563eb;
}

.trend-bar.service {
  background: #64748b;
}

.trend-bar.search {
  background: #7c3aed;
}

.trend-bar.visit {
  background: #0891b2;
}

.trend-bar.shop {
  background: #16a34a;
}

.trend-bar.gmv {
  background: #dc2626;
}

.trend-bar.brand {
  background: #e11d48;
}

.trend-bar.product {
  background: #f97316;
}

.trend-bar.category {
  background: #0ea5e9;
}

.trend-bar.competitor {
  background: #7c3aed;
}

.trend-value {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.breakdown-list {
  display: grid;
  gap: 12px;
}

.breakdown-list.compact {
  max-height: 290px;
  overflow: auto;
}

.breakdown-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}

.progress {
  height: 8px;
  margin: 8px 0 6px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(100, 116, 139, .16);
}

.progress i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #2563eb;
}

.progress.green i {
  background: #16a34a;
}

.progress.amber i {
  background: #f59e0b;
}

.section-title {
  margin: 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.funnel-item {
  min-height: 74px;
  padding: 12px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
}

.funnel-value {
  margin-top: 8px;
  font-size: 18px;
  font-weight: 600;
}

.mapping-alert,
.empty-hint {
  padding: 12px 14px;
  border: 1px solid rgba(245, 158, 11, .35);
  border-radius: 8px;
  background: rgba(245, 158, 11, .08);
  color: var(--n-text-color-2);
}

.score-text {
  color: var(--n-text-color-2);
  font-size: 13px;
  font-weight: 600;
}

@media (max-width: 1100px) {
  .ad-mini-grid,
  .ad-volume-summary,
  .ad-rank-grid,
  .cost-summary-grid,
  .detail-focus-grid,
  .dashboard-grid,
  .dashboard-grid:has(.panel:nth-child(3)),
  .kpi-layout,
  .overview-bottom-grid,
  .overview-source-grid,
  .overview-trend-summary {
    grid-template-columns: 1fr;
  }

  .cost-chart-head {
    flex-direction: column;
  }

  .keyword-chart-head {
    flex-direction: column;
  }

  .overview-trend-head {
    flex-direction: column;
  }

  .overview-trend-head :deep(.n-button-group) {
    width: 100%;
  }

  .overview-trend-head :deep(.n-button) {
    flex: 1;
  }

  .selected-keyword-legend {
    justify-content: flex-start;
    max-width: 100%;
  }

  .cost-chart-actions {
    width: 100%;
  }

  .cost-chart-actions :deep(.n-button-group) {
    width: 100%;
  }

  .cost-chart-actions :deep(.n-button) {
    flex: 1;
  }

  .ad-volume-head {
    justify-content: flex-start;
  }

  .ad-volume-head :deep(.n-button-group) {
    width: 100%;
  }

  .ad-volume-head :deep(.n-button) {
    flex: 1;
  }

  .overview-diagnosis-card {
    align-items: flex-start;
    flex-direction: column;
  }

  .detail-tab-head,
  .detail-table-row {
    align-items: flex-start;
    grid-template-columns: 1fr;
  }

  .detail-tab-head {
    flex-direction: column;
  }

  .detail-tab-head span {
    white-space: normal;
  }
}
</style>
