export const sourceTypeOptions = [
  { label: '聚光投流-创意报表', value: 'juguang' },
  { label: '蒲公英-笔记批量数据', value: 'pgy' },
  { label: '小红星-订单每日数据', value: 'xiaohongxing_order' },
  { label: '小红书搜索日报', value: 'keyword_search' },
  { label: '笔记匹配源', value: 'note_mapping' },
]

export const sourceTypeMap = sourceTypeOptions.reduce((map, item) => {
  map[item.value] = item.label
  return map
}, {})

export const projectStatusOptions = [
  { label: '启用', value: 'active' },
  { label: '停用', value: 'inactive' },
]

export const parseStatusOptions = [
  { label: '待解析', value: 'pending' },
  { label: '解析成功', value: 'success' },
  { label: '部分成功', value: 'partial_success' },
  { label: '解析失败', value: 'failed' },
]

export const parseStatusMap = parseStatusOptions.reduce((map, item) => {
  map[item.value] = item.label
  return map
}, {})

export const statusTypeMap = {
  active: 'success',
  inactive: 'warning',
  pending: 'default',
  success: 'success',
  partial_success: 'warning',
  failed: 'error',
}

export function formatNumber(value, fractionDigits = 0) {
  if (value === null || value === undefined || value === '') return '-'
  return Number(value).toLocaleString('zh-CN', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })
}

export function formatMoney(value) {
  if (value === null || value === undefined || value === '') return '-'
  return `¥${formatNumber(value, 2)}`
}
