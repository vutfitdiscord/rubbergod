import asyncio
from typing import Union

from disnake import User, Member
from disnake.ext.menus import MenuPages


class MenuInnerException(Exception):
    __cause__ = "Inner task raised exception."


class BlockingPagedMenu(MenuPages):
    _inner_exception = None
    inner_error_ev = asyncio.Event()

    """
    Handles some very much unexpected things with discord.ext.menu's.

        - Setting an emoji on button that Discord does not recognise would
          make pagination silently fail. This class hacks it so these
          exceptions are raised in start() call and thus propagated
          into command caller.
    """

    async def start(self, ctx, *, channel=None, wait=False):
        """
        Starts the pagination by sending the first page and then
        blocks until the pagination session finishes.

        :raises Exception: Propagates errors from inner tasks.
        """
        await super().start(ctx, channel=channel, wait=wait)

        def handle_task_exc(inner_task: asyncio.Future):
            try:
                exc = inner_task.exception()
                if exc:
                    self._inner_exception = exc
                    self.inner_error_ev.set()
            except asyncio.CancelledError:
                pass

        for task in self._Menu__tasks:  # noqa
            task.add_done_callback(handle_task_exc)

        await self._wait_finish_or_exc()

        if self._inner_exception:
            inner_exc = MenuInnerException(self._inner_exception)
            # professional exception juggling

            try:
                self.stop()
            except Exception as stop_exc:
                raise stop_exc from inner_exc
            else:
                raise inner_exc
        else:
            self.stop()

    async def _wait_finish_or_exc(self):
        await asyncio.wait(
            [self.inner_error_ev.wait(), self._event.wait()], return_when=asyncio.FIRST_COMPLETED
        )


MemberLike = Union[User, Member]
