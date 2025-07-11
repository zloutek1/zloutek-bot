from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, String, Text, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from bot.adapters.database.database import Base
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

    # Content and state
    content: Mapped[str] = mapped_column(Text, nullable=True)
    attachment_urls: Mapped[list[str]] = mapped_column(Text, nullable=False, default=[])
    reaction_count: Mapped[int] = mapped_column(nullable=False, default=0)

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
            content=model.content,
            attachment_urls=model.attachment_urls,
            reaction_count=model.reaction_count,
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
            content=entity.content,
            attachment_urls=entity.attachment_urls,
            reaction_count=entity.reaction_count,
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

    async def update_reaction_count(self, original_message_id: int, reaction_count: int) -> None:
        async with self.session_factory() as session:
            stmt = (
                update(StarboardMessageTable)
                .where(StarboardMessageTable.original_message_id == original_message_id)
                .values(reaction_count=reaction_count, last_updated=datetime.now(UTC))
            )
            await session.execute(stmt)
            await session.commit()

    async def get_pending_updates(self, cutoff_time: datetime) -> list[StarboardEntry]:
        async with self.session_factory() as session:
            stmt = select(StarboardMessageTable).where(StarboardMessageTable.updated_at < cutoff_time)
            result = await session.execute(stmt)
            entities = list(result.scalars().all())

            return [self.mapper.to_model(entity) for entity in entities]

    async def set_starboard_message_id(self, original_message_id: int, starboard_message_id: int) -> None:
        async with self.session_factory() as session:
            stmt = (
                update(StarboardMessageTable)
                .where(StarboardMessageTable.original_message_id == original_message_id)
                .values(starboard_message_id=starboard_message_id, last_updated=datetime.now(UTC))
            )
            await session.execute(stmt)
            await session.commit()
