from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class WebhookAttempt(SQLModel, table=True):
    __tablename__ = "webhook_attempts"

    id: int | None = Field(default=None, primary_key=True)
    render_id: str = Field(index=True)
    event: str = Field(index=True)
    url: str
    status_code: int | None = Field(default=None)
    response_body_excerpt: str | None = Field(default=None)
    attempt_number: int = Field(default=1)
    scheduled_at: datetime = Field(default_factory=_utcnow)
    delivered_at: datetime | None = Field(default=None)
    error: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
