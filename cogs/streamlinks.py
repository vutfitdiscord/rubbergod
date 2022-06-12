import disnake
from disnake.ext import commands
from repository.stream_links_repo import StreamLinksRepo
from config import cooldowns
from config.app_config import config
from config.messages import Messages
from typing import List, Union
import utils
from repository.database.stream_link import StreamLink
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from features.prompt import PromptSession
from features.list_message_sender import send_list_of_messages
from buttons.embed import EmbedView

# Pattern: "AnyText | [Subject] Page: CurrentPage / {TotalPages}"
pagination_regex = re.compile(r'^\[([^\]]*)\]\s*Page:\s*(\d*)\s*\/\s*(\d*)')


class StreamLinks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repo = StreamLinksRepo()

    @cooldowns.default_cooldown
    @commands.group(
        brief=Messages.streamlinks_brief,
        usage="<subject>",
        aliases=["streamlist", "steamlink", "streamlink", "steamlinks", "stream", "steam", "links", "sl"]
    )
    async def streamlinks(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            parameters = ctx.message.content.split()
            if len(parameters) == 2:
                await self.get_streamlinks(ctx, parameters[1])
            else:
                await ctx.reply(f"{utils.get_command_group_signature(ctx)}\n{ctx.command.brief}")

    async def get_streamlinks(self, ctx: commands.Context, subject: str):
        streamlinks = self.repo.get_streamlinks_of_subject(subject.lower())

        if len(streamlinks) == 0:
            await ctx.reply(content=Messages.streamlinks_no_stream)
            return

        embeds = []
        for idx, link in enumerate(streamlinks):
            embeds.append(self.create_embed_of_link(link, ctx.author, len(streamlinks), idx+1))
        view = EmbedView(embeds, timeout=180)
        view.message = await ctx.reply(embed=embeds[0], view=view)

    @commands.check(utils.helper_plus)
    @streamlinks.command(brief=Messages.streamlinks_add_brief)
    async def add(self, ctx: commands.Context, subject: str, link: str,
                  user: Union[disnake.User, disnake.Member, str], *args):
        try:
            await ctx.message.add_reaction(config.emote_loading)

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
                    if len(args) != 0:
                        link_data['upload_date'] = datetime.strptime(args[0], '%Y-%m-%d')
                        del args[0]
                    else:
                        link_data['upload_date'] = datetime.utcnow()
                except ValueError:
                    link_data['upload_date'] = datetime.utcnow()
            else:
                if len(args) != 0 and utils.is_valid_datetime_format(args[0], '%Y-%m-%d'):
                    link_data['upload_date'] = datetime.strptime(args[0], '%Y-%m-%d')
                    del args[0]

            if len(args) == 0:
                await ctx.reply(utils.fill_message('streamlinks_missing_description'))
                return

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

        messages = []
        for stream in streamlinks:
            at = stream.created_at.strftime("%d. %m. %Y")
            messages.append(f"**{stream.member_name}** ({at}): <{stream.link}> - {stream.description}\n")

        await send_list_of_messages(ctx, messages)

    async def log(self, stream, user):
        embed = disnake.Embed(title="Odkaz na stream byl smazán", color=0xEEE657)
        embed.add_field(name="Provedl", value=user.name)
        embed.add_field(name="Předmět", value=stream.subject.upper())
        embed.add_field(name="Od", value=stream.member_name)
        embed.add_field(name="Popis", value=stream.description)
        embed.add_field(name="Odkaz", value=f"[{stream.link}]({stream.link})", inline=False)
        embed.timestamp = datetime.utcnow()
        channel = self.bot.get_channel(config.log_channel)
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
            params = form[0].select('input', {'type': 'hidden'})
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
        except disnake.HTTPException:
            pass

    def create_embed_of_link(self, streamlink: StreamLink, author: Union[disnake.User, disnake.Member],
                             links_count: int, current_pos: int) -> disnake.Embed:
        embed = disnake.Embed(color=0xEEE657)
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

    @add.error
    async def streamlinks_add_error(self, ctx: commands.Context, error):
        if isinstance(error, disnake.ext.commands.MissingRequiredArgument):
            await ctx.reply(Messages.streamlinks_add_format)

    @remove.error
    async def streamlinks_remove_error(self, ctx: commands.Context, error):
        if isinstance(error, disnake.ext.commands.MissingRequiredArgument):
            await ctx.reply(Messages.streamlinks_remove_format)

    @list.error
    async def streamlinks_list_error(self, ctx: commands.Context, error):
        if isinstance(error, disnake.ext.commands.MissingRequiredArgument):
            await ctx.reply(f"{Messages.streamlinks_list_format}\n{ctx.command.brief}")


def setup(bot):
    bot.add_cog(StreamLinks(bot))
