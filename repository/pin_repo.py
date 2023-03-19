from typing import List

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.pin_map import PinMap


class PinRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    def find_channel_by_id(self, channel_id: str) -> PinMap:
        return session.query(PinMap).filter(PinMap.channel_id == channel_id).one_or_none()

    def add_or_update_channel(self, channel_id: str, message_id: str):
        item: PinMap = self.find_channel_by_id(channel_id)

        if item is None:
            item = PinMap(channel_id=channel_id, message_id=message_id)
            session.add(item)
        else:
            item.message_id = message_id

        session.commit()

    def remove_channel(self, channel_id: str):
        session.query(PinMap).filter(PinMap.channel_id == channel_id).delete()
        session.commit()

    def get_mappings(self) -> List[PinMap]:
        return list(session.query(PinMap).all())
