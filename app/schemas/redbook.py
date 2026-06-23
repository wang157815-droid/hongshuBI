from datetime import date
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class RedbookProjectCreate(BaseModel):
    project_code: str
    project_name: str
    brand_name: Optional[str] = None
    project_period: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "active"
    remark: Optional[str] = None


class RedbookProjectUpdate(RedbookProjectCreate):
    id: int


class RedbookNoteMappingCreate(BaseModel):
    project_id: int
    note_id: str
    blogger_name: Optional[str] = None
    blogger_type: Optional[str] = None
    note_type: Optional[str] = None
    product_name: Optional[str] = None
    product_category: Optional[str] = None
    content_direction: Optional[str] = None
    note_url: Optional[str] = None
    publish_date: Optional[date] = None
    status: str = "active"


class RedbookNoteMappingUpdate(RedbookNoteMappingCreate):
    id: int


class RedbookTaskMappingCreate(BaseModel):
    project_id: int
    order_id: str
    task_id: Optional[str] = None
    task_name: Optional[str] = None
    task_type: Optional[str] = None
    product_name: Optional[str] = None
    product_category: Optional[str] = None
    blogger_type: Optional[str] = None
    cooperation_mode: Optional[str] = None
    status: str = "active"


class RedbookTaskMappingUpdate(RedbookTaskMappingCreate):
    id: int


class RedbookKpiConfigCreate(BaseModel):
    project_id: int
    period_name: Optional[str] = None
    kpi_code: Optional[str] = None
    kpi_name: Optional[str] = None
    metric_code: str
    target_value: Optional[Decimal] = None
    weight_score: Optional[Decimal] = 10
    unit: Optional[str] = None
    direction: Optional[str] = None
    cap_at_full_score: bool = True
    formula_version: str = "v1"
    cost_scope: str = "exclude_service_fee"
    status: str = "active"
    remark: Optional[str] = None


class RedbookKpiConfigUpdate(RedbookKpiConfigCreate):
    id: int


class RedbookRebuildRequest(BaseModel):
    project_id: int
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    build_note_daily: bool = True
    build_task_daily: bool = True
    build_project_daily: bool = True


class ParseIssue(BaseModel):
    row_number: Optional[int] = None
    column_name: Optional[str] = None
    raw_value: Optional[Any] = None
    error_code: str
    error_level: str = "error"
    error_message: str


class ParseResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source_type: str
    total_rows: int = 0
    data_rows: int = 0
    success_rows: int = 0
    failed_rows: int = 0
    warnings: list[ParseIssue] = Field(default_factory=list)
    errors: list[ParseIssue] = Field(default_factory=list)
    records: list[dict[str, Any]] = Field(default_factory=list)
    wide_records: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
