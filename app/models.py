from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)

    sites: Mapped[list["Site"]] = relationship(back_populates="owner")


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    status_code: Mapped[int | None] = mapped_column(nullable=True)
    is_online: Mapped[bool] = mapped_column(default=True)
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    owner: Mapped["User | None"] = relationship(back_populates="sites")
    logs: Mapped[list["CheckLog"]] = relationship(
        back_populates="site",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CheckLog(Base):
    __tablename__ = "check_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    site_id: Mapped[int] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE")
    )
    status_code: Mapped[int] = mapped_column(Integer)
    is_online: Mapped[bool] = mapped_column(Boolean)

    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    site: Mapped["Site"] = relationship(back_populates="logs")