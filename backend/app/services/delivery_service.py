import logging
import os
from datetime import datetime

from app.config import load_env
from app.schemas import DeliveryArtifact, DeliveryChannelState, PipelineJobState, ReservationOptionRequest

logger = logging.getLogger("rosewood.delivery")


class DeliveryService:
    def __init__(self) -> None:
        self.sendgrid_api_key = ""
        self.sendgrid_from_email = "letters@example.com"
        self.sendgrid_from_name = "Rosewood Letter"
        self.delivery_dry_run = False
        self._refresh_config()

    def _refresh_config(self) -> None:
        load_env()
        self.delivery_dry_run = os.getenv("DELIVERY_DRY_RUN", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY", "")
        self.sendgrid_from_email = os.getenv("SENDGRID_FROM_EMAIL", "letters@example.com")
        self.sendgrid_from_name = os.getenv("SENDGRID_FROM_NAME", "Rosewood Letter")

    def status(self) -> dict[str, bool]:
        self._refresh_config()
        return {
            "dry_run": self.delivery_dry_run,
            "email_enabled": self.delivery_dry_run or bool(self.sendgrid_api_key),
        }

    async def send_email(self, *, job: PipelineJobState, to_email: str) -> DeliveryChannelState:
        self._refresh_config()
        subject, text, html = self._email_message(job)

        if self.delivery_dry_run:
            logger.info(
                "SendGrid dry run: guest=%s to=%s subject=%s body=%s",
                job.guest_name,
                to_email,
                subject,
                text,
            )
            return DeliveryChannelState(
                to=to_email,
                status="sent",
                provider="sendgrid_dry_run",
                sent_at=datetime.utcnow(),
            )

        if not self.sendgrid_api_key:
            return DeliveryChannelState(
                to=to_email,
                status="not_configured",
                provider="sendgrid",
                error="SENDGRID_API_KEY is missing.",
            )

        try:
            import httpx
        except ImportError:
            return DeliveryChannelState(
                to=to_email,
                status="not_configured",
                provider="sendgrid",
                error="httpx is not installed.",
            )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {self.sendgrid_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "personalizations": [
                            {
                                "to": [{"email": to_email}],
                                "subject": subject,
                            }
                        ],
                        "from": {
                            "email": self.sendgrid_from_email,
                            "name": self.sendgrid_from_name,
                        },
                        "content": [
                            {
                                "type": "text/plain",
                                "value": text,
                            },
                            {
                                "type": "text/html",
                                "value": html,
                            }
                        ],
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as error:
            logger.error(
                "SendGrid delivery failed: status=%s body=%s",
                error.response.status_code,
                error.response.text[:500],
            )
            return DeliveryChannelState(
                to=to_email,
                status=f"failed_{error.response.status_code}",
                provider="sendgrid",
                error=error.response.text[:240],
            )
        except httpx.HTTPError as error:
            logger.error("SendGrid delivery request error: %s", error)
            return DeliveryChannelState(
                to=to_email,
                status="failed",
                provider="sendgrid",
                error=str(error),
            )

        return DeliveryChannelState(
            to=to_email,
            status="sent",
            provider="sendgrid",
            sent_at=datetime.utcnow(),
        )

    async def send_reservation_email(
        self,
        *,
        job: PipelineJobState,
        to_email: str,
        options: list[ReservationOptionRequest],
    ) -> DeliveryChannelState:
        self._refresh_config()
        subject, text, html = self._reservation_email_message(job=job, options=options)

        if self.delivery_dry_run:
            logger.info(
                "SendGrid reservation dry run: guest=%s to=%s subject=%s body=%s",
                job.guest_name,
                to_email,
                subject,
                text,
            )
            return DeliveryChannelState(
                to=to_email,
                status="sent",
                provider="sendgrid_dry_run",
                sent_at=datetime.utcnow(),
            )

        if not self.sendgrid_api_key:
            return DeliveryChannelState(
                to=to_email,
                status="not_configured",
                provider="sendgrid",
                error="SENDGRID_API_KEY is missing.",
            )

        try:
            import httpx
        except ImportError:
            return DeliveryChannelState(
                to=to_email,
                status="not_configured",
                provider="sendgrid",
                error="httpx is not installed.",
            )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {self.sendgrid_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "personalizations": [
                            {
                                "to": [{"email": to_email}],
                                "subject": subject,
                            }
                        ],
                        "from": {
                            "email": self.sendgrid_from_email,
                            "name": self.sendgrid_from_name,
                        },
                        "content": [
                            {"type": "text/plain", "value": text},
                            {"type": "text/html", "value": html},
                        ],
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as error:
            logger.error(
                "SendGrid reservation delivery failed: status=%s body=%s",
                error.response.status_code,
                error.response.text[:500],
            )
            return DeliveryChannelState(
                to=to_email,
                status=f"failed_{error.response.status_code}",
                provider="sendgrid",
                error=error.response.text[:240],
            )
        except httpx.HTTPError as error:
            logger.error("SendGrid reservation delivery request error: %s", error)
            return DeliveryChannelState(
                to=to_email,
                status="failed",
                provider="sendgrid",
                error=str(error),
            )

        return DeliveryChannelState(
            to=to_email,
            status="sent",
            provider="sendgrid",
            sent_at=datetime.utcnow(),
        )

    def _email_message(self, job: PipelineJobState) -> tuple[str, str, str]:
        letter_url = self._letter_url(job)
        profile = job.response.profile if job.response else None
        intent = job.response.visit_intent.label if job.response else "Personal Note"
        scent = job.response.print_artifact.paper_scent if job.response else "Rosewood"
        property_name = profile.property_location if profile else job.location
        suite = profile.suite if profile else job.suite

        subject = f"Your Rosewood letter is ready, {job.guest_name}"
        text = (
            f"Good morning, {job.guest_name}.\n\n"
            f"Your Rosewood Letter for {property_name} is ready.\n\n"
            "It includes your morning note, a short voice message, and the crossword answers "
            "kept quietly folded until you want them.\n\n"
            f"Open your letter:\n{letter_url}\n\n"
            f"Suite {suite}\n"
            f"{intent} · {scent}\n\n"
            "Rosewood"
        )
        html = f"""
        <!doctype html>
        <html>
          <body style="margin:0;background:#f6f1e8;color:#1a211d;font-family:Georgia,'Times New Roman',serif;">
            <div style="max-width:640px;margin:0 auto;padding:40px 28px;">
              <p style="margin:0 0 28px;color:#6f7d72;font-family:Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;">Rosewood Letter</p>
              <h1 style="margin:0 0 22px;font-size:34px;line-height:1.08;font-weight:500;">Good morning, {job.guest_name}.</h1>
              <p style="margin:0 0 18px;font-size:18px;line-height:1.6;">Your Rosewood Letter for {property_name} is ready.</p>
              <p style="margin:0 0 28px;font-size:18px;line-height:1.6;">Inside is your morning note, a short voice message, and the crossword answers kept quietly folded until you want them.</p>
              <p style="margin:0 0 34px;">
                <a href="{letter_url}" style="display:inline-block;padding:13px 18px;background:#1a211d;color:#f6f1e8;text-decoration:none;font-family:Arial,sans-serif;font-size:14px;font-weight:700;border-radius:4px;">Open your letter</a>
              </p>
              <p style="margin:0;color:#6f7d72;font-family:Arial,sans-serif;font-size:13px;line-height:1.6;">Suite {suite}<br>{intent} · {scent}</p>
              <p style="margin:34px 0 0;color:#1a211d;font-family:Arial,sans-serif;font-size:13px;letter-spacing:.1em;text-transform:uppercase;">Rosewood</p>
            </div>
          </body>
        </html>
        """
        return subject, text, html

    def _reservation_email_message(
        self,
        *,
        job: PipelineJobState,
        options: list[ReservationOptionRequest],
    ) -> tuple[str, str, str]:
        profile = job.response.profile if job.response else None
        property_name = profile.property_location if profile else job.location
        suite = profile.suite if profile else job.suite
        option_lines = [
            f"- {option.label}: {option.title}\n  {option.detail}"
            for option in options
        ]
        option_html = "".join(
            "<li style=\"margin:0 0 16px;\">"
            f"<strong style=\"display:block;color:#1a211d;font-size:16px;\">{option.label}: {option.title}</strong>"
            f"<span style=\"display:block;margin-top:4px;color:#526158;font-size:14px;line-height:1.55;\">{option.detail}</span>"
            "</li>"
            for option in options
        )

        subject = f"Rosewood reservation request received, {job.guest_name}"
        text = (
            f"Good morning, {job.guest_name}.\n\n"
            "We received your reservation request from your Rosewood Letter.\n\n"
            f"{chr(10).join(option_lines)}\n\n"
            f"{property_name} · Suite {suite}\n\n"
            "Rosewood"
        )
        html = f"""
        <!doctype html>
        <html>
          <body style="margin:0;background:#f6f1e8;color:#1a211d;font-family:Georgia,'Times New Roman',serif;">
            <div style="max-width:640px;margin:0 auto;padding:40px 28px;">
              <p style="margin:0 0 28px;color:#6f7d72;font-family:Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;">Rosewood Reservations</p>
              <h1 style="margin:0 0 18px;font-size:32px;line-height:1.12;font-weight:500;">We received your request.</h1>
              <p style="margin:0 0 24px;font-size:18px;line-height:1.6;">Good morning, {job.guest_name}. These are the arrangements we will review from your Rosewood Letter.</p>
              <ul style="margin:0 0 28px;padding:0 0 0 20px;">{option_html}</ul>
              <p style="margin:0;color:#6f7d72;font-family:Arial,sans-serif;font-size:13px;line-height:1.6;">{property_name}<br>Suite {suite}</p>
              <p style="margin:34px 0 0;color:#1a211d;font-family:Arial,sans-serif;font-size:13px;letter-spacing:.1em;text-transform:uppercase;">Rosewood</p>
            </div>
          </body>
        </html>
        """
        return subject, text, html

    def _letter_url(self, job: PipelineJobState) -> str:
        if job.response:
            return job.response.delivery.letter_url or job.response.print_artifact.qr_url
        return job.delivery.letter_url

    def merge_delivery(
        self,
        *,
        job: PipelineJobState,
        email: DeliveryChannelState | None = None,
    ) -> DeliveryArtifact:
        delivery = job.delivery.model_copy(deep=True)
        if job.response:
            delivery.letter_url = job.response.delivery.letter_url or job.response.print_artifact.qr_url
        if email is not None:
            delivery.email = email
        return delivery


delivery_service = DeliveryService()
