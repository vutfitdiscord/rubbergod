# Discord bot for the VUT FIT discord server

## About

This bot manages the verification process, karma and a bunch of simple commands
on our VUT FIT discord server. Since most of the features are custom-made I
wouldn't recommend using it for different servers.

[Rubbergoddess](https://github.com/sinus-x/rubbergoddess) is a Rubbergod-based
bot used on VUT FEKT discord server.

## Creating discord application

Before first run of bot you need to create discord application.
Guide for creating new application and adding bot to your server can be found at
disnake [documentation](https://docs.disnake.dev/en/latest/discord.html)

While creating discord appilication one more step is required.
You will also need to enable `SERVER MEMBERS INTENT` in `Bot` tab.

## Installing and running the bot

Prerequisites:

* Postgresql
* Python3.8+

Start by cloning the repo:

```bash
git clone https://github.com/toaster192/rubbergod.git
cd rubbergod
```

## Docker compose setup (recomended)

Install `docker` and `docker-compose` for your system (will vary from system to system)
and run `docker` (`systemctl start docker.service`)

To run docker user needs to be in `docker` group. (eg. `sudo usermod -aG docker $USER`).

```bash
docker build .
```

and then everytime you want to run the app

```bash
docker-compose down && docker-compose up --build
```

## Local setup (not recommended)

Install the required python modules (`venv` / `--user` flag recommended):

```bash
pip3 install -r requirements.txt
```

Run the bot (might want to use `nohup` or something):

```bash
python3 rubbergod.py
```

### Required/recommended packages (apt)

```bash
git
python3.8
python3.8-dev
python3-pip
postgresql
postgresql-contrib
libpq-dev
```

## Pre-commit (useful for dev)

We have setup pre-commit in this repository. To use it use these commands:

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

## License

This project is licensed under the GNU GPL v.3 License.
