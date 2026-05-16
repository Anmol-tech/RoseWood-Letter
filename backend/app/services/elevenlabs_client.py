import hashlib
import os
from pathlib import Path

from app.config import load_env


class ElevenLabsClient:
    def __init__(self) -> None:
        load_env()
        self.api_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.base_url = os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io")
        self.model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
        self.output_format = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128")
        self.enabled = bool(self.api_key)

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
            "httpx_installed": httpx_installed,
            "model_id": self.model_id,
        }

    def voice_id_for(self, label: str) -> str:
        key = label.upper().replace(" ", "_").replace("/", "_")
        return (
            os.getenv(f"ELEVENLABS_VOICE_ID_{key}")
            or os.getenv("ELEVENLABS_DEFAULT_VOICE_ID")
            or ""
        )

    async def synthesize(self, *, text: str, intent_label: str, suite: str) -> dict[str, str | None]:
        voice_id = self.voice_id_for(intent_label)
        if not self.enabled or not voice_id:
            return {"audio_url": None, "status": "script_ready"}

        digest = hashlib.sha256(f"{suite}:{intent_label}:{text}".encode()).hexdigest()[:16]
        output_dir = Path(__file__).resolve().parents[2] / "static" / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{suite}-{digest}.mp3"

        if output_path.exists():
            return {"audio_url": f"/static/audio/{output_path.name}", "status": "voice_ready"}

        try:
            import httpx
        except ImportError:
            return {"audio_url": None, "status": "script_ready"}

        try:
            async with httpx.AsyncClient(timeout=60) as client:
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
        except httpx.HTTPError:
            return {"audio_url": None, "status": "voice_generation_failed"}

        output_path.write_bytes(response.content)
        return {"audio_url": f"/static/audio/{output_path.name}", "status": "voice_ready"}


elevenlabs_client = ElevenLabsClient()
