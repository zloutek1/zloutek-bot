from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, String, Text, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from bot.core.database import Base
from bot.core.typing import Mapper
from bot.features.starboard.models import StarboardEntry


class StarboardMessageTable(Base):
    __tablename__ = "starboard_messages"

    # Use the original message ID as the primary key as it's unique
    original_message_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Original message details
    original_channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    original_guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    original_author_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    original_jump_url: Mapped[str] = mapped_column(String, nullable=False)

    # Starboard message details
    starboard_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)
    starboard_channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StarboardMapper(Mapper[StarboardEntry, StarboardMessageTable]):
    def from_model(self, model: StarboardEntry) -> StarboardMessageTable:
        return StarboardMessageTable(
            original_message_id=model.original_message_id,
            original_channel_id=model.original_channel_id,
            original_guild_id=model.original_guild_id,
            original_author_id=model.original_author_id,
            original_jump_url=model.original_jump_url,
            starboard_message_id=model.starboard_message_id,
            starboard_channel_id=model.starboard_channel_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def to_model(self, entity: StarboardMessageTable) -> StarboardEntry:
        return StarboardEntry(
            original_message_id=entity.original_message_id,
            original_channel_id=entity.original_channel_id,
            original_guild_id=entity.original_guild_id,
            original_author_id=entity.original_author_id,
            original_jump_url=entity.original_jump_url,
            starboard_message_id=entity.starboard_message_id,
            starboard_channel_id=entity.starboard_channel_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class OrmStarboardRepository:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], mapper: Mapper[StarboardEntry, StarboardMessageTable]
    ):
        self.session_factory = session_factory
        self.mapper = mapper

    async def create(self, message: StarboardEntry) -> None:
        async with self.session_factory() as session:
            session.add(self.mapper.from_model(message))
            await session.commit()

    async def find(self, original_message_id: int) -> StarboardEntry | None:
        async with self.session_factory() as session:
            stmt = select(StarboardMessageTable).where(StarboardMessageTable.original_message_id == original_message_id)
            result = await session.execute(stmt)
            entity = result.scalar_one_or_none()

            return self.mapper.to_model(entity) if entity else None

    async def update(self, message: StarboardEntry) -> None:
        async with self.session_factory() as session:
            stmt = (
                update(StarboardMessageTable)
                .values(
                    starboard_message_id=message.starboard_message_id,
                    starboard_channel_id=message.starboard_channel_id,
                    created_at=message.created_at,
                    updated_at=message.updated_at,
                )
                .where(StarboardMessageTable.original_message_id == message.original_message_id)
            )
            await session.execute(stmt)
            await session.commit()

    async def get_pending_updates(self, cutoff_time: datetime) -> list[StarboardEntry]:
        async with self.session_factory() as session:
            stmt = select(StarboardMessageTable).where(StarboardMessageTable.updated_at < cutoff_time)
            result = await session.execute(stmt)
            entities = list(result.scalars().all())

            return [self.mapper.to_model(entity) for entity in entities]
