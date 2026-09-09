from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/images", tags=["images"])


class GenerateImageRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    seed: int | None = None
    width: int | None = Field(default=None, ge=256, le=1536)
    height: int | None = Field(default=None, ge=256, le=1536)
    steps: int | None = Field(default=None, ge=1, le=20)


def get_generator():
    from app.server.main import state
    return state.image_generator


@router.get("/status")
def image_status():
    generator = get_generator()
    return {
        "available": generator.available(),
        "model": generator.model_name,
        "steps": generator.steps,
        "width": generator.width,
        "height": generator.height,
        "quantize": generator.quantize,
        "keep_loaded": generator.keep_loaded,
    }


@router.post("/generate")
async def generate_image(payload: GenerateImageRequest):
    from app.server.inference import run_serialized
    from app.server.main import state
    try:
        return await run_serialized(
            state.lock, state.generate_image, payload.prompt, seed=payload.seed,
            width=payload.width, height=payload.height, steps=payload.steps,
        )
    except Exception as exc:
        raise HTTPException(500, f"Image generation failed: {exc}") from exc
