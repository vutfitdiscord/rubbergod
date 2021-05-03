import discord
from typing import Union, Iterable
import utils

async def send_list_of_messages(channel:Union[discord.TextChannel, discord.Object],
                                message_list:Iterable, max_msg_len:int=1900):
    if max_msg_len > 2000: max_msg_len = 2000
    if max_msg_len < 1: max_msg_len = 1

    output_arr = []
    for it in message_list:
        if len(it) > max_msg_len:
            output_arr.extend(utils.split_to_parts(it, max_msg_len))
        else:
            output_arr.append(it)

    output_message = ""

    for msg in output_arr:
        tmp_msg = output_message + msg

        if len(tmp_msg) >= max_msg_len:
            await channel.send(output_message[:-1])
            output_message = msg
        else:
            output_message = tmp_msg

    if output_message != "":
        await channel.send(output_message[:-1])