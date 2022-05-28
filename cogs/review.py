import disnake
import datetime
from disnake.ext import commands
import copy

from config.app_config import config
from config.messages import Messages as messages
from config import cooldowns
from repository import review_repo
import utils
from features.review import ReviewManager
from buttons.review import ReviewView
from buttons.embed import EmbedView


class Review(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.manager = ReviewManager(bot)
        self.repo = review_repo.ReviewRepository()

    async def check_member(self, ctx):
        """Check if user is allowed to add/remove new review."""
        guild = self.bot.get_guild(config.guild_id)
        member = guild.get_member(ctx.message.author.id)
        if member is None:
            await ctx.reply(utils.fill_message("review_not_on_server", user=ctx.message.author.mention))
            return False
        roles = member.roles
        verify = False
        for role in roles:
            if config.verification_role_id == role.id:
                verify = True
            if role.id in config.review_forbidden_roles:
                await ctx.reply(utils.fill_message("review_add_denied", user=ctx.message.author.id))
                return False
        if not verify:
            await ctx.reply(utils.fill_message("review_add_denied", user=ctx.message.author.id))
            return False
        return True

    @cooldowns.short_cooldown
    @commands.group(
        aliases=["review", "recenze", "recenzie", "reviev", "rewiev"],
        brief=messages.review_get_brief,
        usage="[subject]"
    )
    async def reviews(self, ctx):
        """Group of commands for reviews.
        If not subcommand is invoked, try to find subject reviews specified by first argument
        """
        if ctx.invoked_subcommand is None:
            # show reviews
            args = ctx.message.content.split()[1:]
            if not args:
                await ctx.reply(messages.review_format)
                return
            subject = args[0]
            embeds = self.manager.list_reviews(ctx.author, subject.lower())
            if len(embeds) == 0:
                await ctx.reply(messages.review_wrong_subject)
                return
            await ctx.reply(embed=embeds[0], view=ReviewView(self.bot, embeds))

    @reviews.command(brief=messages.review_add_brief)
    async def add(self, ctx, subject=None, tier: int = None, *args):
        """Add new review for `subject`"""
        if not await self.check_member(ctx):
            return
        if subject is None or tier is None:
            await ctx.reply(messages.review_add_format)
            return
        if tier < 0 or tier > 4:
            await ctx.reply(messages.review_tier)
            return
        author = ctx.message.author.id
        anonym = False
        if not ctx.guild:  # DM
            anonym = True
        if args:
            args = " ".join(args)
        args_len = len(args)
        if args_len == 0:
            args = None
        if not self.manager.add_review(author, subject.lower(), tier, anonym, args):
            await ctx.reply(messages.review_wrong_subject)
        else:
            await ctx.reply(messages.review_added)

    @reviews.command(brief=messages.review_remove_brief)
    async def remove(self, ctx, subject=None, id: int = None):
        """Remove review from DB. User is just allowed to remove his own review
        For admin it is possible to use 'id' as subject shorcut and delete review by its ID
        """
        if not await self.check_member(ctx):
            return
        if subject is None:
            if utils.is_bot_admin(ctx):
                await ctx.reply(messages.review_remove_format_admin)
            else:
                await ctx.reply(messages.review_remove_format)
        elif subject == "id":
            if utils.is_bot_admin(ctx):
                if id is None:
                    await ctx.reply(messages.review_remove_id_format)
                else:
                    self.repo.remove(id)
                    await ctx.reply(messages.review_remove_success)
            else:
                await ctx.reply(utils.fill_message("insufficient_rights", user=ctx.author.id))
        else:
            subject = subject.lower()
            if self.manager.remove(str(ctx.message.author.id), subject):
                await ctx.reply(messages.review_remove_success)
            else:
                await ctx.reply(messages.review_remove_error)

    @cooldowns.short_cooldown
    @commands.group()
    @commands.check(utils.is_bot_admin)
    async def subject(self, ctx):
        """Group of commands for managing subjects in DB"""
        if ctx.invoked_subcommand is None:
            await ctx.reply(messages.subject_format)
            return

    @subject.command(brief=messages.subject_update_biref)
    async def update(self, ctx):
        """Updates subjects from web"""
        programme_details_link = "https://www.fit.vut.cz/study/field/"
        async with ctx.channel.typing():
            # bachelor
            if not self.manager.update_subject_types(f"{programme_details_link}14451/.cs", False):
                await ctx.reply(messages.subject_update_error)
                return
            # engineer
            for id in range(66, 82):
                if not self.manager.update_subject_types(f"{programme_details_link}144{id}/.cs", True):
                    await ctx.reply(messages.subject_update_error)
                    return
            # NISY with random ID
            if not self.manager.update_subject_types(f"{programme_details_link}15340/.cs", True):
                await ctx.reply(messages.subject_update_error)
                return
            # sports
            self.manager.update_sport_subjects()
            await ctx.reply(messages.subject_update_success)

    @commands.command(aliases=["skratka", "zkratka", "wtf"], brief=messages.shorcut_brief)
    async def shortcut(self, ctx, shortcut=None):
        """Informations about subject specified by its shorcut"""
        if not shortcut:
            await ctx.reply(utils.fill_message("shorcut_format", command=ctx.invoked_with))
            return
        programme = self.repo.get_programme(shortcut.upper())
        if programme:
            embed = disnake.Embed(title=programme.shortcut, description=programme.name)
            embed.add_field(name="Link", value=programme.link)
        else:
            subject = self.repo.get_subject_details(shortcut)
            if not subject:
                subject = self.repo.get_subject_details(f"TV-{shortcut}")
                if not subject:
                    await ctx.reply(messages.review_wrong_subject)
                    return
            embed = disnake.Embed(title=subject.shortcut, description=subject.name)
            if subject.semester == "L":
                semester_value = "Letní"
            if subject.semester == "Z":
                semester_value = "Zimní"
            else:
                semester_value = "Zimní, Letní"
            embed.add_field(name="Semestr", value=semester_value)
            embed.add_field(name="Typ", value=subject.type)
            if subject.year:
                embed.add_field(name="Ročník", value=subject.year)
            embed.add_field(name="Kredity", value=subject.credits)
            embed.add_field(name="Ukončení", value=subject.end)
            if "*" in subject.name:
                embed.add_field(name="Upozornění", value="Předmět není v tomto roce otevřen", inline=False)
            if subject.shortcut.startswith("TV-"):
                embed.add_field(
                    name="Rozvrh předmětu v IS",
                    value=f"https://www.vut.cz/studis/student.phtml?sn=rozvrhy&action=gm_rozvrh_predmetu&operation=rozvrh&predmet_id={subject.card}&fakulta_id=814",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Karta předmětu",
                    value=f"https://www.fit.vut.cz/study/course/{subject.shortcut}/.cs",
                    inline=False
                )
                embed.add_field(
                    name="Statistika úspěšnosti předmětu",
                    value=f"http://fit.nechutny.net/?detail={subject.shortcut}",
                    inline=False,
                )

        utils.add_author_footer(embed, ctx.author)
        await ctx.reply(embed=embed)

    @commands.command(brief=messages.tierboard_brief, description=messages.tierboard_help)
    async def tierboard(self, ctx, type="V", sem="Z", year=""):
        """Board of suject based on average tier from reviews"""
        # TODO autochange sem based on week command?
        degree = None
        type = type.upper()
        sem = sem.upper()
        if type == "HELP" or sem not in ['Z', 'L'] or type not in ['P', 'PVT', 'PVA', 'V']:
            await ctx.reply(f"`{utils.get_command_signature(ctx)}`\n{messages.tierboard_help}")
            return

        author = ctx.author
        if not ctx.message.guild:  # DM
            guild = self.bot.get_guild(config.guild_id)
            author = guild.get_member(author.id)
        for role in author.roles:
            if "BIT" in role.name:
                degree = "BIT"
                if not year and type == "P":
                    if role.name == "4BIT+":
                        year = "3BIT"
                    elif role.name == "0BIT":
                        year = "1BIT"
                    else:
                        year = role.name
                break
            if "MIT" in role.name:
                degree = "MIT"
                if not year and type == "P":
                    year = ""
                    # TODO get programme from DB? or find all MIT P?
                break
        if not degree and not year:
            await ctx.reply(messages.tierboard_missing_year)
            return
        embeds = []
        embed = disnake.Embed(title="Tierboard")
        embed.timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        embed.add_field(name="Typ", value=type)
        embed.add_field(name="Semestr", value="Letní" if sem == "L" else "Zimní")
        if year:
            degree = year
        embed.add_field(name="Program", value=degree)

        utils.add_author_footer(embed, ctx.author, additional_text=("?tierboard help",))

        pages_total = self.repo.get_tierboard_page_count(type, sem, degree, year)
        for page in range(pages_total):
            board = self.repo.get_tierboard(type, sem, degree, year, page*10)
            output = ""
            cnt = 1
            for line in board:
                output += f"{cnt} - **{line.shortcut}**: {round(line.avg_tier, 1)}\n"
                cnt += 1
            embed.description = output
            embeds.append(copy.copy(embed))

        if pages_total == 0:
            embed.description = ""
            embeds.append(embed)

        await ctx.reply(embed=embeds[0], view=EmbedView(embeds))

    @reviews.error
    @subject.error
    async def review_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.reply(messages.review_add_format)
        if isinstance(error, commands.CheckFailure):
            await ctx.reply(utils.fill_message("insufficient_rights", user=ctx.author.id))


def setup(bot):
    bot.add_cog(Review(bot))
