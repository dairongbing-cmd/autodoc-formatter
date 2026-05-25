from typing import Optional

from pydantic import BaseModel


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    size: int
    detected_format: str
    block_counts: dict


class DocumentSummary(BaseModel):
    doc_id: str
    filename: str
    detected_format: str
    block_counts: dict


class RulesPayload(BaseModel):
    rules: dict


class FormatResponse(BaseModel):
    output_id: str
    download_url: str
    size: int


class PresetInfo(BaseModel):
    name: str
    label: str
    description: str


class ErrorResponse(BaseModel):
    detail: str
