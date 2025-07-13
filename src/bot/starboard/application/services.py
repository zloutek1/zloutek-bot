import logging

from bot.starboard.application.ports import (
    StarboardMessage,
    StarboardPresenter,
    StarboardPublisher,
    StarboardReaction,
    StarboardRepository,
)
from bot.starboard.domain.models import StarboardEntry

log = logging.getLogger(__name__)


class StarboardService:
    def __init__(self, repository: StarboardRepository, notifier: StarboardPublisher, presenter: StarboardPresenter):
        self._repository = repository
        self._notifier = notifier
        self._presenter = presenter
        self._starboard_channel_id = 1393196186164264980

    async def handle_reaction_added(self, message: StarboardMessage, reaction: StarboardReaction) -> None:
        if not self._should_be_starred(message, reaction):
            log.debug(
                f"Message {message.id} with reaction {reaction.emoji} and count {reaction.count} doesn't meet criteria"
            )
            return

        existing_entry = await self._repository.find_by_message_id(message.id)

        if existing_entry and existing_entry.starboard_message_id:
            await self._update_starred_message(message, reaction, existing_entry)
        else:
            await self._star_message(message, reaction)

    def _should_be_starred(self, message: StarboardMessage, reaction: StarboardReaction) -> bool:
        """
        Determine whether the reaction meets all the criteria to be sent to the starboard.

        TODO: make this more parametric based on various rules
        """
        return reaction.emoji == "⭐" and reaction.count >= 1

    async def _update_starred_message(
        self, message: StarboardMessage, reaction: StarboardReaction, entry: StarboardEntry
    ) -> None:
        updated_entry = entry.update_timestamp()
        await self._repository.save(updated_entry)

        presentation = await self._presenter.create_presentation(message, reaction, updated_entry)
        await self._notifier.update_starboard_message(updated_entry, presentation)

    async def _star_message(self, message: StarboardMessage, reaction: StarboardReaction) -> None:
        new_entry = StarboardEntry.create(message.id, self._starboard_channel_id)
        await self._repository.save(new_entry)

        presentation = await self._presenter.create_presentation(message, reaction, new_entry)
        starboard_message_id = await self._notifier.post_starboard_message(new_entry, presentation)

        posted_entry = new_entry.assign_starboard_message(starboard_message_id)
        await self._repository.save(posted_entry)
