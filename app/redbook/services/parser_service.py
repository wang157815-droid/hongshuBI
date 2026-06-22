from datetime import datetime
from pathlib import Path

from tortoise.transactions import in_transaction

from app.models.redbook import (
    RedbookFileUpload,
    RedbookKeywordConfig,
    RedbookNoteMapping,
    RedbookParseError,
    RedbookRawJuguang,
    RedbookRawKeywordSearch,
    RedbookRawPgy,
    RedbookRawPgyWide,
    RedbookRawXiaohongxingOrderDaily,
    RedbookTaskMapping,
)
from app.redbook.constants.source_type import (
    SOURCE_JUGUANG,
    SOURCE_KEYWORD_SEARCH,
    SOURCE_NOTE_MAPPING,
    SOURCE_PGY,
    SOURCE_XIAOHONGXING_ORDER,
)
from app.redbook.parsers.juguang import JuguangParser
from app.redbook.parsers.keyword_search import KeywordSearchParser
from app.redbook.parsers.note_mapping import NoteMappingParser
from app.redbook.parsers.pgy import PgyParser
from app.redbook.parsers.xiaohongxing_order import XiaohongxingOrderParser
from app.redbook.services.fact_builder import rebuild_redbook_facts
from app.redbook.services.match_service import normalize_id, refresh_file_match_counts, refresh_project_match_counts

PARSER_BY_SOURCE = {
    SOURCE_JUGUANG: JuguangParser,
    SOURCE_PGY: PgyParser,
    SOURCE_XIAOHONGXING_ORDER: XiaohongxingOrderParser,
    SOURCE_NOTE_MAPPING: NoteMappingParser,
    SOURCE_KEYWORD_SEARCH: KeywordSearchParser,
}


async def parse_uploaded_file(file_obj: RedbookFileUpload):
    parser_cls = PARSER_BY_SOURCE.get(file_obj.source_type)
    if not parser_cls:
        file_obj.parse_status = "failed"
        file_obj.error_message = f"不支持的数据源类型：{file_obj.source_type}"
        await file_obj.save()
        return file_obj

    parser = parser_cls(file_obj.stored_file_path)
    try:
        result = parser.parse()
    except Exception as exc:
        file_obj.parse_status = "failed"
        file_obj.error_message = str(exc)
        file_obj.parsed_at = datetime.now()
        await file_obj.save()
        return file_obj

    async with in_transaction():
        await RedbookParseError.filter(file_id=file_obj.id).delete()
        await _clear_previous_rows(file_obj)
        await _write_parse_errors(file_obj, result.errors + result.warnings)
        await _write_records(file_obj, result)

        file_obj.parser_version = parser.parser_version
        file_obj.total_rows = result.total_rows
        file_obj.data_rows = result.data_rows
        file_obj.success_rows = result.success_rows
        file_obj.failed_rows = result.failed_rows
        file_obj.warning_count = len(result.warnings)
        file_obj.summary_json = result.summary
        file_obj.error_message = result.errors[0].error_message if result.errors else None
        file_obj.parse_status = "failed" if result.errors and not result.records else "partial_success" if result.errors else "success"
        file_obj.parsed_at = datetime.now()
        await file_obj.save()
        await _sync_mappings(file_obj, result)
        await refresh_project_match_counts(file_obj.project_id)
        await refresh_file_match_counts(file_obj)
    if result.records:
        await rebuild_redbook_facts(file_obj.project_id)
    return file_obj


async def delete_uploaded_file(file_obj: RedbookFileUpload):
    project_id = file_obj.project_id
    stored_path = Path(file_obj.stored_file_path)
    async with in_transaction():
        await RedbookParseError.filter(file_id=file_obj.id).delete()
        await _clear_previous_rows(file_obj)
        await RedbookNoteMapping.filter(source_file_id=file_obj.id).delete()
        await RedbookTaskMapping.filter(source_file_id=file_obj.id).delete()
        await file_obj.delete()

    try:
        stored_path.unlink(missing_ok=True)
    except OSError:
        pass

    await refresh_project_match_counts(project_id)
    await rebuild_redbook_facts(project_id)


async def _clear_previous_rows(file_obj: RedbookFileUpload):
    filters = {"source_file_id": file_obj.id}
    if file_obj.source_type == SOURCE_JUGUANG:
        await RedbookRawJuguang.filter(**filters).delete()
    elif file_obj.source_type == SOURCE_PGY:
        await RedbookRawPgy.filter(**filters).delete()
        await RedbookRawPgyWide.filter(**filters).delete()
    elif file_obj.source_type == SOURCE_XIAOHONGXING_ORDER:
        await RedbookRawXiaohongxingOrderDaily.filter(**filters).delete()
    elif file_obj.source_type == SOURCE_NOTE_MAPPING:
        await RedbookNoteMapping.filter(source_file_id=file_obj.id).delete()
    elif file_obj.source_type == SOURCE_KEYWORD_SEARCH:
        await RedbookRawKeywordSearch.filter(**filters).delete()


async def _write_parse_errors(file_obj: RedbookFileUpload, issues):
    rows = [
        RedbookParseError(
            file_id=file_obj.id,
            project_id=file_obj.project_id,
            source_type=file_obj.source_type,
            row_number=issue.row_number,
            column_name=issue.column_name,
            raw_value=str(issue.raw_value) if issue.raw_value is not None else None,
            error_code=issue.error_code,
            error_level=issue.error_level,
            error_message=issue.error_message,
        )
        for issue in issues
    ]
    if rows:
        await RedbookParseError.bulk_create(rows)


async def _write_records(file_obj: RedbookFileUpload, result):
    if file_obj.source_type == SOURCE_JUGUANG:
        await RedbookRawJuguang.bulk_create(
            [RedbookRawJuguang(project_id=file_obj.project_id, source_file_id=file_obj.id, **record) for record in result.records]
        )
    elif file_obj.source_type == SOURCE_PGY:
        await RedbookRawPgy.bulk_create(
            [RedbookRawPgy(project_id=file_obj.project_id, source_file_id=file_obj.id, **record) for record in result.records]
        )
        await RedbookRawPgyWide.bulk_create(
            [
                RedbookRawPgyWide(project_id=file_obj.project_id, source_file_id=file_obj.id, **record)
                for record in result.wide_records
            ]
        )
    elif file_obj.source_type == SOURCE_XIAOHONGXING_ORDER:
        await RedbookRawXiaohongxingOrderDaily.bulk_create(
            [
                RedbookRawXiaohongxingOrderDaily(project_id=file_obj.project_id, source_file_id=file_obj.id, **record)
                for record in result.records
            ]
        )
    elif file_obj.source_type == SOURCE_KEYWORD_SEARCH:
        await RedbookRawKeywordSearch.bulk_create(
            [
                RedbookRawKeywordSearch(project_id=file_obj.project_id, source_file_id=file_obj.id, **record)
                for record in result.records
            ]
        )
    elif file_obj.source_type == SOURCE_NOTE_MAPPING:
        rows = []
        for record in result.records:
            record.pop("raw_json", None)
            rows.append(RedbookNoteMapping(project_id=file_obj.project_id, source_file_id=file_obj.id, **record))
        if rows:
            await RedbookNoteMapping.bulk_create(rows, ignore_conflicts=True)


async def _sync_mappings(file_obj: RedbookFileUpload, result):
    if file_obj.source_type == SOURCE_NOTE_MAPPING:
        for record in result.records:
            note_id = normalize_id(record.get("note_id"))
            if not note_id:
                continue
            defaults = {
                key: value
                for key, value in record.items()
                if key not in {"id", "project_id", "row_number", "raw_json", "note_id"}
            }
            defaults["note_id"] = note_id
            defaults["source_file_id"] = file_obj.id
            await RedbookNoteMapping.update_or_create(defaults=defaults, project_id=file_obj.project_id, note_id=note_id)
    elif file_obj.source_type == SOURCE_PGY:
        for record in result.records:
            note_id = normalize_id(record.get("note_id"))
            if not note_id:
                continue
            exists = await RedbookNoteMapping.filter(project_id=file_obj.project_id, note_id=note_id).exists()
            if exists:
                continue
            await RedbookNoteMapping.create(
                project_id=file_obj.project_id,
                source_file_id=file_obj.id,
                note_id=note_id,
                blogger_name=record.get("blogger_name"),
                note_type=record.get("note_type"),
                note_url=record.get("note_url"),
                publish_date=record.get("publish_date"),
                product_name=record.get("spu_name"),
                product_category=record.get("spu_name"),
                status="active",
            )
    elif file_obj.source_type == SOURCE_XIAOHONGXING_ORDER:
        seen = set()
        for record in result.records:
            order_id = normalize_id(record.get("order_id"))
            if not order_id or order_id in seen:
                continue
            seen.add(order_id)
            existing = await RedbookTaskMapping.get_or_none(project_id=file_obj.project_id, order_id=order_id)
            if existing:
                update_fields = {"source_file_id": file_obj.id, "status": "active"}
                if not existing.task_type and record.get("traffic_type"):
                    update_fields["task_type"] = record.get("traffic_type")
                if existing.task_id == order_id and existing.task_name == order_id:
                    update_fields["task_id"] = None
                    update_fields["task_name"] = None
                await RedbookTaskMapping.filter(id=existing.id).update(**update_fields)
                continue
            await RedbookTaskMapping.create(
                project_id=file_obj.project_id,
                order_id=order_id,
                task_id=None,
                task_name=None,
                task_type=record.get("traffic_type"),
                source_file_id=file_obj.id,
                status="active",
            )
    elif file_obj.source_type == SOURCE_KEYWORD_SEARCH:
        seen = set()
        for record in result.records:
            keyword = record.get("keyword")
            if not keyword or keyword in seen:
                continue
            seen.add(keyword)
            existing = await RedbookKeywordConfig.filter(project_id=file_obj.project_id, keyword=keyword).first()
            defaults = {
                "product_category": record.get("product_category"),
                "keyword_type": record.get("keyword_type") or "custom",
                "is_brand_keyword": record.get("keyword_type") == "brand",
                "is_product_keyword": record.get("keyword_type") in {"product", "category"},
                "is_competitor_keyword": record.get("keyword_type") == "competitor",
                "is_default_selected": record.get("keyword_type") == "brand",
                "enabled": True,
            }
            if existing:
                update_fields = {}
                for key, value in defaults.items():
                    if getattr(existing, key) in (None, "", False) and value not in (None, ""):
                        update_fields[key] = value
                if update_fields:
                    await RedbookKeywordConfig.filter(id=existing.id).update(**update_fields)
                continue
            await RedbookKeywordConfig.create(project_id=file_obj.project_id, keyword=keyword, **defaults)
