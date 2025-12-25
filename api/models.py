from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Party(Base):
    __tablename__ = "parties"

    code: Mapped[str] = mapped_column(String(12), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    host_token: Mapped[str] = mapped_column(String(128), nullable=False)
    host_player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True)

    players: Mapped[list["Player"]] = relationship(
        "Player",
        back_populates="party",
        cascade="all, delete-orphan",
        foreign_keys="Player.party_code",
    )

    host_player: Mapped["Player | None"] = relationship(
        "Player",
        foreign_keys=[host_player_id],
    )

    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="party", cascade="all, delete-orphan"
    )


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    party_code: Mapped[str] = mapped_column(ForeignKey("parties.code"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    venmo: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    party: Mapped["Party"] = relationship(
    "Party",
    back_populates="players",
    foreign_keys=[party_code],
)

    submissions: Mapped[list["Submission"]] = relationship(back_populates="player")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    party_code: Mapped[str] = mapped_column(ForeignKey("parties.code"), index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)

    image_path: Mapped[str] = mapped_column(String(255))
    total_cents: Mapped[int] = mapped_column(Integer, default=0)
    breakdown_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    party: Mapped["Party"] = relationship(back_populates="submissions")
    player: Mapped["Player"] = relationship(back_populates="submissions")
