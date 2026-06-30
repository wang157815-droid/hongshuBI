from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.models.redbook import RedbookNoteMapping, RedbookRawPgy, RedbookTaskMapping, RedbookTaskNoteBridge
from app.redbook.services.fact_builder import rebuild_redbook_facts
from app.redbook.services.match_service import refresh_project_match_counts
from app.schemas.base import Success, SuccessExtra
from app.schemas.redbook import RedbookNoteMappingCreate, RedbookNoteMappingUpdate, RedbookTaskMappingCreate, RedbookTaskMappingUpdate

router = APIRouter()


async def refresh_mapping_outputs(project_id: int):
    await refresh_project_match_counts(project_id)
    await rebuild_redbook_facts(project_id)


def clean_option_value(value):
    if value is None:
        return ""
    return str(value).strip()


def build_select_options(values):
    cleaned = sorted({clean_option_value(value) for value in values if clean_option_value(value)})
    return [{"label": value, "value": value} for value in cleaned]


@router.get("/options", summary="Redbook mapping form options")
async def mapping_form_options(project_id: int = Query(...)):
    blogger_types = await (
        RedbookNoteMapping.filter(project_id=project_id)
        .exclude(blogger_type=None)
        .distinct()
        .values_list("blogger_type", flat=True)
    )
    product_categories = await (
        RedbookRawPgy.filter(project_id=project_id)
        .exclude(spu_name=None)
        .distinct()
        .values_list("spu_name", flat=True)
    )
    return Success(
        data={
            "blogger_type": build_select_options(blogger_types),
            "product_category": build_select_options(product_categories),
        }
    )


@router.get("/notes/list", summary="Redbook note mapping list")
async def list_note_mappings(
    page: int = Query(1),
    page_size: int = Query(10),
    project_id: int | None = Query(None),
    keyword: str = Query(""),
):
    q = Q()
    if project_id is not None:
        q &= Q(project_id=project_id)
    if keyword:
        q &= Q(note_id__contains=keyword) | Q(blogger_name__contains=keyword) | Q(content_direction__contains=keyword)
    query = RedbookNoteMapping.filter(q)
    total = await query.count()
    rows = await query.offset((page - 1) * page_size).limit(page_size).order_by("-updated_at")
    return SuccessExtra(data=[await row.to_dict() for row in rows], total=total, page=page, page_size=page_size)


@router.post("/notes/create", summary="Create redbook note mapping")
async def create_note_mapping(mapping_in: RedbookNoteMappingCreate):
    row = await RedbookNoteMapping.create(**mapping_in.model_dump())
    await refresh_mapping_outputs(row.project_id)
    return Success(data=await row.to_dict(), msg="Created Successfully")


@router.post("/notes/update", summary="Update redbook note mapping")
async def update_note_mapping(mapping_in: RedbookNoteMappingUpdate):
    row = await RedbookNoteMapping.get(id=mapping_in.id)
    row.update_from_dict(mapping_in.model_dump(exclude={"id"}))
    await row.save()
    await refresh_mapping_outputs(row.project_id)
    return Success(data=await row.to_dict(), msg="Updated Successfully")


@router.delete("/notes/delete", summary="Delete redbook note mapping")
async def delete_note_mapping(id: int = Query(...)):
    row = await RedbookNoteMapping.get_or_none(id=id)
    if not row:
        return Success(msg="Deleted Successfully")
    project_id = row.project_id
    await row.delete()
    await refresh_mapping_outputs(project_id)
    return Success(msg="Deleted Successfully")


@router.get("/tasks/list", summary="Redbook task mapping list")
async def list_task_mappings(
    page: int = Query(1),
    page_size: int = Query(10),
    project_id: int | None = Query(None),
    keyword: str = Query(""),
):
    q = Q()
    if project_id is not None:
        q &= Q(project_id=project_id)
    if keyword:
        q &= Q(order_id__contains=keyword) | Q(task_name__contains=keyword) | Q(task_type__contains=keyword)
    query = RedbookTaskMapping.filter(q)
    total = await query.count()
    rows = await query.offset((page - 1) * page_size).limit(page_size).order_by("-updated_at")
    return SuccessExtra(data=[await row.to_dict() for row in rows], total=total, page=page, page_size=page_size)


@router.get("/tasks/pgy-task-options", summary="蒲公英任务 ID 选项")
async def list_pgy_task_options(project_id: int = Query(...)):
    rows = await (
        RedbookRawPgy.filter(project_id=project_id)
        .exclude(task_id=None)
        .order_by("task_id", "-update_date")
        .values("task_id", "cooperation_name", "spu_name")
    )
    seen = set()
    options = []
    for row in rows:
        task_id = row.get("task_id") or ""
        task_id = str(task_id).strip()
        if not task_id or task_id in seen:
            continue
        seen.add(task_id)
        task_name = row.get("cooperation_name") or ""
        product_name = row.get("spu_name") or ""
        label_parts = [task_id]
        if task_name:
            label_parts.append(task_name)
        options.append(
            {
                "label": " - ".join(label_parts),
                "value": task_id,
                "task_id": task_id,
                "task_name": task_name,
                "product_name": product_name,
            }
        )
    return Success(data=options)


@router.post("/tasks/create", summary="Create redbook task mapping")
async def create_task_mapping(mapping_in: RedbookTaskMappingCreate):
    row = await RedbookTaskMapping.create(**mapping_in.model_dump())
    await refresh_mapping_outputs(row.project_id)
    return Success(data=await row.to_dict(), msg="Created Successfully")


@router.post("/tasks/update", summary="Update redbook task mapping")
async def update_task_mapping(mapping_in: RedbookTaskMappingUpdate):
    row = await RedbookTaskMapping.get(id=mapping_in.id)
    row.update_from_dict(mapping_in.model_dump(exclude={"id"}))
    await row.save()
    await refresh_mapping_outputs(row.project_id)
    return Success(data=await row.to_dict(), msg="Updated Successfully")


@router.delete("/tasks/delete", summary="Delete redbook task mapping")
async def delete_task_mapping(id: int = Query(...)):
    row = await RedbookTaskMapping.get_or_none(id=id)
    if not row:
        return Success(msg="Deleted Successfully")
    project_id = row.project_id
    await row.delete()
    await refresh_mapping_outputs(project_id)
    return Success(msg="Deleted Successfully")


@router.get("/task-note-bridge/list", summary="Redbook task note bridge list")
async def list_task_note_bridge(project_id: int = Query(...), task_id: str = Query("")):
    query = RedbookTaskNoteBridge.filter(project_id=project_id)
    if task_id:
        query = query.filter(task_id=task_id)
    rows = await query.order_by("-updated_at").limit(500)
    return Success(data=[await row.to_dict() for row in rows])
