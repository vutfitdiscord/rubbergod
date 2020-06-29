# Discord bot for the VUT FIT discord server

## About

This bot manages the verification process, karma and a bunch of simple commands
on our VUT FIT discord server. Since most of the features are custom-made I
wouldn't recommend using it for different servers.

[Rubbergoddess](https://github.com/sinus-x/rubbergoddess) is a Rubbergod-based
bot used on VUT FEKT discord server.

## Installing and running the bot

Prerequisites:
* Postgresql
* Python3.6+

Start by cloning the repo:
```bash
git clone https://github.com/toaster192/rubbergod.git
cd rubbergod
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

#### Required/recommended packages (apt)

```
git
python3.7
python3.7-dev
python3-pip
postgresql
postgresql-contrib
libpq-dev
```

## Docker compose setup

Install `docker` and `docker-compose` for your system (will vary from system to system)
and run `docker` (`systemctl start docker.service`)

Your user account must be in the `docker` group (eg. `sudo usermod -aG docker $USER`).
This will take effect on next logon.

```bash
docker build .
```

and then everytime you want to run the app

```bash
docker-compose down && docker-compose up --build
```

## Authors

* [Matthew](https://github.com/matejsoroka)
* [Toaster](https://github.com/toaster192)
* [Fpmk](https://github.com/TheGreatfpmK)
* [_peter](https://github.com/peterdragun)
* [Urumasi](https://github.com/Urumasi)
* [Leo](https://github.com/ondryaso)
* [sinus-x](https://github.com/sinus-x)

**Pull requests, issues or tips for new features are very much welcome!**

## License

This project is licensed under the GNU GPL v.3 License.
