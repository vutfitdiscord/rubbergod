import discord
from discord.ext import commands
import re
import os

import utils
from config.app_config import Config


class DynamicConfig(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.check(utils.is_bot_owner)
    @commands.group(pass_context=True)
    async def config(self, ctx):
        # TODO help
        pass

    @config.command(name='set')
    async def set_value(self, ctx, key, *value):
        await self.change_value(ctx, key, value, False)

    @config.command()
    async def update(self, ctx, key, *value):
        await self.change_value(ctx, key, value, True)

    @config.command(name='list')
    async def list_all(self, ctx):
        keys = dir(Config)
        output = '```'
        for key in keys[:]:
            if not re.match(r"__.*__", key):
                output += key + '\n'
        output += '```'
        await ctx.send(output)

    @config.command()
    async def get(self, ctx, key):
        value = getattr(Config, key)
        embed = discord.Embed(title=key, description=value)
        await ctx.send(embed=embed)

    async def change_value(self, ctx, key, value, append):
        config_path = os.path.dirname(__file__)[:-4] + 'config/config.py'
        with open(config_path, 'r') as fd:
            lines = fd.readlines()
        attrb = getattr(Config, key)
        for i, line in enumerate(lines):
            if re.search('    ' + key + r".*", line):
                if isinstance(attrb, int):
                    lines[i] = '    ' + key + " = " + value
                    value = int(value)
                elif isinstance(attrb, str):
                    lines[i] = '    ' + key + " = '" + value + "'"
                elif isinstance(attrb, list):
                    # look for ] and read whole list in var
                    list_str = ''
                    # read whole list
                    lines_cnt = 0
                    for list_line in lines[i:]:
                        list_str += list_line
                        lines_cnt += 1
                        if re.match(r'.*].*', list_line):
                            break
                    line_str = ''.join(list_str.split())
                    # remove setting name
                    line_str = line_str.split('[')[1]
                    # remove ]
                    line_str = line_str[:-1]
                    line_list = line_str.split(',')
                    value = list(value)
                    # add quotes to string list
                    if isinstance(value[0], str):
                        for j, item in enumerate(value):
                            value[j] = '"' + item + '"'
                    if append:
                        line_list += value
                    else:
                        line_list = value
                    # remove duplicates
                    value = list(dict.fromkeys(line_list))
                    # print list back to config file with correct formatting
                    lines_out = ['    ' + key + " = ["]
                    current_line = '        '
                    for item in value:
                        if len(current_line) + len(item) > 100:
                            lines_out.append(current_line[:-1])
                            current_line = '        '
                        else:
                            current_line += item + ', '
                    lines_out[-1] = lines_out[-1][:-1]
                    lines_out.append('    ]')
                    del lines[i:i+lines_cnt]
                    lines = lines[:i] + lines_out + lines[i:]
                    for line in lines:
                        print(line)
                else:
                    # TODO tuple
                    return # TODO error
                break
        with open(config_path, 'w') as fd:
            fd.writelines(lines)
        setattr(Config, key, value)
        await ctx.send('Config updated')
        # TODO error handlings


def setup(bot):
    bot.add_cog(DynamicConfig(bot))

