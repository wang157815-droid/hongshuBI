from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from app.schemas.redbook import ParseIssue, ParseResult


class BaseRedbookParser:
    source_type = "unknown"
    parser_version = "v1"

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.warnings: list[ParseIssue] = []
        self.errors: list[ParseIssue] = []

    def parse(self) -> ParseResult:
        raise NotImplementedError

    def warn(self, row_number: int | None, column_name: str | None, raw_value: Any, code: str, message: str):
        self.warnings.append(
            ParseIssue(
                row_number=row_number,
                column_name=column_name,
                raw_value=str(raw_value) if raw_value is not None else None,
                error_code=code,
                error_level="warning",
                error_message=message,
            )
        )

    def error(self, row_number: int | None, column_name: str | None, raw_value: Any, code: str, message: str):
        self.errors.append(
            ParseIssue(
                row_number=row_number,
                column_name=column_name,
                raw_value=str(raw_value) if raw_value is not None else None,
                error_code=code,
                error_level="error",
                error_message=message,
            )
        )


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text in {"", "-", "—", "nan", "NaN", "None"}:
        return None
    return text


def to_decimal(value: Any, is_percent: bool = False) -> Decimal | None:
    text = clean_text(value)
    if text is None:
        return None
    had_percent = text.endswith("%")
    text = text.replace(",", "").replace("%", "")
    if text.startswith("<"):
        return None
    try:
        number = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if is_percent and (had_percent or number > 1):
        number = number / Decimal("100")
    return number


def to_int(value: Any) -> int | None:
    number = to_decimal(value)
    if number is None:
        return None
    return int(number)


def to_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        number_text = str(int(value))
        if len(number_text) == 8 and number_text.startswith(("19", "20")):
            return datetime.strptime(number_text, "%Y%m%d").date()
        if 20000 < value < 60000:
            return (datetime(1899, 12, 30) + timedelta(days=int(value))).date()
    text = clean_text(value)
    if text is None:
        return None
    if text.isdigit() and len(text) == 8:
        return datetime.strptime(text, "%Y%m%d").date()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def serializable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def compact_raw(row: dict[str, Any]) -> dict[str, Any]:
    return {k: serializable(v) for k, v in row.items() if v is not None}
