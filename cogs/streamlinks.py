import discord
from discord.ext import commands
from repository.stream_links_repo import StreamLinksRepo
from config import app_config, cooldowns
from config.messages import Messages
from typing import List, Union
import shlex
import utils
from repository.database.stream_link import StreamLink
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from features.reaction_context import ReactionContext
from features.prompt import PromptSession

# Pattern: "AnyText | [Subject] Page: CurrentPage / {TotalPages}"
pagination_regex = re.compile(r'^\[([^\]]*)\]\s*Page:\s*(\d*)\s*\/\s*(\d*)')


class StreamLinks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repo = StreamLinksRepo()
        self.config = app_config.Config

    @cooldowns.default_cooldown
    @commands.group(brief=Messages.streamlinks_brief, usage="<subject>")
    async def streamlinks(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            parameters = ctx.message.content[len('streamlinks') + 1:].strip()
            params_arr = shlex.split(parameters)
            if len(params_arr) == 1:
                await self.get_streamlinks(ctx, params_arr[0])
            else:
                await ctx.reply(f"{utils.get_command_group_signature(ctx)}\n{ctx.command.brief}")

    async def get_streamlinks(self, ctx: commands.Context, subject: str):
        streamlinks = self.repo.get_streamlinks_of_subject(subject.lower())

        if len(streamlinks) == 0:
            await ctx.reply(content=Messages.streamlinks_no_stream)
            return

        embed = self.create_embed_of_link(streamlinks[0], ctx.author, len(streamlinks), 1)
        message: discord.Message = await ctx.reply(embed=embed)
        await utils.add_pagination_reactions(message, len(streamlinks))

    @commands.check(utils.helper_plus)
    @streamlinks.command(brief=Messages.streamlinks_add_brief)
    async def add(self, ctx: commands.Context, subject: str, link: str,
                  user: Union[discord.User, discord.Member, str], *args):
        try:
            await ctx.message.add_reaction(self.config.emote_loading)

            username = user if type(user) == str else user.display_name
            link = utils.clear_link_escape(link)
            args = list(args)

            if self.repo.exists_link(link):
                await self.replace_reaction(ctx, "❌")
                await ctx.reply(utils.fill_message('streamlinks_add_link_exists', user=ctx.author.id))
                return

            link_data = self.get_link_data(link)
            if link_data['upload_date'] is None:
                try:
                    link_data['upload_date'] = datetime.strptime(args[0], '%Y-%m-%d')
                    del args[0]
                except ValueError:
                    link_data['upload_date'] = datetime.utcnow()
            else:
                if utils.is_valid_datetime_format(args[0], '%Y-%m-%d'):
                    del args[0]

            self.repo.create(subject.lower(), link, username,
                             " ".join(args), link_data['image'], link_data['upload_date'])
            await ctx.reply(content=Messages.streamlinks_add_success)
            await self.replace_reaction(ctx, "✅")
        except:  # noqa: E722
            await self.replace_reaction(ctx, "❌")
            raise

    @streamlinks.command(brief=Messages.streamlinks_list_brief)
    async def list(self, ctx: commands.Context, subject: str):
        streamlinks: List[StreamLink] = self.repo.get_streamlinks_of_subject(subject.lower())

        if len(streamlinks) == 0:
            await ctx.reply(content=Messages.streamlinks_no_stream)
            return

        msg = ""
        groups = []
        for stream in streamlinks:
            at = stream.created_at.strftime("%d. %m. %Y")
            stream_msg: str = f"**{stream.member_name}** ({at}): <{stream.link}> - {stream.description}\n"

            if len(msg) + len(stream_msg) > 2000:
                groups.append(msg)
                msg = stream_msg
            else:
                msg = msg + stream_msg

        if len(msg) > 0:
            groups.append(msg)

        await ctx.reply(content=groups[0])
        del groups[0]
        for group in groups:
            await ctx.send(group)

    async def log(self, stream, user):
        embed = discord.Embed(title="Odkaz na stream byl smazán", color=0xEEE657)
        embed.add_field(name="Provedl", value=user.name)
        embed.add_field(name="Předmět", value=stream.subject.upper())
        embed.add_field(name="Od", value=stream.member_name)
        embed.add_field(name="Popis", value=stream.description)
        embed.add_field(name="Odkaz", value=f"[{stream.link}]({stream.link})", inline=False)
        embed.timestamp = datetime.utcnow()
        channel = self.bot.get_channel(self.config.log_channel)
        await channel.send(embed=embed)

    @commands.check(utils.helper_plus)
    @streamlinks.command(brief=Messages.streamlinks_remove_brief)
    async def remove(self, ctx: commands.Context, id: int):
        if not self.repo.exists(id):
            await ctx.reply(Messages.streamlinks_not_exists)
            return

        stream = self.repo.get_stream_by_id(id)
        link = stream.link

        prompt_message = utils.fill_message('streamlinks_remove_prompt', link=link)
        result = await PromptSession(self.bot, ctx, prompt_message, 60).run()

        if result:
            await self.log(stream, ctx.author)
            self.repo.remove(id)
            await ctx.reply(utils.fill_message('streamlinks_remove_success', link=link))

    def get_link_data(self, link: str):
        """
        Gets thumbnail from youtube or maybe from another service.
        It downloads HTML from link and tries get thumbnail url from SEO meta tags.
        """
        data = {
            'image': None,
            'upload_date': None
        }

        session = requests.Session()
        retry = Retry(connect=5, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        response = session.get(link)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        form = soup.select('form', {'action': 'https://consent.youtube.com/s'})
        if len(form) > 0:
            # Consent check detected. Will try to pass...
            params = form[0].select('input', {'type' : 'hidden'})
            pars = {}
            for par in params:
                if 'name' in par.attrs:
                    pars[par.attrs['name']] = par.attrs['value']
            session.post("https://consent.youtube.com/s", data=pars)
            response = session.get(link)
            if response.status_code != 200:
                return None
            soup = BeautifulSoup(response.content, 'html.parser')
        meta_tags = soup.select('meta')

        for meta in meta_tags:
            if 'property' in meta.attrs and meta.attrs['property'] == 'og:image':
                data['image'] = meta.attrs['content']
            if 'itemprop' in meta.attrs and meta.attrs['itemprop'] in ['datePublished', 'uploadDate']:
                data['upload_date'] = datetime.strptime(meta.attrs['content'], '%Y-%m-%d')

        return data

    async def replace_reaction(self, ctx: commands.Context, emoji: str):
        try:
            await ctx.message.clear_reactions()
            await ctx.message.add_reaction(emoji)
        except discord.HTTPException:
            pass

    def create_embed_of_link(self, streamlink: StreamLink, author: Union[discord.User, discord.Member],
                             links_count: int, current_pos: int) -> discord.Embed:
        embed = discord.Embed(color=0xEEE657)
        embed.set_author(name="Streamlinks")

        if streamlink.thumbnail_url is not None:
            embed.set_image(url=streamlink.thumbnail_url)

        embed.add_field(name="Předmět", value=streamlink.subject.upper(), inline=True)
        embed.add_field(name="Od", value=streamlink.member_name, inline=True)
        embed.add_field(name="Datum vydání", value=streamlink.created_at.strftime("%d. %m. %Y"), inline=True)
        embed.add_field(name="Odkaz", value=f"[{streamlink.link}]({streamlink.link})", inline=False)
        embed.add_field(name="Popis", value=streamlink.description, inline=False)
        embed.timestamp = datetime.utcnow()
        utils.add_author_footer(embed, author, additional_text=[
                                f"[{streamlink.subject.upper()}] Page: {current_pos} / {links_count}"
                                f" (#{streamlink.id})"])

        return embed

    async def handle_reaction(self, ctx: ReactionContext):
        if ctx.emoji not in ["⏪", "◀", "▶", "⏩"]:
            return
        try:
            if ctx.reply_to is None:  # Reply is required to render embed.
                await ctx.message.edit(content=Messages.streamlinks_missing_original, embed=None)
                return

            embed: discord.Embed = ctx.message.embeds[0]
            footer_text = embed.footer.text.split('|')[1].strip()
            match = pagination_regex.match(footer_text)

            if match is None:
                await ctx.message.edit(content=Messages.streamlinks_unsupported_embed, embed=None)
                return  # Invalid or unsupported embed.

            groups = match.groups()
            subject = str(groups[0]).lower()
            current_page = int(groups[1])
            pages_count = int(groups[2])

            streamlinks = self.repo.get_streamlinks_of_subject(subject)

            if len(streamlinks) != pages_count:  # New streamlink was added, but removed.
                await ctx.message.edit(content=Messages.streamlinks_not_actual, embed=None)
                return

            new_page = utils.pagination_next(ctx.emoji, current_page, pages_count)
            if new_page <= 0 or new_page == current_page:
                return  # Pagination to same page. We can ignore.

            # Index - 1, because index position.
            streamlink: StreamLink = streamlinks[new_page - 1]
            embed = self.create_embed_of_link(streamlink, ctx.reply_to.author, len(streamlinks), new_page)
            await ctx.message.edit(embed=embed)
        finally:
            if ctx.message.guild:  # cannot remove reaction in DM
                await ctx.message.remove_reaction(ctx.emoji, ctx.member)

    @add.error
    async def streamlinks_add_error(self, ctx: commands.Context, error):
        if isinstance(error, discord.ext.commands.MissingRequiredArgument):
            await ctx.reply(Messages.streamlinks_add_format)

    @remove.error
    async def streamlinks_remove_error(self, ctx: commands.Context, error):
        if isinstance(error, discord.ext.commands.MissingRequiredArgument):
            await ctx.reply(Messages.streamlinks_remove_format)

    @list.error
    async def streamlinks_list_error(self, ctx: commands.Context, error):
        if isinstance(error, discord.ext.commands.MissingRequiredArgument):
            await ctx.reply(f"{Messages.streamlinks_list_format}\n{ctx.command.brief}")


def setup(bot):
    bot.add_cog(StreamLinks(bot))
