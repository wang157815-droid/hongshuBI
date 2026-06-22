from app.models.redbook import (
    RedbookFileUpload,
    RedbookNoteMapping,
    RedbookRawJuguang,
    RedbookRawXiaohongxingOrderDaily,
    RedbookTaskMapping,
)
from app.redbook.constants.source_type import SOURCE_JUGUANG, SOURCE_XIAOHONGXING_ORDER


def normalize_id(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


async def unmatched_note_ids(file_obj: RedbookFileUpload) -> list[str]:
    raw_notes = await RedbookRawJuguang.filter(source_file_id=file_obj.id).exclude(note_id=None).distinct().values_list(
        "note_id", flat=True
    )
    mapped_notes = await RedbookNoteMapping.filter(project_id=file_obj.project_id).values_list("note_id", flat=True)
    raw_set = {value for value in (normalize_id(item) for item in raw_notes) if value}
    mapped_set = {value for value in (normalize_id(item) for item in mapped_notes) if value}
    return sorted(raw_set - mapped_set)


async def unmatched_order_ids(file_obj: RedbookFileUpload) -> list[str]:
    raw_orders = await RedbookRawXiaohongxingOrderDaily.filter(source_file_id=file_obj.id).exclude(
        order_id=None
    ).distinct().values_list("order_id", flat=True)
    mapped_orders = await RedbookTaskMapping.filter(project_id=file_obj.project_id).values_list("order_id", flat=True)
    raw_set = {value for value in (normalize_id(item) for item in raw_orders) if value}
    mapped_set = {value for value in (normalize_id(item) for item in mapped_orders) if value}
    return sorted(raw_set - mapped_set)


async def refresh_file_match_counts(file_obj: RedbookFileUpload) -> RedbookFileUpload:
    if file_obj.source_type == SOURCE_JUGUANG:
        file_obj.unmatched_note_count = len(await unmatched_note_ids(file_obj))
        await file_obj.save()
    elif file_obj.source_type == SOURCE_XIAOHONGXING_ORDER:
        file_obj.unmatched_order_count = len(await unmatched_order_ids(file_obj))
        await file_obj.save()
    return file_obj


async def refresh_project_match_counts(project_id: int):
    files = await RedbookFileUpload.filter(project_id=project_id, source_type__in=[SOURCE_JUGUANG, SOURCE_XIAOHONGXING_ORDER])
    for file_obj in files:
        await refresh_file_match_counts(file_obj)
