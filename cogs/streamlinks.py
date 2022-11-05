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

subjects = []


async def autocomp_subjects(inter: disnake.ApplicationCommandInteraction, user_input: str):
    return [subject[0] for subject in subjects if user_input.lower() in subject[0]][:25]


class StreamLinks(commands.Cog):
    def __init__(self, bot):
        global subjects
        self.bot = bot
        self.repo = StreamLinksRepo()
        subjects = self.repo.get_subjects_with_stream()

    @cooldowns.default_cooldown
    @commands.group(aliases=[
        "streamlist", "steamlink", "streamlink", "steamlinks", "stream", "steam", "links", "sl"]
        )
    async def streamlinks(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            command_id = utils.get_command_id(self, "streamlinks")
            await ctx.reply(utils.fill_message("moved_command", name="streamlinks", id=command_id))

    @cooldowns.default_cooldown
    @commands.slash_command(name="streamlinks", brief=Messages.streamlinks_brief)
    async def _streamlinks(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @_streamlinks.sub_command(name="get", description=Messages.streamlinks_brief)
    async def streamlinks_get(
        self,
        inter: disnake.ApplicationCommandInteraction,
        subject: str = commands.Param(autocomplete=autocomp_subjects)
    ):
        await inter.response.defer()

        streamlinks = self.repo.get_streamlinks_of_subject(subject.lower())

        if len(streamlinks) == 0:
            await inter.edit_original_message(content=Messages.streamlinks_no_stream)
            return

        embeds = []
        for idx, link in enumerate(streamlinks):
            embeds.append(self.create_embed_of_link(link, inter.author, len(streamlinks), idx+1))
        view = EmbedView(inter.author, embeds, timeout=180)
        view.message = await inter.edit_original_message(embed=embeds[0], view=view)

    @commands.check(utils.helper_plus)
    @_streamlinks.sub_command(name="add", description=Messages.streamlinks_add_brief)
    async def streamlinks_add(
        self,
        inter: disnake.ApplicationCommandInteraction,
        link: str,
        subject: str,
        user: str,
        description: str,
        date: str = commands.Param(default=None, description=Messages.streamlinks_date_format)
    ):
        await inter.response.defer()

        link = utils.clear_link_escape(link)

        if self.repo.exists_link(link):
            await inter.edit_original_message(
                utils.fill_message('streamlinks_add_link_exists', user=inter.author.id)
            )
            return

        # str is discord tag so fetch user and get his name
        if "@" in user:
            user = await utils.get_username_from_tag(self, user)
            user = " & ".join(user)

        link_data = self.get_link_data(link)
        if date is not None:
            link_data['upload_date'] = datetime.strptime(date, '%d.%m.%Y')
        else:
            if link_data['upload_date'] is None:
                link_data['upload_date'] = datetime.utcnow()

        self.repo.create(subject.lower(), link, user,
                         description, link_data['image'], link_data['upload_date'])
        await inter.edit_original_message(content=Messages.streamlinks_add_success)

    @_streamlinks.sub_command(name="list", description=Messages.streamlinks_list_brief)
    async def streamlinks_list(
        self,
        inter: disnake.ApplicationCommandInteraction,
        subject: str = commands.Param(autocomplete=autocomp_subjects)
    ):
        streamlinks: List[StreamLink] = self.repo.get_streamlinks_of_subject(subject.lower())

        if len(streamlinks) == 0:
            await inter.send(content=Messages.streamlinks_no_stream)
            return

        messages = [f"Streamy k **{subject.upper()}**:"]
        for stream in streamlinks:
            at = stream.created_at.strftime("%d. %m. %Y")
            messages.append(f"**{stream.member_name}** ({at}): <{stream.link}> - {stream.description}\n")

        await send_list_of_messages(inter, messages)

    async def log(self, stream, user):
        embed = disnake.Embed(title="Odkaz na stream byl smazán", color=0xEEE657)
        embed.add_field(name="Provedl", value=user.name)
        embed.add_field(name="Předmět", value=stream.subject.upper())
        embed.add_field(name="Od", value=stream.member_name)
        embed.add_field(name="Popis", value=stream.description[:1024])
        embed.add_field(name="Odkaz", value=f"[{stream.link}]({stream.link})", inline=False)
        embed.timestamp = datetime.utcnow()
        channel = self.bot.get_channel(config.log_channel)
        await channel.send(embed=embed)

    @commands.check(utils.helper_plus)
    @_streamlinks.sub_command(name="remove", description=Messages.streamlinks_remove_brief)
    async def streamlinks_remove(
        self,
        inter: disnake.ApplicationCommandInteraction,
        id: int = commands.Param(description=Messages.streamlinks_remove_ID)
    ):

        await inter.response.defer()
        if not self.repo.exists(id):
            await inter.edit_original_message(Messages.streamlinks_not_exists)
            return

        stream = self.repo.get_stream_by_id(id)
        link = stream.link

        prompt_message = utils.fill_message('streamlinks_remove_prompt', link=link)
        result = await PromptSession(self.bot, inter, prompt_message, 60).run()

        if result:
            await self.log(stream, inter.author)
            self.repo.remove(id)
            await inter.channel.send(utils.fill_message('streamlinks_remove_success', link=link))

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
        embed.add_field(name="Popis", value=streamlink.description[:1024], inline=False)
        embed.timestamp = datetime.utcnow()
        utils.add_author_footer(embed, author, additional_text=[
                                f"[{streamlink.subject.upper()}] Page: {current_pos} / {links_count}"
                                f" (#{streamlink.id})"])

        return embed


def setup(bot):
    bot.add_cog(StreamLinks(bot))
