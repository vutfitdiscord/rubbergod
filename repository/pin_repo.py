from repository.base_repository import BaseRepository
from repository.database.pin_map import PinMap
from repository.database import session


class PinRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    def find_channel_by_id(self, channel_id: str):
        return session.query(PinMap).filter(PinMap.channel_id == channel_id).one_or_none()

    def toggle_active(self, channel_id: str):
        item: PinMap = self.find_channel_by_id(channel_id)

        if item is not None:
            item.is_active = not item.is_active

        session.commit()

    def add_or_update_channel(self, channel_id: str, message_id: str):
        item: PinMap = self.find_channel_by_id(channel_id)

        if item is None:
            item = PinMap(channel_id=channel_id, message_id=message_id, is_active=True)
            session.add(item)
        else:
            item.message_id = message_id

        session.commit()
