import disnake
from disnake.ext import commands
from typing import Optional, List

from config.app_config import config
from config.messages import Messages
from repository import subscription_repo
from repository.database.subscription import Subscription

repo = subscription_repo.SubscriptionRepository()

rooms = []


async def autocomplete_rooms(inter, string: str) -> List[str]:
    return [room.name for room in rooms if string.lower() in room.name.lower()]


class Subscriptions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global rooms

    @commands.Cog.listener()
    async def on_ready(self):
        for room in config.subscribable_channels:
            rooms.append(self.bot.get_channel(room))

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.channel.id not in config.subscribable_channels:
            return
        subscribers: List[Subscription] = repo.get_channel_subscribers(message.channel.id)
        if not len(subscribers):
            return

        embed = disnake.Embed(description=message.content[:2048])
        embed.set_author(
            name=message.author.name,
            icon_url=message.author.display_avatar.with_size(128).url,
        )
        embed.add_field(
            name=Messages.subscriptions_message_link,
            value=f"[{message.guild.name} #{message.channel.name}]({message.jump_url})",
        )
        if len(message.attachments) or len(message.embeds):
            embed.add_field(
                name=Messages.subscriptions_embed_name,
                value=Messages.subscriptions_embed_value,
            )

        for subscriber in subscribers:
            member = message.guild.get_member(subscriber.user_id)
            if member is None:
                continue
            if not self.phone_or_offline(member):
                continue

            try:
                await member.send(embed=embed)
            except disnake.errors.HTTPException:
                continue

    def phone_or_offline(self, member: disnake.Member) -> bool:
        """This helper function returns 'True' only if the member is not active
        on desktop or web; they have to be on mobile or offline."""
        if str(member.desktop_status) != "offline":
            return False
        if str(member.web_status) != "offline":
            return False
        return True

    @commands.guild_only()
    @commands.slash_command(name="subscription", description=Messages.subscribe_brief)
    async def _subscription(self, inter):
        pass

    @_subscription.sub_command(name="subscribe", description=Messages.subscribe_brief)
    async def subscribe(self, inter, channel=commands.Param(autocomplete=autocomplete_rooms)):
        for room in rooms:
            if room.name == channel:
                subscription = repo.add_subscription(inter.author.id, room.id)
                break
        else:
            await inter.send(Messages.subscriptions_unsubscribable)
            return

        if subscription is None:
            await inter.send(Messages.subscriptions_already_subscribed)
            return
        await inter.send(Messages.subscriptions_new_subscription)

    @_subscription.sub_command(name="unsubscribe", description=Messages.unsubscribe_brief)
    async def unsubscribe(self, inter, channel=commands.Param(autocomplete=autocomplete_rooms)):
        for room in rooms:
            if room.name == channel:
                removed: int = repo.remove_subscription(inter.author.id, room.id)
                if removed == 0:
                    await inter.send(Messages.subscriptions_not_subscribed)
                    return
        await inter.send(Messages.subscriptions_unsubscribed)

    @_subscription.sub_command(name="list", description=Messages.subscribeable_brief)
    async def subscribeable(self, inter):
        channels = [self.bot.get_channel(channel).mention for channel in config.subscribable_channels]
        if not len(channels):
            await inter.send(Messages.subscriptions_none)
            return

        await inter.send(" ".join(channels))

    @_subscription.sub_command(name="user", description=Messages.subscriptions_user_brief)
    async def user_subscriptions(self, inter, *, target: disnake.User = None):
        if target is None:
            user_ids = set()
            user_subscriptions: dict = dict()
            for item in repo.get_all():
                user_ids.add(item.user_id)
                if item.user_id not in user_subscriptions.keys():
                    user_subscriptions[item.user_id] = [
                        item.channel_id,
                    ]
                else:
                    user_subscriptions[item.user_id].append(item.channel_id)

            users = [self.bot.get_user(user_id) for user_id in user_ids]

            result: list = list()
            for user in users:
                user_channels = [
                    f"#{getattr(inter.guild.get_channel(cid), 'name', '???')}"
                    for cid in user_subscriptions[user.id]
                ]
                result.append(f"> {user.name}: {', '.join(user_channels)}")

            if not len(result):
                await inter.send(Messages.subscriptions_none)
                return

            await inter.send("\n".join(result))
            return

        subs: set = set()
        if type(target) == disnake.User:
            channels = repo.get_user_subscriptions(target.id)
            for entry in channels:
                channel: Optional[disnake.TextChannel] = inter.guild.get_channel(entry.channel_id)
                subs.add(f"#{channel}" if channel is not None else str(entry.channel_id))

        if not len(subs):
            await inter.send(Messages.subscriptions_none)
            return

        await inter.send("> " + ", ".join(subs))

    @_subscription.sub_command(name="channel", description=Messages.subscriptions_channel_brief)
    async def channel_subscriptions(
            self,
            inter,
            *,
            channel=commands.Param(default=None, autocomplete=autocomplete_rooms)):

        if channel is None:
            user_ids = set()
            user_subscriptions: dict = dict()
            for item in repo.get_all():
                user_ids.add(item.user_id)
                if item.user_id not in user_subscriptions.keys():
                    user_subscriptions[item.user_id] = [
                        item.channel_id,
                    ]
                else:
                    user_subscriptions[item.user_id].append(item.channel_id)

            users = [self.bot.get_user(user_id) for user_id in user_ids]

            result: list = list()
            for user in users:
                user_channels = [
                    f"#{getattr(inter.guild.get_channel(cid), 'name', '???')}"
                    for cid in user_subscriptions[user.id]
                ]
                result.append(f"> {user.name}: {', '.join(user_channels)}")

            if not len(result):
                await inter.send(Messages.subscriptions_none)
                return

            await inter.send("\n".join(result))
            return

        subs: set = set()
        if channel is not None:
            for room in rooms:
                if room.name == channel:
                    users = repo.get_channel_subscribers(room.id)
                    break

            for entry in users:
                user: Optional[disnake.User] = self.bot.get_user(entry.user_id)
                subs.add(str(user) if user is not None else str(entry.user_id))

        if not len(subs):
            await inter.send(Messages.subscriptions_none)
            return

        await inter.send("> " + ", ".join(subs))


def setup(bot):
    bot.add_cog(Subscriptions(bot))
