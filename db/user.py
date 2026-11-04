from sqlalchemy import Integer,String,Date
from db.connection import Base
from sqlalchemy.orm import Mapped,mapped_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100))

    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        index=True
    )

    google_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True
    )

    profile_picture: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    access_token: Mapped[str | None] = mapped_column(
        String(2048), nullable=True
    )

    refresh_token: Mapped[str | None] = mapped_column(
        String(2048), nullable=True
    )

    expires_at: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    token_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    scope: Mapped[str | None] = mapped_column(
        String(2000), nullable=True
    )
    




