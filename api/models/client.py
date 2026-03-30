from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.database import Base


class Client(Base):
    __tablename__: str = "client"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    client_secret: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    authorizations: Mapped[list["ClientServiceAuthorization"]] = relationship(
        back_populates="client",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class ClientServiceAuthorization(Base):
    __tablename__: str = "client_service_authorization"
    __table_args__ = (UniqueConstraint("client_id", "service", name="uq_client_service"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("client.id"), nullable=False)
    service: Mapped[str] = mapped_column(String, nullable=False)
    quotas: Mapped[int | None] = mapped_column(Integer, nullable=True)

    client: Mapped["Client"] = relationship(back_populates="authorizations")
