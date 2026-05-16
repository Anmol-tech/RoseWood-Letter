import hashlib
import logging
import os
import re
from pathlib import Path

from app.config import load_env

logger = logging.getLogger("rosewood.elevenlabs")

BUILT_IN_VOICES = {
    "restoration": "EXAVITQu4vr4xnSDxMaL",  # Bella
    "milestone": "ErXwobaYiN019PkySvjV",  # Antoni
    "celebration": "MF3mGyEYCl7XYWbV9V6O",  # Elli
    "executive": "pNInz6obpgDQGcFmaJgB",  # Adam
    "default": "JBFqnCBsd6RMkjVDRZzb",  # George
}


class ElevenLabsClient:
    def __init__(self) -> None:
        load_env()
        self.api_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.base_url = os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io")
        self.model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
        self.output_format = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128")
        self.enabled = bool(self.api_key)
        self._voices_cache: list[dict[str, str]] | None = None

    def status(self) -> dict[str, str | bool]:
        try:
            import httpx  # noqa: F401
            httpx_installed = True
        except ImportError:
            httpx_installed = False

        return {
            "enabled": self.enabled,
            "api_key_present": bool(self.api_key),
            "default_voice_present": bool(os.getenv("ELEVENLABS_DEFAULT_VOICE_ID")),
            "default_voice_configured": bool(self.configured_voice_id_for("Quiet Restoration")),
            "httpx_installed": httpx_installed,
            "model_id": self.model_id,
        }

    def configured_voice_id_for(self, label: str) -> str:
        key = label.upper().replace(" ", "_").replace("/", "_")
        voice_id = (
            os.getenv(f"ELEVENLABS_VOICE_ID_{key}")
            or os.getenv("ELEVENLABS_DEFAULT_VOICE_ID")
            or ""
        )
        return "" if self._is_placeholder(voice_id) else voice_id

    def voice_id_for(self, label: str) -> str:
        return self.configured_voice_id_for(label)

    def _is_placeholder(self, value: str) -> bool:
        lowered = value.strip().lower()
        return not lowered or lowered.startswith("your_") or lowered in {"todo", "changeme"}

    async def list_voices(self) -> list[dict[str, str]]:
        if self._voices_cache is not None:
            return self._voices_cache

        if not self.enabled:
            return []

        try:
            import httpx
        except ImportError:
            return []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.base_url}/v1/voices",
                    headers={"xi-api-key": self.api_key},
                )
                response.raise_for_status()
        except httpx.HTTPError as error:
            logger.error("ElevenLabs voice list failed: %s", error)
            self._voices_cache = []
            return []

        self._voices_cache = [
            {
                "voice_id": voice.get("voice_id", ""),
                "name": voice.get("name", ""),
                "category": voice.get("category", ""),
            }
            for voice in response.json().get("voices", [])
        ]
        return self._voices_cache

    async def choose_voice_id(self, *, intent_label: str, persona_segment: str) -> str:
        configured = self.configured_voice_id_for(intent_label)
        if configured:
            logger.info("ElevenLabs voice selected from env for intent=%s", intent_label)
            return configured

        voices = await self.list_voices()
        if not voices:
            selected = self._built_in_voice_id(intent_label=intent_label, persona_segment=persona_segment)
            logger.info(
                "ElevenLabs voice selected from built-in defaults: intent=%s persona=%s voice=%s",
                intent_label,
                persona_segment,
                selected,
            )
            return selected

        terms = self._voice_terms(intent_label=intent_label, persona_segment=persona_segment)
        selected = max(voices, key=lambda voice: self._voice_score(voice, terms))
        logger.info(
            "ElevenLabs voice auto-selected: intent=%s persona=%s voice=%s name=%s",
            intent_label,
            persona_segment,
            selected.get("voice_id"),
            selected.get("name"),
        )
        return selected.get("voice_id", "")

    def _built_in_voice_id(self, *, intent_label: str, persona_segment: str) -> str:
        text = f"{intent_label} {persona_segment}".lower()

        if "restoration" in text or "recovery" in text or "wellness" in text:
            return BUILT_IN_VOICES["restoration"]
        if "milestone" in text or "ceremony" in text or "proposal" in text:
            return BUILT_IN_VOICES["milestone"]
        if "celebration" in text or "discovery" in text or "explorer" in text:
            return BUILT_IN_VOICES["celebration"]
        if "executive" in text or "business" in text or "diplomat" in text:
            return BUILT_IN_VOICES["executive"]

        return BUILT_IN_VOICES["default"]

    def _voice_terms(self, *, intent_label: str, persona_segment: str) -> list[str]:
        text = f"{intent_label} {persona_segment}".lower()

        if "restoration" in text or "recovery" in text or "wellness" in text:
            return ["calm", "soft", "gentle", "warm", "soothing", "serene", "bella", "rachel"]
        if "milestone" in text or "ceremony" in text or "proposal" in text:
            return ["warm", "deep", "elegant", "formal", "adam", "antoni"]
        if "celebration" in text or "discovery" in text or "explorer" in text:
            return ["bright", "warm", "expressive", "young", "energetic", "domi", "elli"]
        if "executive" in text or "business" in text or "diplomat" in text:
            return ["calm", "clear", "professional", "measured", "adam", "arnold"]

        return ["warm", "calm", "natural", "narrative"]

    def _voice_score(self, voice: dict[str, str], terms: list[str]) -> int:
        haystack = f"{voice.get('name', '')} {voice.get('category', '')}".lower()
        score = sum(3 for term in terms if term in haystack)
        if voice.get("category") == "premade":
            score += 1
        return score

    def _safe_filename_part(self, value: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
        return safe or "rosewood-letter"

    async def synthesize(
        self,
        *,
        text: str,
        intent_label: str,
        persona_segment: str,
        suite: str,
        public_base_url: str | None = None,
    ) -> dict[str, str | None]:
        voice_id = await self.choose_voice_id(
            intent_label=intent_label,
            persona_segment=persona_segment,
        )
        if not self.enabled or not voice_id:
            logger.warning(
                "ElevenLabs synthesis skipped: enabled=%s voice_id_present=%s intent=%s",
                self.enabled,
                bool(voice_id),
                intent_label,
            )
            return {"audio_url": None, "status": "missing_voice_id"}

        digest = hashlib.sha256(f"{suite}:{intent_label}:{text}".encode()).hexdigest()[:16]
        output_dir = Path(__file__).resolve().parents[2] / "static" / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self._safe_filename_part(suite)}-{digest}.mp3"
        audio_path = f"/static/audio/{output_path.name}"
        audio_url = f"{public_base_url.rstrip('/')}{audio_path}" if public_base_url else audio_path

        if output_path.exists():
            logger.info("ElevenLabs audio cache hit: %s", output_path)
            return {"audio_url": audio_url, "status": "voice_ready"}

        try:
            import httpx
        except ImportError:
            return {"audio_url": None, "status": "script_ready"}

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                logger.info(
                    "ElevenLabs synthesis start: intent=%s voice_id=%s model=%s output=%s",
                    intent_label,
                    voice_id,
                    self.model_id,
                    self.output_format,
                )
                response = await client.post(
                    f"{self.base_url}/v1/text-to-speech/{voice_id}",
                    params={"output_format": self.output_format},
                    headers={
                        "xi-api-key": self.api_key,
                        "content-type": "application/json",
                    },
                    json={
                        "text": text,
                        "model_id": self.model_id,
                        "voice_settings": {
                            "stability": 0.58,
                            "similarity_boost": 0.78,
                            "style": 0.18,
                            "use_speaker_boost": True,
                        },
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as error:
            logger.error(
                "ElevenLabs synthesis failed: status=%s body=%s",
                error.response.status_code,
                error.response.text[:500],
            )
            return {"audio_url": None, "status": f"voice_generation_failed_{error.response.status_code}"}
        except httpx.HTTPError as error:
            logger.error("ElevenLabs synthesis request error: %s", error)
            return {"audio_url": None, "status": "voice_generation_failed"}

        output_path.write_bytes(response.content)
        if not output_path.exists() or output_path.stat().st_size == 0:
            logger.error("ElevenLabs audio write failed: %s", output_path)
            return {"audio_url": None, "status": "voice_file_missing"}

        logger.info("ElevenLabs audio saved: %s", output_path)
        return {"audio_url": audio_url, "status": "voice_ready"}


elevenlabs_client = ElevenLabsClient()
