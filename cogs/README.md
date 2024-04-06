# Cogs

## Summary

All extensions, also known as cogs, are contained within this folder. The cogs can be dynamically loaded and unloaded at runtime, which allows for the removal or addition of features without requiring the entire bot to be restarted. The `/cogs` command in [system cog](system/cog.py) is responsible for handling this process.

## Must be met

1. All cogs must have their own directory. The directory must contain the `cog.py`, `__init__.py` and `messages_*.py` file. Other files should have prefix e.g. (`features_*.py`, `modals_*.py`, `views_*.py`)
2. Name of the directory represents name of the cog. (if you are adding it to extension in config)
3. All cogs must inherit from [class Base](base.py).
4. File name is lowercase, class name is CamelCase.
5. If there is task in cog it must be initialized in `self.tasks` list.
6. Comment at the beginning of the file summarizing function of cog.
7. All cogs should be included in cogs folder and added to the README with their commands.

## List of Cogs

### [Absolvent](absolvent/cog.py)

Cog for diploma verification. When successful, the user is given Survivor (Bc.) or King (Ing.) role.\
**Commands:**

    - /diplom
    - /diplom help
---

### [AutoPin](autopin/cog.py)

Cog controlling auto pinning of messages and priority pins in channels.\
**Commands:**

    - /pin_mod add
    - /pin_mod remove
    - /pin_mod list
    - /pin get_all
---

### [Bettermeme](bettermeme/cog.py)

Cog for handling memes with X number of reactions to be reposted to a specific channel.\
**Commands:**

    - /better-meme leaderboard
---

### [Bookmark](bookmark/cog.py)

Cog controlling bookmarks. The bot will send copy of message to user.\
**Commands:**

    - react 🔖
    - message_command "Bookmark"
---

### [Contest](contest/cog.py)

Cog for handling vote reactions for contests.\
**Commands:**

    - /contest calculate_contribution
    - /contest top_contributions
    - /contest submit
    - /contest_mod get_author
    - /contest_mod start
    - /contest_mod end

---

### [DynamicConfig](dynamicconfig/cog.py)

Cog for dynamically changing config.\
**Commands:**

    - /config set
    - /config append
    - /config load
    - /config list
    - /config get
    - /config backup
    - /config update
---

### [Emoji](emoji/cog.py)

Cog for managing server emojis. Download emojis and stickers. Get full size of emoji.\
**Commands:**

    - /emoji get_emojis
    - /emoji get_emoji
---

### [Error](error/cog.py)

Cog for handling command errors. This is mostly for logging purposes.
Errors originating from other than commands (such as reaction handlers and listeners) are handled in rubbergod.py `on_error` function.

---

### [Exams](exams/cog.py)

Cog to parse exams data from website and send it to channel.
Available for each year of study.\
**Commands:**

    - /exams
    - /terms
    - /terms update
    - /terms remove_all
    - /terms remove
    - /terms start
    - /terms stop
    - /exams

**Tasks:**

    - update_terms_task
---

### [FitRoom](fitroom/cog.py)

Cog for finding rooms on FIT BUT.\
**Commands:**

    - /room
---

### [FitWide](fitwide/cog.py)

Cog implementing management of year roles and database of user logins.\
**Commands:**

    - /role_check
    - /increment_roles
    - /verify_db update
    - /verify_db pull
    - /verify_db get_login
    - /verify_db get_user
    - /verify_db reset_login
    - /verify_db link_login_user
    - /vutapi
---

### [Forum](forum/cog.py)

Cog managing threads in forums (auto-archive, etc.).

---

### [Fun](fun/cog.py)

Cog containing commands that call random APIs for fun things.\
**Commands:**

    - /cat
    - /dog
    - /fox
    - /duck
    - /dadjoke
    - /yo_mamajoke
    - /fuchs
---

### [Gif](gif/cog.py)

Cog for creating gifs.\
**Commands:**

    - /pet
    - /catnap
    - /bonk
---

### [GrillbotApi](grillbotapi/cog.py)

Functions and commands that communicate with the Grillbot API.

---

### [Help](help/cog.py)

Cog containing help command. Only shows commands that user has access to
and are context commands.\
**Commands:**

    - ?help
---

### [Hugs](hugs/cog.py)

Cog implementing hug commands. Send hug to user and see leaderboard.\
**Commands:**

    - /hug hugboard
    - /hug huggersboard
    - /hug mosthugged
    - /hug me
    - /hug give
---

### [Icons](icons/cog.py)

Cog implementing dynamic icon system. Users can assign themselves icons from a list of roles.\
**Commands:**

    - /icon
---

### [Info](info/cog.py)

Cog containing commands that get basic information from other sources.\
**Commands:**

    - /urban
    - /pocasi
    - /kreditovy_strop
---

### [IOS](ios/cog.py)

Cog for the IOS subject. Get users on merlin/eva server which have blocking processes running.\
**Commands:**

    - /ios
    - /ios_task start
    - /ios_task stop
    - /ios_task cancel
**Tasks:**

    - ios_task
---

### [Karma](karma/cog.py)

Cog implementing karma system. Users can give each other positive/negative karma points with reactions.\
**Commands:**

    - /karma me
    - /karma stalk
    - /karma getall
    - /karma get
    - /karma message
    - /karma leaderboard
    - /karma givingboard
    - /karma_mod revote
    - /karma_mod vote
    - /karma_mod give
    - /karma_mod transfer
    - user_command Karma uživatele
    - message_command Karma zprávy
---

### [Latex](latex/cog.py)

Cog for interpreting latex commands as images.\
**Commands:**

    - ?latex
---

### [Meme](meme/cog.py)

Cog for meme commands.\
**Commands:**

    - /uhoh
---

### [Message](message/cog.py)

Cog for sending and managing messages sent by bot.\
**Commands:**

    - /message send
    - /message resend
    - /message edit
---

### [Moderation](moderation/cog.py)

Cog implementing functions for server moderation and help functions for mods.
Implemented logging for tagging @mods.\
**Commands:**

    - /slowmode set
    - /slowmode remove
---

### [Nameday](nameday/cog.py)

Cog for sending name days and birthdays.\
**Commands:**

    - /svatek
    - /meniny
**Tasks:**

    - send_names
---

### [Random](random/cog.py)

Implementing commands using random module.\
**Commands:**

    - /pick
    - /flip
    - /roll
---

### [Reactions](reactions/cog.py)

Cog for handling reactions and delegating to specific cog.

---

### [Report](report/cog.py)

Cog implementing anonymous reporting from users.
**Commands:**

    - /report general
    - /report message
    - /report google_form
    - /report_mod unban
    - message_command Report message
---

### [Review](review/cog.py)

Cog implementing review system for subjects.\
**Commands:**

    - /review get
    - /review add
    - /review remove
    - /review list
    - /subject update
    - /wtf
    - /tierboard
---

### [Roles](roles/cog.py)

Cog implementing channels and roles management. Copying/creating channels with permissions.\
**Commands:**

    - /add_channels_description
    - /channel copy
    - /channel clone
    - /channel create
    - /channel get_overwrites
    - /channel overwrite_to_role
    - /channel role_to_overwrites
    - /remove_exclusive_roles
---

### [StreamLinks](streamlinks/cog.py)

Cog implementing streamlinks system. List streams for a subject.\
**Commands:**

    - /streamlinks get
    - /streamlinks list
    - /streamlinks_mod add
    - /streamlinks_mod update
    - /streamlinks_mod remove
---

### [Studijni](studijni/cog.py)

Cog implementing information about office hours of the study department.\
**Commands:**

    - /studijni
---

### [Subscriptions](subscriptions/cog.py)

Cog implementing subscriptions to forum posts based on their tags. \
**Commands:**

    - /subscriptions add
    - /subscriptions remove
    - /subscriptions list
---

### [System](system/cog.py)

Core cog for bot. Can't be unloaded. Contains commands for cog management.\
**Commands:**

    - /git pull
    - /get_logs
    - /shutdown
    - /cogs
    - /uptime
---

### [Timeout](timeout/cog.py)

Containing timeout commands and manipulating with timeout.\
**Commands:**

    - /timeout user
    - /timeout remove
    - /timeout list
    - /timeout get_user
    - /selftimeout
**Tasks:**

    - refresh_timeout
---

### [Verify](verify/cog.py)

Cog for verification system. Allows users to verify themselves with xlogin00 and gain access to server.\
**Commands:**

    - /verify
    - /dynamic_verify create
    - /dynamic_verify list
    - /dynamic_verify edit
    - user_command Verify host
---

### [Vote](vote/cog.py)

Cog implementing vote and polls feature.\
**Commands:**

    - ?vote
    - ?singlevote
---

### [Warden](warden/cog.py)

Cog for repost detection.\
**Commands:**

    - ?scan
    - ?scan history
    - ?scan message
---

### [Week](week/cog.py)

Cog containing information about week (odd/even) and its relation to calendar/academic week.
**Commands:**

    - /week
