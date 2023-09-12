# Discord bot for the BUT FIT Discord server

## About

This bot manages the verification process, karma and a bunch of other simple commands
on our [BUT FIT Discord server](https://discord.com/invite/vutfit). It is written in Python with the help of [Disnake](https://docs.disnake.dev/en/latest/index.html) and its DB runs on PostgreSQL with ORM.

Since the most of the features are custom-made, we
wouldn't recommend using it for different servers.

## Setup

### Creating a Discord App

Before you proceed to the environment setup, you will need to create a Discord application
to get the Discord API key. We will not provide you with the exact steps on how to do this as there already exists this
[awesome guide](https://docs.disnake.dev/en/latest/discord.html)
from the developers of Disnake, Discord API Python library.

- When creating an invite URL in the [Inviting Your Bot](https://docs.disnake.dev/en/latest/discord.html#inviting-your-bot) section,
the `bot` and `applications.commands` scopes are required. We also strongly recommend choosing `Administrator` in the __Bot permissions__
as it is hard to figure out which of these permissions you actually need for the development.

> You should set up a separate server just for the development purposes so it shouldn't be that much of a security risk anyway.

- After you create the Discord application, one additional step is required.
You will also need to enable `SERVER MEMBERS INTENT` in __Bot__ tab:

![image](https://user-images.githubusercontent.com/16971100/224842973-efa05793-31a4-4e88-b2da-8bc864d6adcb.png)

> You can do this by going to the [Discord Developer Portal](https://discord.com/developers/applications) and selecting your newly created application.
Then click on the __Bot__ tab on the left and scroll down to the __Privileged Gateway Intents__ section.

### Installing and running the bot

Start by cloning the repo:

```bash
git clone https://github.com/Toaster192/rubbergod.git
cd rubbergod
```

> If you want to contribute to this project, refer to the [contribution](#contribution) section first.

#### Configuration

```bash
cp config/config.template.toml config/config.toml
```

Now open the `config.toml` file in your editor. Insert the Discord API key you obtained earlier in the setup process:
```
1 [base]
2 command_prefix = ['?', '!']
3 default_prefix = '?'
4 ignored_prefixes = ['!']
5 key = '<Your Discord API key>'
...
```

> __Be careful.__ Bad things will happen if anyone else gets a possession of this key. Do not share it with anyone, ever!

On the next two lines, insert your Discord user and server ID so you get administrator rights over the bot:

```
6 admin_ids = [<Your Discord user ID>]
7 guild_id = <Your Server ID here>
```

> [Where can I find my User/Server/Message ID?](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-)

Then, create the following 5 channels (or use one channel for all of them) on your server and paste their IDs to the config:

```
58 log_channel = <Channel ID>
59 bot_dev_channel = <Channel ID>
60 vote_room = <Channel ID>
61 bot_room = <Channel ID>
62 mod_room = <Channel ID>
```

(Optional) For some features you will also need to set other config variables, usually they are divided into categories based on cogs.

--------------------------------------

### Docker setup (recommended)

Install Docker & Docker Compose V2 by going to their [official documentation](https://docs.docker.com/engine/install/). Just select your OS and follow the steps.

> You can also install Docker as a GUI App — Docker Desktop — which includes everything you need.

- If you haven't already, enable `docker` service on startup: `sudo systemctl enable --now docker.service`. Most installers should do that automatically, though.
- To use Docker without `sudo`, you also need to be in `docker` group (eg. `sudo usermod -aG docker $USER && newgrp docker`).
- It's recommended to restart your system at this point (to get all the permissions and other stuff right).

#### a. Dev containers in VS Code (one click run) — preferred option

If you are using VS Code, you can simply run Rubbergod by using the [Dev containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension.
Either by clicking on a notification or by clicking on arrows in bottom left corner (Open a Remote Window) and choosing `Reopen in container`.

#### b. Docker Compose CLI — if you don't use VS Code

This command should do the trick:

```bash
docker compose up
```

**Note:** We use the newer Compose V2 here. If the above command doesn't work, please install Compose V2: `docker-compose-plugin`. As a second option, you can install and use (now deprecated) `docker-compose` command instead.

Docker will download all the necessary stuff and run the container. If you did everything correctly, bot will connect to the DB, load all the extensions and print `Ready` at the end. It will also send `:peepowave:` emoji to the `#bot-room` if you configured one. You're now all set!

--------------------------------------

### Development

If you didn't run the container in detached mode, just press `Ctrl+C` to stop it.

Try to tweak some command a little bit and run the bot again, this time you can try to open it in detached mode so it won't block your terminal:

```bash
docker compose up --detach
```

**Note:** You can use shorter `-d` instead of `--detach`.

> If you changed some internal command logic, it should be applied instantly. If, however, your change involves Discord-side API changes — command name change, for example — it can take longer (few minutes to a few hours in extreme cases).

To stop the detached container, use this command:

```bash
docker compose down
```

### Tips (optional)

> These things are not necessary for development but can help from time to time.

#### Enable commands sync debug

To enable command synchronization debug logging, change the following setting in `rubbergod.py` to `True`:

```python
command_sync_flags = commands.CommandSyncFlags()
command_sync_flags.sync_commands_debug = False
```

Database-related tips can be found in [database README](database/README.md).

List with all cogs, their commands and tasks can be found in [cog README](cogs/README.md).

--------------------------------------

### Local setup (not recommended)

Install the required Python modules (`venv` / `--user` flag recommended):

```bash
pip3 install -r requirements.txt
```

Run the bot (might want to use `nohup` or something):

```bash
python3 rubbergod.py
```

#### Required/recommended packages (apt)

```bash
git
python3.8
python3.8-dev
python3-pip
postgresql
postgresql-contrib
libpq-dev
```
--------------------------------------

## Contribution

To participate in the development, you need to create a fork and send us your contributions through "Pull requests". You can read more in [About forks](https://docs.github.com/en/get-started/quickstart/fork-a-repo#about-forks) and [Creating a pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) guides directly from GitHub. It may look scary at the first moment, but don't worry, it's actually pretty simple. If you don't know where to start, we can help you on Discord (mentioned below).

#### `pre-commit` (useful for contributors)

We use `pre-commit` for lint check before each commit. Use it by running these commands:

```bash
pip install -r requirements-dev.txt
pre-commit install
```

## Authors

* [Matthew](https://github.com/matejsoroka)
* [Toaster](https://github.com/toaster192)
* [Fpmk](https://github.com/TheGreatfpmK)
* [peter](https://github.com/peterdragun)
* [Urumasi](https://github.com/Urumasi)
* [Leo](https://github.com/ondryaso)
* [sinus-x](https://github.com/sinus-x)
* [Solumath](https://github.com/solumath)

**Pull requests, issues or tips for new features are very much welcome!**

## Discord development channel

#### Got stuck with the above steps? Any questions?

You can discuss bot-related stuff in the [`#bot-development`](https://discord.com/channels/461541385204400138/597009137905303552) channel on the [BUT FIT Discord server](https://discord.com/invite/vutfit).

## Other bots

[GrillBot](https://github.com/GrillBot) — our 2nd Discord bot almost entirely developed and maintained by [@Misha12](https://github.com/Misha12) aka Hobit.

[Pumpkin.py](https://github.com/pumpkin-py/pumpkin-py) — Highly modular Discord bot created by folks at BUT FEEC.

## License

This project is licensed under the GNU GPL v.3 License.
