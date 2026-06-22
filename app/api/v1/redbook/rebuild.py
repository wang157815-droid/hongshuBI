from fastapi import APIRouter

from app.redbook.services.fact_builder import rebuild_redbook_facts
from app.schemas.base import Success
from app.schemas.redbook import RedbookRebuildRequest

router = APIRouter()


@router.post("/facts", summary="重建红书事实表")
async def rebuild_facts(req: RedbookRebuildRequest):
    data = await rebuild_redbook_facts(
        project_id=req.project_id,
        date_start=req.date_start,
        date_end=req.date_end,
        build_note_daily=req.build_note_daily,
        build_task_daily=req.build_task_daily,
        build_project_daily=False,
    )
    return Success(data=data)


@router.post("/marts", summary="重建红书看板表")
async def rebuild_marts(req: RedbookRebuildRequest):
    data = await rebuild_redbook_facts(
        project_id=req.project_id,
        date_start=req.date_start,
        date_end=req.date_end,
        build_note_daily=False,
        build_task_daily=False,
        build_project_daily=True,
    )
    return Success(data=data)


@router.post("/all", summary="重建红书事实表和看板表")
async def rebuild_all(req: RedbookRebuildRequest):
    data = await rebuild_redbook_facts(
        project_id=req.project_id,
        date_start=req.date_start,
        date_end=req.date_end,
        build_note_daily=req.build_note_daily,
        build_task_daily=req.build_task_daily,
        build_project_daily=req.build_project_daily,
    )
    return Success(data=data)
