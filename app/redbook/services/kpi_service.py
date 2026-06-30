from datetime import date
from decimal import Decimal
from typing import Any

from app.api.v1.redbook.dashboards import (
    build_keyword_search_dashboard,
    build_planting_dashboard,
    build_xiaohongxing_dashboard_payload,
)
from app.models.redbook import RedbookKpiConfig, RedbookProject
from app.redbook.services.fact_builder import dec, div


DEFAULT_PERIOD_NAME = "默认周期"


KPI_METRICS: list[dict[str, Any]] = [
    {
        "code": "total_cost",
        "label": "总花费",
        "category": "投入类",
        "unit": "元",
        "default_direction": "higher_better",
        "source": "融合总览",
        "description": "笔记费用 + 投流费用，默认不含服务费。",
        "default_cost_scope": "exclude_service_fee",
    },
    {
        "code": "total_cost_with_service",
        "label": "含服务费总花费",
        "category": "投入类",
        "unit": "元",
        "default_direction": "higher_better",
        "source": "融合总览",
        "description": "笔记费用 + 投流费用 + 服务费。",
        "default_cost_scope": "include_service_fee",
    },
    {
        "code": "note_fee",
        "label": "笔记费用",
        "category": "投入类",
        "unit": "元",
        "default_direction": "higher_better",
        "source": "蒲公英",
        "description": "蒲公英博主报价汇总。",
    },
    {
        "code": "ad_cost",
        "label": "投流费用",
        "category": "投入类",
        "unit": "元",
        "default_direction": "higher_better",
        "source": "聚光投流",
        "description": "聚光消费汇总。",
    },
    {
        "code": "service_fee",
        "label": "服务费",
        "category": "投入类",
        "unit": "元",
        "default_direction": "higher_better",
        "source": "蒲公英",
        "description": "蒲公英服务费汇总。",
    },
    {
        "code": "content_exposure",
        "label": "内容曝光",
        "category": "内容类",
        "unit": "次",
        "default_direction": "higher_better",
        "source": "蒲公英",
        "description": "蒲公英笔记曝光汇总。",
    },
    {
        "code": "read_play_uv",
        "label": "阅读/播放UV",
        "category": "内容类",
        "unit": "UV",
        "default_direction": "higher_better",
        "source": "小红星",
        "description": "小红星订单/任务数据汇总。",
    },
    {
        "code": "interaction_uv",
        "label": "互动UV",
        "category": "内容类",
        "unit": "UV",
        "default_direction": "higher_better",
        "source": "小红星",
        "description": "点赞、收藏、评论、转发等互动UV汇总。",
    },
    {
        "code": "interaction_rate",
        "label": "互动率",
        "category": "内容类",
        "unit": "%",
        "default_direction": "higher_better",
        "source": "小红星",
        "description": "互动UV / 阅读播放UV。",
    },
    {
        "code": "cpc",
        "label": "CPC",
        "category": "投流效率类",
        "unit": "元",
        "default_direction": "lower_better",
        "source": "种草投流",
        "description": "投流费用 / 点击量。",
    },
    {
        "code": "cpm",
        "label": "CPM",
        "category": "投流效率类",
        "unit": "元",
        "default_direction": "lower_better",
        "source": "种草投流",
        "description": "投流费用 / 曝光量 * 1000。",
    },
    {
        "code": "cpe",
        "label": "CPE",
        "category": "投流效率类",
        "unit": "元",
        "default_direction": "lower_better",
        "source": "种草投流",
        "description": "投流费用 / 互动量。",
    },
    {
        "code": "search_component_cost",
        "label": "搜索组件点击成本",
        "category": "投流效率类",
        "unit": "元",
        "default_direction": "lower_better",
        "source": "种草投流",
        "description": "投流费用 / 搜索组件点击量。",
    },
    {
        "code": "visit_uv_cost",
        "label": "进店UV成本",
        "category": "投流效率类",
        "unit": "元",
        "default_direction": "lower_better",
        "source": "小红星",
        "description": "总花费 / 进店UV。",
    },
    {
        "code": "search_index",
        "label": "红搜指数",
        "category": "搜索类",
        "unit": "指数",
        "default_direction": "higher_better",
        "source": "红搜搜索日报",
        "description": "红搜看板当前关键词口径下的搜索指数汇总。",
    },
    {
        "code": "selected_keyword_count",
        "label": "已选关键词数",
        "category": "搜索类",
        "unit": "个",
        "default_direction": "higher_better",
        "source": "红搜搜索日报",
        "description": "红搜看板当前参与统计的关键词数量。",
    },
    {
        "code": "avg_search_index",
        "label": "平均搜索指数",
        "category": "搜索类",
        "unit": "指数",
        "default_direction": "higher_better",
        "source": "红搜搜索日报",
        "description": "红搜看板当前关键词口径下的平均搜索指数。",
    },
    {
        "code": "search_exposure_uv",
        "label": "搜索曝光UV",
        "category": "承接类",
        "unit": "UV",
        "default_direction": "higher_better",
        "source": "小红星",
        "description": "小红星手淘搜索曝光UV。",
    },
    {
        "code": "search_visit_uv",
        "label": "搜索进店UV",
        "category": "承接类",
        "unit": "UV",
        "default_direction": "higher_better",
        "source": "小红星",
        "description": "小红星搜索进店UV。",
    },
    {
        "code": "shop_visit_uv",
        "label": "进店UV",
        "category": "承接类",
        "unit": "UV",
        "default_direction": "higher_better",
        "source": "小红星",
        "description": "小红星进店UV。",
    },
    {
        "code": "collect_cart_uv",
        "label": "收藏加购UV",
        "category": "承接类",
        "unit": "UV",
        "default_direction": "higher_better",
        "source": "小红星",
        "description": "商品收藏UV + 商品加购UV。",
    },
    {
        "code": "deal_uv",
        "label": "成交UV",
        "category": "成交类",
        "unit": "UV",
        "default_direction": "higher_better",
        "source": "小红星",
        "description": "小红星成交UV。",
    },
    {
        "code": "merchant_gmv",
        "label": "GMV",
        "category": "成交类",
        "unit": "元",
        "default_direction": "higher_better",
        "source": "小红星",
        "description": "商家商品成交GMV。",
    },
    {
        "code": "roi",
        "label": "ROI",
        "category": "成交类",
        "unit": "倍",
        "default_direction": "higher_better",
        "source": "小红星",
        "description": "GMV / 总花费。",
    },
    {
        "code": "new_customer_deal_uv",
        "label": "新客成交UV",
        "category": "成交类",
        "unit": "UV",
        "default_direction": "higher_better",
        "source": "小红星",
        "description": "小红星新客成交UV。",
    },
    {
        "code": "order_product_new_customer_gmv",
        "label": "新客成交GMV",
        "category": "成交类",
        "unit": "元",
        "default_direction": "higher_better",
        "source": "小红星",
        "description": "任务商品新客成交GMV。",
    },
]

KPI_METRIC_MAP = {item["code"]: item for item in KPI_METRICS}


async def default_period_name(project_id: int, period_name: str | None = None):
    if period_name:
        return period_name.strip() or DEFAULT_PERIOD_NAME
    project = await RedbookProject.filter(id=project_id).first()
    if project and project.project_period:
        return project.project_period
    return DEFAULT_PERIOD_NAME


def metric_options():
    return KPI_METRICS


def get_metric_meta(metric_code: str):
    return KPI_METRIC_MAP.get(metric_code)


def normalize_kpi_code(project_id: int, period_name: str, metric_code: str):
    safe_period = "".join(ch if ch.isalnum() else "_" for ch in period_name)[:24] or "default"
    return f"{project_id}_{safe_period}_{metric_code}"[:64]


def decimal_or_none(value):
    if value is None:
        return None
    return dec(value)


def pick_value(primary: dict[str, Any], fallback: dict[str, Any], key: str):
    value = primary.get(key)
    if value is None:
        value = fallback.get(key)
    return value


async def resolve_kpi_metric_values(
    project_id: int,
    date_start: date | None = None,
    date_end: date | None = None,
    product_category: str = "",
    task_id: str = "",
    selected_keywords: str = "",
    keyword: str = "",
    use_default_keywords: bool = False,
):
    planting_dashboard = await build_planting_dashboard(
        project_id=project_id,
        date_start=date_start,
        date_end=date_end,
        product_category=product_category,
        blogger_type="",
        note_type="",
        content_direction="",
        keyword="",
        task_id=task_id,
    )
    planting_totals = planting_dashboard.get("totals") or {}

    xhx_dashboard = await build_xiaohongxing_dashboard_payload(
        project_id=project_id,
        date_start=date_start,
        date_end=date_end,
        product_category=product_category,
        task_id=task_id,
    )
    xhx_summary = xhx_dashboard.get("summary") or {}

    keyword_dashboard = await build_keyword_search_dashboard(
        project_id=project_id,
        date_start=date_start,
        date_end=date_end,
        selected_keywords=selected_keywords,
        keyword=keyword,
        use_default_keywords=use_default_keywords,
    )
    keyword_summary = keyword_dashboard.get("summary") or {}

    values = {}
    for key in [
        "total_cost",
        "total_cost_with_service",
        "note_fee",
        "ad_cost",
        "service_fee",
        "content_exposure",
        "read_play_uv",
        "interaction_uv",
        "interaction_rate",
        "search_exposure_uv",
        "search_visit_uv",
        "shop_visit_uv",
        "collect_cart_uv",
        "deal_uv",
        "merchant_gmv",
        "roi",
        "new_customer_deal_uv",
        "order_product_new_customer_gmv",
    ]:
        values[key] = pick_value(xhx_summary, planting_totals, key)

    for key in ["cpc", "cpm", "cpe", "search_component_cost"]:
        values[key] = pick_value(planting_totals, xhx_summary, key)

    values["visit_uv_cost"] = div(dec(values.get("total_cost")), values.get("shop_visit_uv"))
    values["search_index"] = keyword_summary.get("search_index")
    values["selected_keyword_count"] = keyword_summary.get("selected_keyword_count")
    values["avg_search_index"] = keyword_summary.get("avg_search_index")
    return values


def build_progress_item(config: RedbookKpiConfig, actual_value):
    meta = get_metric_meta(config.metric_code) or {}
    target_value = decimal_or_none(config.target_value)
    weight_score = dec(config.weight_score)
    actual_decimal = decimal_or_none(actual_value)
    achievement_rate = None
    actual_score = None
    score_gap = None
    status = "missing"
    status_label = "数据缺失"

    if target_value is None or target_value <= 0:
        status = "no_target"
        status_label = "未配置目标"
    elif actual_decimal is not None:
        if config.direction == "lower_better":
            achievement_rate = Decimal("1") if actual_decimal == 0 else div(target_value, actual_decimal)
        else:
            achievement_rate = div(actual_decimal, target_value)
        if achievement_rate is not None:
            score_rate = min(dec(achievement_rate), Decimal("1")) if config.cap_at_full_score else dec(achievement_rate)
            actual_score = score_rate * weight_score
            score_gap = max(weight_score - actual_score, Decimal("0"))
            if achievement_rate >= 1:
                status = "achieved"
                status_label = "已达标"
            else:
                status = "below_target"
                status_label = "未达标"

    return {
        "id": config.id,
        "kpi_code": config.kpi_code,
        "kpi_name": config.kpi_name,
        "period_name": config.period_name,
        "metric_code": config.metric_code,
        "metric_label": meta.get("label", config.metric_code),
        "category": meta.get("category", ""),
        "source": meta.get("source", ""),
        "description": meta.get("description", ""),
        "actual_value": actual_decimal,
        "target_value": target_value,
        "weight_score": weight_score,
        "achievement_rate": achievement_rate,
        "actual_score": actual_score,
        "score_gap": score_gap,
        "direction": config.direction,
        "cost_scope": config.cost_scope,
        "unit": config.unit or meta.get("unit"),
        "cap_at_full_score": config.cap_at_full_score,
        "status": status,
        "status_label": status_label,
        "remark": config.remark,
    }


async def calculate_kpi_progress(
    project_id: int,
    period_name: str | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    product_category: str = "",
    task_id: str = "",
    selected_keywords: str = "",
    keyword: str = "",
    use_default_keywords: bool = False,
):
    resolved_period = await default_period_name(project_id, period_name)
    configs = await RedbookKpiConfig.filter(
        project_id=project_id,
        period_name=resolved_period,
        status="active",
    ).order_by("id")
    if not configs:
        return {
            "configured": False,
            "project_id": project_id,
            "period_name": resolved_period,
            "items": [],
            "weak_items": [],
            "configured_count": 0,
            "scored_count": 0,
            "achieved_count": 0,
            "failed_count": 0,
            "missing_count": 0,
            "total_weight": Decimal("0"),
            "configured_weight": Decimal("0"),
            "total_score": None,
            "score_rate": None,
        }

    metric_values = await resolve_kpi_metric_values(
        project_id=project_id,
        date_start=date_start,
        date_end=date_end,
        product_category=product_category,
        task_id=task_id,
        selected_keywords=selected_keywords,
        keyword=keyword,
        use_default_keywords=use_default_keywords,
    )
    items = [build_progress_item(config, metric_values.get(config.metric_code)) for config in configs]
    scored_items = [item for item in items if item["actual_score"] is not None]
    total_score = sum((dec(item["actual_score"]) for item in scored_items), Decimal("0"))
    total_weight = sum((dec(item["weight_score"]) for item in scored_items), Decimal("0"))
    configured_weight = sum((dec(item["weight_score"]) for item in items), Decimal("0"))
    weak_items = sorted(
        [item for item in items if item["status"] == "below_target"],
        key=lambda item: dec(item["score_gap"]),
        reverse=True,
    )

    return {
        "configured": True,
        "project_id": project_id,
        "period_name": resolved_period,
        "items": items,
        "weak_items": weak_items[:10],
        "configured_count": len(items),
        "scored_count": len(scored_items),
        "achieved_count": len([item for item in items if item["status"] == "achieved"]),
        "failed_count": len([item for item in items if item["status"] == "below_target"]),
        "missing_count": len([item for item in items if item["status"] in {"missing", "no_target"}]),
        "total_weight": total_weight,
        "configured_weight": configured_weight,
        "total_score": total_score,
        "score_rate": div(total_score, total_weight),
    }
