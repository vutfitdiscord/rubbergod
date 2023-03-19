from typing import Iterable, Union

import disnake
from disnake.ext import commands

import utils


# Take care of single messages larger than message len limit
def trim_messages(message_list: Iterable, max_msg_len: int):
    assert isinstance(max_msg_len, int)
    if max_msg_len < 1:
        return []

    output_arr = []
    for it in message_list:
        if len(it) > max_msg_len:
            output_arr.extend(utils.split_to_parts(it, max_msg_len))
        else:
            output_arr.append(it)
    return output_arr


# Merge messages and add newline char between them
def merge_messages(message_list: Iterable, max_msg_len: int):
    assert isinstance(max_msg_len, int)
    if max_msg_len < 1:
        return []

    messages = []

    output_message = ""
    for msg in message_list:
        if len(msg) > max_msg_len:
            return []
        if output_message and output_message[-1] != "\n":
            output_message += "\n"

        tmp_msg = output_message + msg

        if len(tmp_msg) > max_msg_len:
            messages.append(output_message.rstrip())
            output_message = msg
        else:
            output_message = tmp_msg

    if output_message != "":
        messages.append(output_message.rstrip())

    return messages


##
# @brief Send bunch of messages at once
#
# Send all messages from @p message_list to @p channel. Each message from @p message_list will
# have its own line but they will be merged message/s as large as possible limited by @p max_msg_len.
# @p max_msg_len minimal value is 2 because new line chars are counted too.
#
# @param channel any text channel where messages will be send
# @param message_list list of messages to send
# @param max_msg_len maximal length of message
#
async def send_list_of_messages(channel: Union[disnake.TextChannel, disnake.Object, commands.Context],
                                message_list: Iterable, max_msg_len: int = 1900):
    assert isinstance(max_msg_len, int)
    if max_msg_len > 2000:
        max_msg_len = 2000
    if max_msg_len < 2:
        max_msg_len = 2

    message_list = trim_messages(message_list, max_msg_len - 1)
    message_list = merge_messages(message_list, max_msg_len - 1)

    for idx, message in enumerate(message_list):
        if idx == 0 and type(channel) is commands.Context:
            await channel.reply(message)
        else:
            await channel.send(message)
