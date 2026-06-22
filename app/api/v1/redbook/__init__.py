from fastapi import APIRouter

from .dashboards import router as dashboards_router
from .files import router as files_router
from .mappings import router as mappings_router
from .projects import router as projects_router
from .rebuild import router as rebuild_router

redbook_router = APIRouter()
redbook_router.include_router(projects_router, prefix="/projects", tags=["红书项目"])
redbook_router.include_router(files_router, prefix="/files", tags=["红书文件"])
redbook_router.include_router(mappings_router, prefix="/mappings", tags=["红书映射"])
redbook_router.include_router(rebuild_router, prefix="/rebuild", tags=["红书重算"])
redbook_router.include_router(dashboards_router, prefix="/dashboards", tags=["红书看板"])
