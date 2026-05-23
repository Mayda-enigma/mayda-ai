"""
API routes for the Voice Service.
"""
import logging
import os
import shutil
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.api.deps import TranscriberDep
from src.middleware.service_auth import require_service_token
from src.schemas.voice_schema import (
    ChefParseRequest,
    ChefParseResponse,
    OrderParseItem,
    OrderParseRequest,
    OrderParseResponse,
)
from src.services.voice_chef_parser import parse_chef_command
from src.services.voice_order_parser import parse_order

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Voice Endpoints ──

@router.post(
    "/transcribe",
    dependencies=[Depends(require_service_token)],
)
async def transcribe_audio(
    transcriber: TranscriberDep,
    audio: UploadFile = File(...),
    language: str | None = Form(None),
):
    """
    Transcribe raw vocal/audio files (e.g. WAV, MP3, M4A) to standard French or English text.
    Saves to a temporary file, executes Whisper STT, and cleans up.
    """
    logger.info("Transcribe audio request received: filename=%s, content_type=%s, language=%s",
                audio.filename, audio.content_type, language)

    # 1. Create a temporary file to save the uploaded audio bytes
    suffix = os.path.splitext(audio.filename)[1] if audio.filename else ".wav"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name
            shutil.copyfileobj(audio.file, temp_file)
    except Exception as exc:
        logger.error("Failed to write uploaded file to disk: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to process audio upload: {str(exc)}")

    # 2. Run Whisper STT
    try:
        result = transcriber.transcribe(temp_path, language=language)
        return result
    except Exception as exc:
        logger.error("Whisper transcription failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Speech transcription failed: {str(exc)}")
    finally:
        # 3. Clean up the temporary file
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                logger.info("Successfully cleaned up temporary audio file: %s", temp_path)
        except Exception as cleanup_err:
            logger.warning("Could not clean up temp file %s: %s", temp_path, cleanup_err)


@router.post(
    "/parse/chef",
    response_model=ChefParseResponse,
    dependencies=[Depends(require_service_token)],
)
async def parse_chef_vocal_command(
    body: ChefParseRequest,
):
    """
    Parse French chef instructions (such as "commande 15 lance") using fuzzy matching.
    """
    try:
        result = parse_chef_command(body.text)
        if result is None:
            return ChefParseResponse(
                type=None,
                order_number=None,
                confidence=None,
                matched_phrase=None,
                message=f"❌ Commande rejetée - format ou intention incomprise: '{body.text}'"
            )

        return ChefParseResponse(
            type=result["type"],
            order_number=result["order_number"],
            confidence=result["confidence"],
            matched_phrase=result["matched_phrase"],
            message=result["message"],
        )
    except Exception as exc:
        logger.error("Error parsing chef command: %s", exc)
        raise HTTPException(status_code=500, detail=f"Chef parser error: {str(exc)}")


@router.post(
    "/parse/order",
    response_model=OrderParseResponse,
    dependencies=[Depends(require_service_token)],
)
async def parse_customer_verbal_order(
    body: OrderParseRequest,
):
    """
    Fuzzy-parse verbal orders to match spoken menu names with actual restaurant catalog products.
    E.g. "two burgers and a cola" matches product database ids and quantities.
    """
    try:
        # Transform MenuItem Pydantic models to dictionaries
        menu_items_list = [{"id": item.id, "name": item.name} for item in body.menu_items]

        parsed_results = parse_order(body.text, menu_items_list)

        items = [
            OrderParseItem(
                menu_item_id=res["menu_item_id"],
                menu_item_name=res["menu_item_name"],
                quantity=res["quantity"],
                confidence=res["confidence"],
            )
            for res in parsed_results
        ]

        return OrderParseResponse(items=items)
    except Exception as exc:
        logger.error("Error parsing customer order: %s", exc)
        raise HTTPException(status_code=500, detail=f"Order parser error: {str(exc)}")
