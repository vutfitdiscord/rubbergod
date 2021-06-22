import discord
from discord.ext import commands
from typing import Union, Optional

from config import app_config, messages
from repository import subscription_repo

repo = subscription_repo.SubscriptionRepository()
config = app_config.Config
messages = messages.Messages


class Subscriptions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id not in config.subscribable_channels:
            return
        subscribers: List[Subscription] = repo.get_channel_subscribers(message.channel.id)
        if not len(subscribers):
            return

        embed = discord.Embed(description=message.content[:2048])
        embed.set_author(
            name=message.author.name,
            icon_url=message.author.avatar_url_as(size=128),
        )
        embed.add_field(
            name=messages.subscriptions_message_link,
            value=f"[{message.guild.name} #{message.channel.name}]({message.jump_url})",
        )
        if len(message.attachments) or len(message.embeds):
            embed.add_field(
                name=messages.subscriptions_embed_name,
                value=messages.subscriptions_embed_value,
            )

        for subscriber in subscribers:
            member = message.guild.get_member(subscriber.user_id)
            if member is None:
                continue
            if not self.phone_or_offline(member):
                continue

            try:
                await member.send(embed=embed)
            except discord.errors.HTTPException:
                continue

    def phone_or_offline(self, member: discord.Member) -> bool:
        """This helper function returns 'True' only if the member is not active
        on desktop or web; they have to be on mobile or offline."""
        if str(member.desktop_status) != "offline":
            return False
        if str(member.web_status) != "offline":
            return False
        return True

    @commands.guild_only()
    @commands.command(brief=messages.subscribe_brief)
    async def subscribe(self, ctx: commands.Context, channel: discord.TextChannel):
        if channel.id not in config.subscribable_channels:
            await ctx.reply(messages.subscriptions_unsubscribable)
            return

        subscription = repo.add_subscription(ctx.author.id, channel.id)
        if subscription is None:
            await ctx.reply(messages.subscriptions_already_subscribed)
            return
        await ctx.reply(messages.subscriptions_new_subscription)

    @commands.guild_only()
    @commands.command(brief=messages.unsubscribe_brief)
    async def unsubscribe(self, ctx: commands.Context, channel: discord.TextChannel):
        removed: int = repo.remove_subscription(ctx.author.id, channel.id)
        if removed == 0:
            await ctx.reply(messages.subscriptions_not_subscribed)
            return
        await ctx.reply(messages.subscriptions_unsubscribed)

    @commands.guild_only()
    @commands.command(brief=messages.subscribeable_brief)
    async def subscribeable(self, ctx):
        channel_names = [
            getattr(ctx.guild.get_channel(channel_id), "name", str(channel_id))
            for channel_id in config.subscribable_channels
        ]
        if not len(channel_names):
            await ctx.reply(messages.subscriptions_none)
            return

        await ctx.reply(", ".join(f"#{name}" for name in channel_names))

    @commands.guild_only()
    @commands.command(brief=messages.subscriptions_brief)
    async def subscriptions(self, ctx, *, target: Union[discord.User, discord.TextChannel] = None):
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
                    f"#{getattr(ctx.guild.get_channel(cid), 'name', '???')}"
                    for cid in user_subscriptions[user.id]
                ]
                result.append(f"> {user.name}: {', '.join(user_channels)}")

            if not len(result):
                await ctx.reply(messages.subscriptions_none)
                return

            await ctx.reply("\n".join(result))
            return

        subs: set = set()
        if type(target) == discord.TextChannel:
            users = repo.get_channel_subscribers(target.id)
            for entry in users:
                user: Optional[discord.User] = self.bot.get_user(entry.user_id)
                subs.add(str(user) if user is not None else str(entry.user_id))
        elif type(target) == discord.User:
            channels = repo.get_user_subscriptions(target.id)
            for entry in channels:
                channel: Optional[discord.TextChannel] = ctx.guild.get_channel(entry.channel_id)
                subs.add(f"#{channel}" if channel is not None else str(entry.channel_id))

        if not len(subs):
            await ctx.reply(messages.subscriptions_none)
            return

        await ctx.reply("> " + ", ".join(subs))

    @subscribe.error
    @unsubscribe.error
    async def subscription_no_argument(self, ctx, error):
        if isinstance(error, commands.UserInputError):
            await ctx.send(messages.subscriptions_missing_argument)

    @subscriptions.error
    async def subscription_no_argument(self, ctx, error):
        if isinstance(error, commands.UserInputError):
            await ctx.send(messages.subscriptions_bad_argument)


def setup(bot):
    bot.add_cog(Subscriptions(bot))
