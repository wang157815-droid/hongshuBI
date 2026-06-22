from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.models.redbook import RedbookProject
from app.schemas.base import Success, SuccessExtra
from app.schemas.redbook import RedbookProjectCreate, RedbookProjectUpdate

router = APIRouter()


@router.get("/list", summary="红书项目列表")
async def list_projects(page: int = Query(1), page_size: int = Query(10), keyword: str = Query(""), status: str = Query("")):
    q = Q()
    if keyword:
        q &= Q(project_name__contains=keyword) | Q(project_code__contains=keyword) | Q(brand_name__contains=keyword)
    if status:
        q &= Q(status=status)
    query = RedbookProject.filter(q)
    total = await query.count()
    rows = await query.offset((page - 1) * page_size).limit(page_size).order_by("-created_at")
    return SuccessExtra(data=[await row.to_dict() for row in rows], total=total, page=page, page_size=page_size)


@router.get("/get", summary="红书项目详情")
async def get_project(project_id: int = Query(...)):
    row = await RedbookProject.get(id=project_id)
    return Success(data=await row.to_dict())


@router.post("/create", summary="创建红书项目")
async def create_project(project_in: RedbookProjectCreate):
    row = await RedbookProject.create(**project_in.model_dump())
    return Success(data=await row.to_dict(), msg="Created Successfully")


@router.post("/update", summary="更新红书项目")
async def update_project(project_in: RedbookProjectUpdate):
    row = await RedbookProject.get(id=project_in.id)
    row.update_from_dict(project_in.model_dump(exclude={"id"}))
    await row.save()
    return Success(data=await row.to_dict(), msg="Updated Successfully")


@router.delete("/delete", summary="删除红书项目")
async def delete_project(project_id: int = Query(...)):
    await RedbookProject.filter(id=project_id).delete()
    return Success(msg="Deleted Successfully")
