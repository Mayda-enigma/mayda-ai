"""
Whisper-based speech transcription service.
Ported and refactored from mayda-ai/voice/VoiceScript.py.
"""
import logging
import os
from typing import Dict, Any, Optional
import whisper

logger = logging.getLogger(__name__)


class Transcriber:
    """
    Manages loading and utilizing the Whisper model for audio transcribing.
    Avoids loading model on module import by using eager instantiation on lifespan startup.
    """

    def __init__(self, model_size: str = "tiny") -> None:
        self.model_size = model_size
        self.model = None

    def initialize_model(self) -> None:
        """Loads the Whisper model into memory."""
        logger.info("Initializing Whisper model ('%s')... This may take some time...", self.model_size)
        self.model = whisper.load_model(self.model_size)
        logger.info("Whisper model '%s' successfully loaded.", self.model_size)

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribes an audio file into text.
        Returns:
            Dict: {
                "text": transcribed string,
                "language": detected language string,
                "duration_seconds": float
            }
        """
        if self.model is None:
            self.initialize_model()

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info("Transcribing audio file: %s (language_override=%s)...", audio_path, language)
        
        # Call whisper transcribe
        # By default, whisper transcribe returns a dict containing "text", "language", "segments", etc.
        transcribe_args = {}
        if language:
            transcribe_args["language"] = language

        result = self.model.transcribe(audio_path, **transcribe_args)
        
        text = result.get("text", "").strip()
        detected_lang = result.get("language", language or "unknown")

        # Estimate duration using audio file metadata (soundfile)
        duration = 0.0
        try:
            import soundfile as sf
            info = sf.info(audio_path)
            duration = info.duration
        except Exception as exc:
            logger.warning("Could not calculate exact audio duration: %s", exc)

        logger.info("Transcription completed: '%s' (language=%s, duration=%.2fs)", text, detected_lang, duration)
        return {
            "text": text,
            "language": detected_lang,
            "duration_seconds": duration,
        }
