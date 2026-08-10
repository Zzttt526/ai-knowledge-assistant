"""Secure upload persistence and text extraction for supported documents."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings


class DocumentProcessingError(ValueError):
    """Raised when an uploaded document cannot be stored or read."""


class DocumentLoader:
    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}

    def __init__(self, settings: Settings) -> None:
        self._upload_dir = Path(settings.upload_dir)
        self._max_size_bytes = settings.max_upload_size_mb * 1024 * 1024

    async def save_and_extract(self, upload: UploadFile) -> tuple[str, Path, str]:
        filename = self._validate_filename(upload.filename)
        document_id = str(uuid4())
        destination = self._upload_dir / document_id / filename
        destination.parent.mkdir(parents=True, exist_ok=True)

        size = 0
        try:
            with destination.open("wb") as target:
                while chunk := await upload.read(1024 * 1024):
                    size += len(chunk)
                    if size > self._max_size_bytes:
                        raise DocumentProcessingError("文件超过允许的最大大小")
                    target.write(chunk)
            if size == 0:
                raise DocumentProcessingError("上传文件为空")
            text = self.extract_text(destination)
            if not text.strip():
                raise DocumentProcessingError("未能从文件中提取有效文本")
            return document_id, destination, text
        except DocumentProcessingError:
            destination.unlink(missing_ok=True)
            raise
        except OSError as exc:
            destination.unlink(missing_ok=True)
            raise DocumentProcessingError("文件保存失败") from exc
        finally:
            await upload.close()

    def extract_text(self, file_path: Path) -> str:
        extension = file_path.suffix.lower()
        try:
            if extension in {".txt", ".md", ".markdown"}:
                return file_path.read_text(encoding="utf-8-sig")
            if extension == ".pdf":
                return self._extract_pdf(file_path)
        except UnicodeDecodeError as exc:
            raise DocumentProcessingError("文本文件必须使用 UTF-8 编码") from exc
        except OSError as exc:
            raise DocumentProcessingError("文件读取失败") from exc
        raise DocumentProcessingError(f"不支持的文件类型：{extension or '无扩展名'}")

    @staticmethod
    def _extract_pdf(file_path: Path) -> str:
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(file_path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError as exc:
            raise DocumentProcessingError("PDF 解析组件未安装") from exc
        except Exception as exc:  # pypdf exposes several parsing exception types
            raise DocumentProcessingError("PDF 解析失败") from exc

    def _validate_filename(self, supplied_name: str | None) -> str:
        filename = Path(supplied_name or "").name
        filename = re.sub(r"[\\x00-\\x1f]", "", filename)
        if not filename:
            raise DocumentProcessingError("缺少文件名")
        if Path(filename).suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise DocumentProcessingError("仅支持 PDF、TXT 和 Markdown 文件")
        return filename
