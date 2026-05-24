"""Nutrition analysis routes — AI-powered food calorie and macro estimation.
POST /nutrition/analyze — image-to-nutrition analysis endpoint.
"""

from __future__ import annotations

import base64
import logging
from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from PIL import Image

from src.agent.graph import food_agent
from src.agent.schema import NutritionReport
from src.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nutrition", tags=["Nutrition"])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _validate_and_encode(file: UploadFile) -> tuple[str, str]:
    """
    Read the uploaded file, validate it is a supported image type,
    and return (base64_encoded_string, mime_type).

    Raises HTTPException on invalid input.
    """
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                f"Accepted types: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
            ),
        )

    image_bytes = file.file.read()
    max_size_bytes = settings.NUTRITION_MAX_IMAGE_SIZE_MB * 1024 * 1024

    if len(image_bytes) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds the {settings.NUTRITION_MAX_IMAGE_SIZE_MB} MB size limit.",
        )

    # Validate the bytes are actually a readable image
    try:
        Image.open(BytesIO(image_bytes)).verify()
    except Exception as e:
        logger.warning(f"Image validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is not a valid image.",
        )

    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    return b64, file.content_type


@router.post(
    "/analyze",
    response_model=NutritionReport,
    status_code=status.HTTP_200_OK,
    summary="Analyze a food image and estimate its nutritional content",
    description=(
        "Upload a food image (JPEG, PNG, WebP, or GIF, max 10 MB). "
        "Returns a structured JSON report with identified food components, "
        "estimated calories, macronutrients, and health flags."
    ),
)
async def analyze_food_image(
    image: UploadFile = File(..., description="Food image to analyze"),
) -> NutritionReport:
    """
    POST /api/nutrition/analyze

    Accepts a multipart/form-data upload with field name `image`.
    Returns a NutritionReport JSON object with calorie and macro estimates.

    **Note:** Estimates are approximations based on visual analysis. Consult a dietitian for precise guidance.
    """
    if not settings.NUTRITION_AGENT_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nutrition analysis service is currently disabled.",
        )

    b64, mime_type = _validate_and_encode(image)

    initial_state = {
        "image_base64": b64,
        "image_mime_type": mime_type,
        "identified_foods": None,
        "cuisine_type": None,
        "image_quality": None,
        "raw_nutrition_estimate": None,
        "nutrition_report": None,
        "error": None,
    }

    try:
        result = food_agent.invoke(initial_state)
    except Exception as e:
        logger.exception("Unexpected error during nutrition agent execution")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Nutrition analysis failed: {str(e)[:100]}",
        )

    if result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result["error"],
        )

    report: NutritionReport = result.get("nutrition_report")
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent completed but produced no report.",
        )

    return report
