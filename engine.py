import random
import string

from sqlalchemy import ForeignKey, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _random_string():
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(6)
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(6), default=_random_string, primary_key=True)
    fullname: Mapped[str]
    delivery_instructions: Mapped[str]
    gift_recepient_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    gift_recepient: Mapped["User | None"] = relationship(
        back_populates="gift_giver", remote_side=[id]
    )
    gift_giver: Mapped["User | None"] = relationship(back_populates="gift_recepient")


engine = create_engine("sqlite:///secretsanta.db")
Base.metadata.create_all(engine)
