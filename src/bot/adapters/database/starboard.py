from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from bot.adapters.database.database import Base
from bot.features.starboard.models import MessageReference, StarboardMessage


class StarboardMessageTable(Base):
    __tablename__ = "starboard_messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    original_guild_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    original_channel_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    original_message_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    starboard_guild_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    starboard_channel_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    starboard_message_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)

    reaction_count: Mapped[int] = mapped_column(default=1)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<StarboardMessage(id={self.id}, "
            f"original_message_id={self.original_message_id}, "
            f"reaction_count={self.reaction_count})>"
        )

    def to_model(self) -> StarboardMessage:
        return StarboardMessage(
            original=MessageReference(
                guild_id=self.original_guild_id,
                channel_id=self.original_channel_id,
                message_id=self.original_message_id,
            ),
            starboard=MessageReference(
                guild_id=self.starboard_guild_id,
                channel_id=self.starboard_channel_id,
                message_id=self.starboard_message_id,
            )
            if self.starboard_guild_id and self.starboard_channel_id and self.starboard_message_id
            else None,
            reaction_count=self.reaction_count,
            last_updated=self.last_updated,
        )

    @classmethod
    def from_model(cls, model: StarboardMessage) -> "StarboardMessageTable":
        return cls(
            original_guild_id=model.original.guild_id,
            original_channel_id=model.original.channel_id,
            original_message_id=model.original.message_id,
            starboard_guild_id=model.starboard.guild_id if model.starboard else None,
            starboard_channel_id=model.starboard.channel_id if model.starboard else None,
            starboard_message_id=model.starboard.message_id if model.starboard else None,
            reaction_count=model.reaction_count,
            last_updated=model.last_updated,
        )


class OrmStarboardRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def save_starboard_message(self, message: StarboardMessage) -> None:
        async with self.session_factory() as session:
            session.add(StarboardMessageTable.from_model(message))
            await session.commit()

    async def get_starboard_message(self, original_message_id: int) -> StarboardMessage | None:
        async with self.session_factory() as session:
            stmt = select(StarboardMessageTable).where(StarboardMessageTable.original_message_id == original_message_id)
            result = await session.execute(stmt)
            entity = result.scalar_one_or_none()

            return entity.to_model() if entity else None

    async def update_reaction_count(self, original_message_id: int, reaction_count: int) -> None:
        async with self.session_factory() as session:
            stmt = (
                update(StarboardMessageTable)
                .where(StarboardMessageTable.original_message_id == original_message_id)
                .values(reaction_count=reaction_count, last_updated=datetime.now(UTC))
            )
            await session.execute(stmt)
            await session.commit()

    async def get_pending_updates(self, cutoff_time: datetime) -> list[StarboardMessage]:
        async with self.session_factory() as session:
            stmt = select(StarboardMessageTable).where(StarboardMessageTable.last_updated < cutoff_time)
            result = await session.execute(stmt)
            entities = list(result.scalars().all())

            return [entity.to_model() for entity in entities]

    async def set_starboard_message(self, original_message_id: int, starboard_message_id: int) -> None:
        async with self.session_factory() as session:
            stmt = (
                update(StarboardMessageTable)
                .where(StarboardMessageTable.original_message_id == original_message_id)
                .values(starboard_message_id=starboard_message_id, last_updated=datetime.now(UTC))
            )
            await session.execute(stmt)
            await session.commit()
