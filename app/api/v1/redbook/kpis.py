from datetime import date

from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.api.v1.redbook.dashboards import merge_product_filters
from app.models.redbook import RedbookKpiConfig
from app.redbook.services.kpi_service import (
    calculate_kpi_progress,
    default_period_name,
    get_metric_meta,
    metric_options,
    normalize_kpi_code,
)
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.redbook import RedbookKpiConfigCreate, RedbookKpiConfigUpdate

router = APIRouter()


async def config_payload(row: RedbookKpiConfig):
    meta = get_metric_meta(row.metric_code) or {}
    return {
        **await row.to_dict(),
        "metric_label": meta.get("label", row.metric_code),
        "category": meta.get("category", ""),
        "source": meta.get("source", ""),
        "description": meta.get("description", ""),
        "default_direction": meta.get("default_direction", "higher_better"),
    }


async def build_config_data(data: dict):
    metric_code = data.get("metric_code")
    metric = get_metric_meta(metric_code)
    if not metric:
        return None, Fail(msg="指标不存在，请从系统指标库中选择")

    project_id = data["project_id"]
    period_name = await default_period_name(project_id, data.get("period_name"))
    data["period_name"] = period_name
    data["kpi_name"] = data.get("kpi_name") or metric["label"]
    data["kpi_code"] = data.get("kpi_code") or normalize_kpi_code(project_id, period_name, metric_code)
    data["unit"] = data.get("unit") or metric.get("unit")
    data["direction"] = data.get("direction") or metric.get("default_direction", "higher_better")
    data["cost_scope"] = data.get("cost_scope") or metric.get("default_cost_scope", "exclude_service_fee")
    return data, None


async def has_duplicate_metric(project_id: int, period_name: str, metric_code: str, exclude_id: int | None = None):
    query = RedbookKpiConfig.filter(project_id=project_id, period_name=period_name, metric_code=metric_code)
    if exclude_id:
        query = query.exclude(id=exclude_id)
    return await query.exists()


@router.get("/metrics", summary="Redbook KPI metric library")
async def list_metrics():
    return Success(data=metric_options())


@router.get("/configs", summary="Redbook KPI config list")
async def list_configs(
    page: int = Query(1),
    page_size: int = Query(10),
    project_id: int | None = Query(None),
    period_name: str = Query(""),
    status: str = Query(""),
    keyword: str = Query(""),
):
    q = Q()
    if project_id:
        q &= Q(project_id=project_id)
    if period_name:
        q &= Q(period_name=period_name)
    if status:
        q &= Q(status=status)
    if keyword:
        q &= Q(kpi_name__contains=keyword) | Q(metric_code__contains=keyword) | Q(kpi_code__contains=keyword)

    query = RedbookKpiConfig.filter(q)
    total = await query.count()
    rows = await query.offset((page - 1) * page_size).limit(page_size).order_by("-created_at")
    return SuccessExtra(
        data=[await config_payload(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/configs/create", summary="Create Redbook KPI config")
async def create_config(config_in: RedbookKpiConfigCreate):
    data, error = await build_config_data(config_in.model_dump())
    if error:
        return error
    if await has_duplicate_metric(data["project_id"], data["period_name"], data["metric_code"]):
        return Fail(msg="同一项目周期下该KPI指标已存在")

    row = await RedbookKpiConfig.create(**data)
    return Success(data=await config_payload(row), msg="Created Successfully")


@router.post("/configs/update", summary="Update Redbook KPI config")
async def update_config(config_in: RedbookKpiConfigUpdate):
    row = await RedbookKpiConfig.get(id=config_in.id)
    data, error = await build_config_data(config_in.model_dump(exclude={"id"}))
    if error:
        return error
    if await has_duplicate_metric(data["project_id"], data["period_name"], data["metric_code"], exclude_id=config_in.id):
        return Fail(msg="同一项目周期下该KPI指标已存在")

    row.update_from_dict(data)
    await row.save()
    return Success(data=await config_payload(row), msg="Updated Successfully")


@router.delete("/configs/delete", summary="Delete Redbook KPI config")
async def delete_config(id: int = Query(...)):
    await RedbookKpiConfig.filter(id=id).delete()
    return Success(msg="Deleted Successfully")


@router.get("/progress", summary="Redbook KPI progress")
async def progress(
    project_id: int = Query(...),
    period_name: str = Query(""),
    date_start: date | None = Query(None),
    date_end: date | None = Query(None),
    product_category: str = Query(""),
    product_categories: list[str] | None = Query(None),
    task_id: str = Query(""),
    selected_keywords: str = Query(""),
    keyword: str = Query(""),
    use_default_keywords: bool = Query(False),
):
    product_filter = merge_product_filters(product_category, product_categories)
    return Success(
        data=await calculate_kpi_progress(
            project_id=project_id,
            period_name=period_name,
            date_start=date_start,
            date_end=date_end,
            product_category=product_filter,
            task_id=task_id,
            selected_keywords=selected_keywords,
            keyword=keyword,
            use_default_keywords=use_default_keywords,
        )
    )
