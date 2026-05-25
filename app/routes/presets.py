from fastapi import APIRouter, HTTPException

from app.formatter.presets import list_presets, load_preset

router = APIRouter(prefix="/api/presets", tags=["presets"])


@router.get("")
async def get_presets():
    return list_presets()


@router.get("/{name}")
async def get_preset(name: str):
    preset = load_preset(name)
    if preset is None:
        raise HTTPException(status_code=404, detail=f"预设 '{name}' 未找到")
    return preset.model_dump()
