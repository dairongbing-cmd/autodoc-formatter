from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from app.main import storage
from app.models.api import DocumentSummary, FormatResponse, RulesPayload
from app.models.rules import FormattingRules
from app.routes.upload import pipeline

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("/{doc_id}", response_model=DocumentSummary)
async def get_document(doc_id: str):
    summary = pipeline.get_summary(doc_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="文档未找到")
    return DocumentSummary(**summary)


@router.post("/{doc_id}/rules")
async def save_rules(doc_id: str, payload: RulesPayload):
    if pipeline.get_document(doc_id) is None:
        raise HTTPException(status_code=404, detail="文档未找到")
    try:
        rules = pipeline.set_rules(doc_id, payload.rules)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"格式规则无效: {e}")
    return {"doc_id": doc_id, "preset_name": rules.preset_name}


@router.get("/{doc_id}/rules")
async def get_rules(doc_id: str):
    rules = pipeline.get_rules(doc_id)
    if rules is None:
        rules = FormattingRules()
    return rules.model_dump()


@router.get("/{doc_id}/preview", response_class=HTMLResponse)
async def preview_document(doc_id: str):
    html = await pipeline.preview(doc_id)
    if html is None:
        raise HTTPException(status_code=404, detail="文档未找到")
    return HTMLResponse(content=html)


@router.post("/{doc_id}/format", response_model=FormatResponse)
async def format_document(doc_id: str, payload: RulesPayload | None = None):
    if pipeline.get_document(doc_id) is None:
        raise HTTPException(status_code=404, detail="文档未找到")

    if payload:
        try:
            pipeline.set_rules(doc_id, payload.rules)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"格式规则无效: {e}")

    try:
        result = await pipeline.format(doc_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"排版处理时出错: {e}")

    return FormatResponse(**result)


@router.get("/{doc_id}/download")
async def download_document(doc_id: str):
    error_msg = "排版文件未生成，请先调用 format 接口"
    output_path = storage.get_output_path(doc_id)
    if output_path is None:
        raise HTTPException(status_code=404, detail=error_msg)
    filename = pipeline._filenames.get(doc_id, "document")
    name = filename.rsplit(".", 1)[0]
    return FileResponse(
        path=str(output_path),
        filename=f"{name}_formatted.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    pipeline.cleanup(doc_id)
    return {"status": "deleted"}
