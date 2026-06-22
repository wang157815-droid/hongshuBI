import hashlib
import uuid
from pathlib import Path

import openpyxl
from fastapi import UploadFile

from app.models.redbook import RedbookFileUpload
from app.settings import settings

UPLOAD_ROOT = Path(settings.REDBOOK_UPLOAD_ROOT)


async def save_upload_file(project_id: int, source_type: str, file: UploadFile, upload_user_id: int | None = None):
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "").suffix.lower()
    stored_path = UPLOAD_ROOT / f"{uuid.uuid4().hex}{suffix}"
    digest = hashlib.sha256()
    size = 0
    with stored_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
            buffer.write(chunk)
    await file.seek(0)

    sheet_names = None
    if suffix in {".xlsx", ".xlsm"}:
        try:
            workbook = openpyxl.load_workbook(stored_path, read_only=True, data_only=True)
            sheet_names = workbook.sheetnames
            workbook.close()
        except Exception:
            sheet_names = []

    return await RedbookFileUpload.create(
        project_id=project_id,
        source_type=source_type,
        original_file_name=file.filename or stored_path.name,
        stored_file_path=str(stored_path),
        file_ext=suffix.lstrip("."),
        file_size=size,
        file_hash=digest.hexdigest(),
        sheet_names=sheet_names,
        upload_user_id=upload_user_id,
    )
