from fastapi import APIRouter, HTTPException

from app.models.schemas import HealthResponse, Layer12Input, Layer34Output
from app.services.pipeline_service import Layer34PipelineService

router = APIRouter()
pipeline = Layer34PipelineService()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="layer3-4-content-protection")


@router.post("/layers/3-4/process", response_model=Layer34Output)
def process_layer_3_4(payload: Layer12Input) -> Layer34Output:
    return pipeline.process(payload)


@router.get("/layers/3-4/content/{content_id}", response_model=Layer34Output)
def get_registered_content(content_id: str) -> Layer34Output:
    result = pipeline.get_registered_content(content_id=content_id)
    if result is None:
        raise HTTPException(status_code=404, detail="content_id not found")
    return result
