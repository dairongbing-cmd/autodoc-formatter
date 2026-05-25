from fastapi import APIRouter, File, HTTPException, UploadFile

from app.main import storage
from app.models.api import UploadResponse
from app.services.pipeline import Pipeline
from app.utils.validators import ValidationError

router = APIRouter(prefix="/api", tags=["upload"])
pipeline = Pipeline(storage)


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    try:
        result = await pipeline.ingest(file)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=415, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理文件时出错: {e}")

    return UploadResponse(**result)
