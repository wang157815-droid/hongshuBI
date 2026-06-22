import shutil

from aerich import Command
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from tortoise import connections
from tortoise.expressions import Q

from app.api import api_router
from app.controllers.api import api_controller
from app.controllers.user import UserCreate, user_controller
from app.core.exceptions import (
    DoesNotExist,
    DoesNotExistHandle,
    HTTPException,
    HttpExcHandle,
    IntegrityError,
    IntegrityHandle,
    RequestValidationError,
    RequestValidationHandle,
    ResponseValidationError,
    ResponseValidationHandle,
)
from app.log import logger
from app.models.admin import Api, Menu, Role
from app.schemas.menus import MenuType
from app.settings.config import settings

from .middlewares import BackGroundTaskMiddleware, HttpAuditLogMiddleware


def make_middlewares():
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
        ),
        Middleware(BackGroundTaskMiddleware),
        Middleware(
            HttpAuditLogMiddleware,
            methods=["GET", "POST", "PUT", "DELETE"],
            exclude_paths=[
                "/api/v1/base/access_token",
                "/docs",
                "/openapi.json",
            ],
        ),
    ]
    return middleware


def register_exceptions(app: FastAPI):
    app.add_exception_handler(DoesNotExist, DoesNotExistHandle)
    app.add_exception_handler(HTTPException, HttpExcHandle)
    app.add_exception_handler(IntegrityError, IntegrityHandle)
    app.add_exception_handler(RequestValidationError, RequestValidationHandle)
    app.add_exception_handler(ResponseValidationError, ResponseValidationHandle)


def register_routers(app: FastAPI, prefix: str = "/api"):
    app.include_router(api_router, prefix=prefix)


async def init_superuser():
    user = await user_controller.model.exists()
    if not user:
        await user_controller.create_user(
            UserCreate(
                username="admin",
                email="admin@admin.com",
                password="123456",
                is_active=True,
                is_superuser=True,
            )
        )


async def init_menus():
    menus = await Menu.exists()
    if not menus:
        parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="系统管理",
            path="/system",
            order=1,
            parent_id=0,
            icon="carbon:gui-management",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/system/user",
        )
        children_menu = [
            Menu(
                menu_type=MenuType.MENU,
                name="用户管理",
                path="user",
                order=1,
                parent_id=parent_menu.id,
                icon="material-symbols:person-outline-rounded",
                is_hidden=False,
                component="/system/user",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="角色管理",
                path="role",
                order=2,
                parent_id=parent_menu.id,
                icon="carbon:user-role",
                is_hidden=False,
                component="/system/role",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="菜单管理",
                path="menu",
                order=3,
                parent_id=parent_menu.id,
                icon="material-symbols:list-alt-outline",
                is_hidden=False,
                component="/system/menu",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="API管理",
                path="api",
                order=4,
                parent_id=parent_menu.id,
                icon="ant-design:api-outlined",
                is_hidden=False,
                component="/system/api",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="部门管理",
                path="dept",
                order=5,
                parent_id=parent_menu.id,
                icon="mingcute:department-line",
                is_hidden=False,
                component="/system/dept",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="审计日志",
                path="auditlog",
                order=6,
                parent_id=parent_menu.id,
                icon="ph:clipboard-text-bold",
                is_hidden=False,
                component="/system/auditlog",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(children_menu)
        await Menu.create(
            menu_type=MenuType.MENU,
            name="一级菜单",
            path="/top-menu",
            order=2,
            parent_id=0,
            icon="material-symbols:featured-play-list-outline",
            is_hidden=False,
            component="/top-menu",
            keepalive=False,
            redirect="",
        )
    await ensure_redbook_menus()


async def ensure_redbook_menus():
    parent_menu = await Menu.filter(path="/redbook", parent_id=0).first()
    if not parent_menu:
        parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="红书数据看板",
            path="/redbook",
            order=3,
            parent_id=0,
            icon="material-symbols:dashboard-customize-outline",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/redbook/dashboard-overview",
        )

    children = [
        {
            "name": "总览看板",
            "path": "dashboard-overview",
            "order": 1,
            "icon": "material-symbols:monitoring-outline",
            "component": "/redbook/dashboard/overview",
        },
        {
            "name": "项目管理",
            "path": "project",
            "order": 2,
            "icon": "material-symbols:folder-managed-outline",
            "component": "/redbook/project",
        },
        {
            "name": "数据上传",
            "path": "upload",
            "order": 3,
            "icon": "material-symbols:upload-file-outline",
            "component": "/redbook/upload",
        },
        {
            "name": "解析记录",
            "path": "parse-record",
            "order": 4,
            "icon": "material-symbols:article-outline",
            "component": "/redbook/parse-record",
        },
        {
            "name": "笔记映射",
            "path": "note-mapping",
            "order": 5,
            "icon": "material-symbols:edit-note-outline",
            "component": "/redbook/note-mapping",
        },
        {
            "name": "任务映射",
            "path": "task-mapping",
            "order": 6,
            "icon": "material-symbols:account-tree-outline",
            "component": "/redbook/task-mapping",
        },
    ]

    for item in children:
        exists = await Menu.filter(path=item["path"], parent_id=parent_menu.id).exists()
        if exists:
            continue
        await Menu.create(
            menu_type=MenuType.MENU,
            parent_id=parent_menu.id,
            is_hidden=False,
            keepalive=False,
            **item,
        )


async def init_apis():
    apis = await api_controller.model.exists()
    if not apis:
        await api_controller.refresh_api()


async def init_db():
    command = Command(tortoise_config=settings.TORTOISE_ORM)
    try:
        await command.init_db(safe=True)
    except FileExistsError:
        pass

    await command.init()
    try:
        await command.migrate()
    except AttributeError:
        logger.warning("unable to retrieve model history from database, model history will be created from scratch")
        shutil.rmtree("migrations")
        await command.init_db(safe=True)

    await command.upgrade(run_in_transaction=True)
    await ensure_redbook_schema()


async def ensure_redbook_schema():
    """Keep mounted SQLite files compatible with newly added redbook columns."""
    conn = connections.get("sqlite")
    await conn.execute_script(
        """
        CREATE TABLE IF NOT EXISTS redbook_keyword_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            project_id BIGINT NOT NULL,
            keyword VARCHAR(128) NOT NULL,
            product_category VARCHAR(128),
            keyword_type VARCHAR(64) NOT NULL DEFAULT 'custom',
            is_brand_keyword BOOL NOT NULL DEFAULT 0,
            is_product_keyword BOOL NOT NULL DEFAULT 0,
            is_competitor_keyword BOOL NOT NULL DEFAULT 0,
            is_default_selected BOOL NOT NULL DEFAULT 0,
            is_kpi_keyword BOOL NOT NULL DEFAULT 0,
            kpi_name VARCHAR(128),
            sort_order INT NOT NULL DEFAULT 0,
            enabled BOOL NOT NULL DEFAULT 1
        )
        """
    )
    await conn.execute_script(
        "CREATE UNIQUE INDEX IF NOT EXISTS uid_redbook_keyword_config_project_keyword "
        "ON redbook_keyword_config (project_id, keyword)"
    )
    await conn.execute_script(
        """
        CREATE TABLE IF NOT EXISTS redbook_raw_keyword_search (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            project_id BIGINT NOT NULL,
            source_file_id BIGINT NOT NULL,
            row_number INT,
            column_number INT,
            stat_date DATE,
            keyword VARCHAR(128) NOT NULL,
            product_category VARCHAR(128),
            keyword_type VARCHAR(64) NOT NULL DEFAULT 'custom',
            raw_value VARCHAR(64),
            search_index DECIMAL(20,6),
            is_less_than_threshold BOOL NOT NULL DEFAULT 0,
            threshold_value DECIMAL(20,6),
            estimate_value DECIMAL(20,6),
            raw_json JSON
        )
        """
    )
    columns_by_table = {
        "redbook_raw_pgy": {
            "task_id": "VARCHAR(128)",
        },
        "redbook_fact_task_daily": {
            "like_uv": "BIGINT",
            "collect_uv": "BIGINT",
            "comment_uv": "BIGINT",
            "share_uv": "BIGINT",
            "content_interaction_rate": "DECIMAL(20,8)",
            "new_customer_visit_uv": "BIGINT",
            "shop_follow_uv": "BIGINT",
            "shop_member_uv": "BIGINT",
            "new_customer_deal_uv": "BIGINT",
            "order_product_new_customer_gmv": "DECIMAL(20,6)",
            "presale_deposit_gmv": "DECIMAL(20,6)",
            "presale_estimated_gmv": "DECIMAL(20,6)",
            "presale_deposit_uv": "BIGINT",
        },
        "redbook_mart_project_daily": {
            "pgy_exposure": "BIGINT",
            "pgy_read_count": "BIGINT",
            "pgy_interaction_count": "BIGINT",
            "task_like_uv": "BIGINT",
            "task_collect_uv": "BIGINT",
            "task_comment_uv": "BIGINT",
            "task_share_uv": "BIGINT",
            "task_interaction_uv": "BIGINT",
            "task_new_customer_visit_uv": "BIGINT",
            "task_shop_follow_uv": "BIGINT",
            "task_shop_member_uv": "BIGINT",
            "task_new_customer_deal_uv": "BIGINT",
            "task_order_product_gmv": "DECIMAL(20,6)",
            "task_non_order_product_gmv": "DECIMAL(20,6)",
            "task_order_product_new_customer_gmv": "DECIMAL(20,6)",
            "task_presale_deposit_gmv": "DECIMAL(20,6)",
            "task_presale_estimated_gmv": "DECIMAL(20,6)",
            "task_presale_deposit_uv": "BIGINT",
        },
    }
    for table, columns in columns_by_table.items():
        table_exists = await conn.execute_query_dict(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            [table],
        )
        if not table_exists:
            continue
        current_columns = {
            item["name"]
            for item in await conn.execute_query_dict(f"PRAGMA table_info({table})")
        }
        for column_name, column_type in columns.items():
            if column_name in current_columns:
                continue
            await conn.execute_script(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_type}")
            logger.info(f"added missing redbook column {table}.{column_name}")


async def init_roles():
    roles = await Role.exists()
    if not roles:
        admin_role = await Role.create(
            name="管理员",
            desc="管理员角色",
        )
        user_role = await Role.create(
            name="普通用户",
            desc="普通用户角色",
        )

        # 分配所有API给管理员角色
        all_apis = await Api.all()
        await admin_role.apis.add(*all_apis)
        # 分配所有菜单给管理员和普通用户
        all_menus = await Menu.all()
        await admin_role.menus.add(*all_menus)
        await user_role.menus.add(*all_menus)

        # 为普通用户分配基本API
        basic_apis = await Api.filter(Q(method__in=["GET"]) | Q(tags="基础模块"))
        await user_role.apis.add(*basic_apis)


async def init_data():
    await init_db()
    await init_superuser()
    await init_menus()
    await init_apis()
    await init_roles()
