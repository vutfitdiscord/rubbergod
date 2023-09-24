"""
Cog implementing subscriptions to forum posts based on their tags
"""

import disnake
from disnake.ext import commands

from buttons.general import TrashView
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from database.subscription import AlreadyNotifiedDB, SubscriptionDB
from utils import add_author_footer


async def autocomp_available_tags(inter: disnake.ApplicationCommandInteraction, user_input: str):
    channel_id = inter.filled_options["channel"]
    channel: disnake.ForumChannel = await inter.bot.fetch_channel(channel_id)
    return [tag.name for tag in channel.available_tags if user_input in tag.name][:25]


async def autocomp_subscribed_tags(inter: disnake.ApplicationCommandInteraction, user_input: str):
    channel_id = str(inter.filled_options["channel"])
    tags = SubscriptionDB.get_tags(str(inter.author.id), channel_id)
    return [tag for tag in tags if user_input in tag][:25]


class Subscriptions(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @cooldowns.short_cooldown
    @commands.slash_command(name="subscription")
    async def subscription(self, inter: disnake.ApplicationCommandInteraction):
        """Group of commands for forum subscriptions."""
        await inter.response.defer(ephemeral=True)

    @subscription.sub_command(name="add", description=Messages.subscription_add_brief)
    async def add(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.ForumChannel,
        tag: str = commands.Param(autocomplete=autocomp_available_tags),
    ):
        available_tags = [tag.name for tag in channel.available_tags]
        if tag not in available_tags:
            await inter.edit_original_message(
                Messages.subscription_tag_not_found(channel=channel.mention, tag=tag)
            )
            return
        if SubscriptionDB.get(str(inter.author.id), str(channel.id), tag):
            await inter.edit_original_message(Messages.subscription_already_subscribed)
            return
        SubscriptionDB.add(inter.author.id, channel.id, tag)
        await inter.edit_original_response(Messages.subscription_added(channel=channel.mention, tag=tag))

    @subscription.sub_command(name="remove", description=Messages.subscription_remove_brief)
    async def remove(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.ForumChannel,
        tag: str = commands.Param(autocomplete=autocomp_subscribed_tags),
    ):
        sub = SubscriptionDB.get(str(inter.author.id), str(channel.id), tag)
        if not sub:
            await inter.edit_original_message(Messages.subscription_not_found(tag=tag))
            return
        sub.remove()
        await inter.edit_original_message(Messages.subscription_removed(channel=channel.mention, tag=tag))

    @subscription.sub_command(name="list", description=Messages.subscription_list_brief)
    async def list(self, inter: disnake.ApplicationCommandInteraction):
        subs = SubscriptionDB.get_user(str(inter.author.id))
        sub_list = [f"> <#{sub.forum_id}> - {sub.tag}" for sub in subs]
        message = f"{Messages.subscription_list_title}\n" + "\n".join(sub_list)
        await inter.edit_original_response(message)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: disnake.Thread):
        if not thread.applied_tags:
            # thread without tags
            return
        tags = [tag.name for tag in thread.applied_tags]
        subs = SubscriptionDB.get_channel(str(thread.parent_id))
        already_notified = AlreadyNotifiedDB.get(str(thread.id))
        for sub in subs:
            if sub.tag in tags and sub.user_id not in already_notified:
                await self.send_notification(sub.user_id, thread)
                already_notified.append(sub.user_id)
                AlreadyNotifiedDB.add(sub.user_id, str(thread.id))

    @commands.Cog.listener()
    async def on_thread_update(self, before: disnake.Thread, after: disnake.Thread):
        if not after.applied_tags:
            # thread without tags
            return
        tags = [tag.name for tag in filter(lambda x: x not in before.applied_tags, after.applied_tags)]
        subs = SubscriptionDB.get_channel(str(after.parent_id))
        already_notified = AlreadyNotifiedDB.get(str(after.id))
        for sub in subs:
            if sub.tag in tags and sub.user_id not in already_notified:
                await self.send_notification(sub.user_id, after)
                already_notified.append(sub.user_id)
                AlreadyNotifiedDB.add(sub.user_id, str(after.id))

    async def send_notification(self, user_id: str, thread: disnake.Thread):
        user: disnake.User = await self.bot.get_or_fetch_user(user_id)
        # get content of first message if available
        first_message = await thread.history(limit=1, oldest_first=True).flatten()
        content = first_message[0].content if first_message[0] else None
        embed = disnake.Embed(
            title=Messages.subscription_embed_title,
            url=thread.jump_url,
            description=content,
        )
        embed.add_field(
            name=Messages.subscription_embed_author,
            value=thread.owner.display_name
        )
        embed.add_field(
            name=Messages.subscription_embed_channel,
            value=thread.mention
        )
        tags = [f"`{tag.name}`" for tag in thread.applied_tags]
        embed.add_field(name=Messages.subscription_embed_tags, value=", ".join(tags))
        add_author_footer(embed, thread.owner)
        await user.send(embed=embed, view=TrashView())


def setup(bot: commands.Bot):
    bot.add_cog(Subscriptions(bot))
