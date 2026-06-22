from fastapi import APIRouter, File, Form, Query, UploadFile
from tortoise.expressions import Q

from app.models.redbook import (
    RedbookFileUpload,
    RedbookParseError,
)
from app.redbook.services.parser_service import delete_uploaded_file, parse_uploaded_file
from app.redbook.services.upload import save_upload_file
from app.redbook.services.match_service import unmatched_note_ids, unmatched_order_ids
from app.schemas.base import Success, SuccessExtra

router = APIRouter()


@router.post("/upload", summary="上传红书数据源文件")
async def upload_file(
    project_id: int = Form(...),
    source_type: str = Form(...),
    parse_now: bool = Form(False),
    file: UploadFile = File(...),
):
    file_obj = await save_upload_file(project_id=project_id, source_type=source_type, file=file)
    if parse_now:
        file_obj = await parse_uploaded_file(file_obj)
    return Success(data=await file_obj.to_dict(), msg="upload success")


@router.get("/list", summary="红书上传文件列表")
async def list_files(
    page: int = Query(1),
    page_size: int = Query(10),
    project_id: int | None = Query(None),
    source_type: str = Query(""),
    parse_status: str = Query(""),
):
    q = Q()
    if project_id is not None:
        q &= Q(project_id=project_id)
    if source_type:
        q &= Q(source_type=source_type)
    if parse_status:
        q &= Q(parse_status=parse_status)
    query = RedbookFileUpload.filter(q)
    total = await query.count()
    rows = await query.offset((page - 1) * page_size).limit(page_size).order_by("-upload_time")
    return SuccessExtra(data=[await row.to_dict() for row in rows], total=total, page=page, page_size=page_size)


@router.get("/get", summary="红书上传文件详情")
async def get_file(file_id: int = Query(...)):
    row = await RedbookFileUpload.get(id=file_id)
    return Success(data=await row.to_dict())


@router.post("/parse", summary="解析红书数据源文件")
async def parse_file(file_id: int = Query(...)):
    file_obj = await RedbookFileUpload.get(id=file_id)
    file_obj = await parse_uploaded_file(file_obj)
    return Success(data=await file_obj.to_dict())


@router.post("/reparse", summary="重新解析红书数据源文件")
async def reparse_file(file_id: int = Query(...)):
    file_obj = await RedbookFileUpload.get(id=file_id)
    file_obj = await parse_uploaded_file(file_obj)
    return Success(data=await file_obj.to_dict())


@router.delete("/delete", summary="删除红书数据源文件")
async def delete_file(file_id: int = Query(...)):
    file_obj = await RedbookFileUpload.get(id=file_id)
    await delete_uploaded_file(file_obj)
    return Success(msg="delete success")


@router.get("/parse-report", summary="查看解析报告")
async def parse_report(file_id: int = Query(...)):
    file_obj = await RedbookFileUpload.get(id=file_id)
    errors = await RedbookParseError.filter(file_id=file_id).limit(200).order_by("row_number")
    data = await file_obj.to_dict()
    data["errors"] = [await row.to_dict() for row in errors]
    return Success(data=data)


@router.get("/errors", summary="查看解析错误明细")
async def parse_errors(file_id: int = Query(...), page: int = Query(1), page_size: int = Query(50)):
    query = RedbookParseError.filter(file_id=file_id)
    total = await query.count()
    rows = await query.offset((page - 1) * page_size).limit(page_size).order_by("row_number")
    return SuccessExtra(data=[await row.to_dict() for row in rows], total=total, page=page, page_size=page_size)


@router.get("/unmatched-notes", summary="查看未匹配note_id清单")
async def unmatched_notes(file_id: int = Query(...)):
    file_obj = await RedbookFileUpload.get(id=file_id)
    unmatched = await unmatched_note_ids(file_obj)
    file_obj.unmatched_note_count = len(unmatched)
    await file_obj.save()
    return Success(data={"count": len(unmatched), "note_ids": unmatched})


@router.get("/unmatched-orders", summary="查看未匹配order_id清单")
async def unmatched_orders(file_id: int = Query(...)):
    file_obj = await RedbookFileUpload.get(id=file_id)
    unmatched = await unmatched_order_ids(file_obj)
    file_obj.unmatched_order_count = len(unmatched)
    await file_obj.save()
    return Success(data={"count": len(unmatched), "order_ids": unmatched})
