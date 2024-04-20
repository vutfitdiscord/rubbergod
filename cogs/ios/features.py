from __future__ import annotations

import datetime
import re
from enum import Enum

import disnake

import utils
from database import session
from database.verification import PermitDB, ValidPersonDB
from features.list_message_sender import send_list_of_messages


def running_for(time: str, time_dom: str) -> int:
    now = datetime.datetime.now()
    time_list = time.split(":")
    if len(time_list) == 2 or len(time_list) == 3:
        hours = now.hour - int(time_list[0])
        minutes = now.minute - int(time_list[1])
        return hours * 60 + minutes
    else:
        if time_dom:
            time_list[0] = "".join([time, time_dom])
        try:
            date = datetime.datetime.strptime(time_list[0], "%b%d")
        except ValueError:
            date = datetime.datetime.strptime(time_list[0], "%a%d")
            date = date.replace(year=now.year, month=now.month)
        minutes = int((now - date.replace(year=now.year)).total_seconds()) // 60
        # subtracting a day as to assume it was ran right before midnight
        return minutes - 1440


def unchanged_for(date_str: str, format_str: str) -> int:
    now = datetime.datetime.now()
    date = datetime.datetime.strptime(date_str, format_str)
    return int((now - date.replace(year=now.year)).total_seconds()) // 60


# filter people and keep only those containing "BIT" or "FEKT" in person.year
def filter_year(resources: dict[RESOURCE_TYPE, dict]) -> dict[RESOURCE_TYPE, dict]:
    # get unique logins and people objects from db
    logins = set(login for res_data in resources.values() for login in res_data.keys())
    people = {
        login: session.query(ValidPersonDB).filter(ValidPersonDB.login == login).one_or_none()
        for login in logins
    }

    # keep only people with "BIT" or "FEKT" in their person.year
    out_res: dict[RESOURCE_TYPE, dict] = {res_type: {} for res_type in resources.keys()}
    for res_type, res_data in resources.items():
        for login, data in res_data.items():
            if not people.get(login) or "BIT" in people[login].year or "FEKT" in people[login].year:
                out_res[res_type][login] = data
    return out_res


def parse_memory(memory: str) -> dict:
    parsed: dict = {}
    for line in memory.strip().splitlines():
        line_split = line.split()
        login = line_split[1]
        if not login.startswith("x"):
            continue
        last_change = " ".join(line_split[-3:])
        since_last_change = unchanged_for(last_change, "%b %d %H:%M:%S")
        if since_last_change > 10:
            if login not in parsed:
                parsed[login] = list()
            parsed[login].append(since_last_change)
    return parsed


def parse_semaphores(semaphores: str) -> tuple[dict, dict[str, tuple[list, bool]]]:
    parsed: dict = {}
    parsed_files: dict[str, tuple[list, bool]] = {}
    if "soubory semaforu" in semaphores:
        semaphores, files = semaphores.split("soubory semaforu:\n")
    else:
        files = ""

    for line in semaphores.strip().splitlines():
        line_split = line.split()
        login = line_split[1]
        if not login.startswith("x"):
            continue
        last_change = " ".join(line_split[-4:-1])
        since_last_change = unchanged_for(last_change, "%b %d %H:%M:%S")
        if since_last_change > 10:
            if login not in parsed:
                parsed[login] = list()
            parsed[login].append(since_last_change)

    for line in files.strip().splitlines():
        line_split = line.split()
        login = line_split[2]
        if not login.startswith("x"):
            continue
        last_change = " ".join(line_split[5:7])
        name = line_split[7]
        since_last_change = unchanged_for(last_change, "%m-%d %H:%M")
        if since_last_change > 10 or login not in name:
            if login not in parsed_files:
                parsed_files[login] = (list(), False)
            parsed_files[login][0].append(since_last_change)
            if login not in name:
                parsed_files[login] = (parsed_files[login][0], True)

    return parsed, parsed_files


def parse_processes(processes: str) -> dict:
    parsed: dict = {}
    for line in processes.strip().splitlines():
        line_split = line.split()
        login = line_split[0]
        if not login.startswith("x"):
            continue
        time = line_split[8]
        time_dom = line_split[9]
        uptime = running_for(time, time_dom)
        if uptime > 10:
            if login not in parsed:
                parsed[login] = list()
            parsed[login].append(uptime)
    return parsed


def filter_processes(processes: str) -> str:
    out = []
    for line in processes.strip().splitlines():
        if re.search(r"/[a-zA-Z0-9.]+ \d+ \d+ \d+ \d+ \d+$", line):
            out.append(line)
    return "\n".join(out)


def format_time(minutes: int) -> str:
    hours = minutes / 60
    days = hours / 24
    weeks = days / 7
    months = days / 30
    years = months / 12

    if years >= 1:
        return f"{round(years, 1)} roků"
    elif months >= 1:
        return f"{round(months, 1)} měsíců"
    elif weeks >= 1:
        return f"{round(weeks, 1)} týdnů"
    elif days >= 1:
        return f"{round(days, 1)} dní"
    elif hours >= 1:
        return f"{round(hours, 1)} hodin"
    return f"{round(minutes, 1)} minut"


class RESOURCE_TYPE(Enum):
    MEMORY = "MEMORY"
    SEMAPHORE = "SEMAPHORE"
    PROCESS = "PROCESS"
    FILE = "FILE"


# inflected resource names to match the czech language
_inflected_resources = {
    RESOURCE_TYPE.MEMORY: ("sdílená paměť", "sdílené paměti", "ztracené"),
    RESOURCE_TYPE.SEMAPHORE: ("semafory", "semaforů", "ležících"),
    RESOURCE_TYPE.PROCESS: ("procesy", "procesů", "běžících"),
}


def insult_login(parsed_items: dict, system: str, res_type: RESOURCE_TYPE) -> list[str]:
    output_array = []
    for login, array in parsed_items.items():
        user = session.query(PermitDB).filter(PermitDB.login == login).one_or_none()

        if not user:
            msg = (
                f"Na {system} leží {_inflected_resources[res_type][0]} "
                f"nějakého `{login}`, co není na serveru."
            )
        else:
            count = len(array)
            avg_time = int(sum(array) // count)

            msg = (
                f"{utils.generate_mention(user.discord_ID)}, máš na "
                f"{system} `{count}` {_inflected_resources[res_type][1]}, "
                f"{_inflected_resources[res_type][2]} průměrně `{format_time(avg_time)}`."
            )
        output_array += [msg]
    return output_array


def insult_login_shm(parsed_files: dict, system: str) -> list[str]:
    output_array = []
    for login, data in parsed_files.items():
        user = session.query(PermitDB).filter(PermitDB.login == login).one_or_none()
        array, login_not_in_name = data

        if not user:
            msg = f"Na {system} leží soubory semaforů nějakého `{login}`, co není na serveru."
        else:
            count = len(array)
            avg_time = int(sum(array) // count)

            msg = (
                f"{utils.generate_mention(user.discord_ID)} "
                f"máš na {system} (`/dev/shm`) `{count}` souborů semaforů."
            )
            if avg_time > 9:
                msg += f"\n\t\tLeží ti tam průměrně už `{format_time(avg_time)}`"
            if login_not_in_name:
                msg += "\n\t\tNemáš v názvu tvůj login, takže můžeš mit kolize s ostatními."
        output_array += [msg]
    return output_array


async def print_output(
    channel: disnake.TextChannel, system: str, resources: dict[RESOURCE_TYPE, dict]
) -> None:
    out_arr = []
    for res_type in [RESOURCE_TYPE.MEMORY, RESOURCE_TYPE.SEMAPHORE, RESOURCE_TYPE.PROCESS]:
        if resources.get(res_type):
            out_arr += insult_login(resources[res_type], system, res_type)
    if shm_resources := resources.get(RESOURCE_TYPE.FILE):
        out_arr += insult_login_shm(shm_resources, system)

    if not any(resources.values()):
        await channel.send(f"Na {system} uklizeno <:HYPERS:493154327318233088>")
    else:
        await send_list_of_messages(channel, out_arr)
