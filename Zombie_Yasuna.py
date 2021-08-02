import discord
from discord.ext import commands
from utils.JsonIO import JsonIO

private_keys = JsonIO('data/private_keys.json').read().result()
client = commands.Bot(command_prefix=private_keys['prefix'], help_command=None)


@client.event
async def on_ready():
    await init()
    print('ready')


@client.event
async def on_message(message):
    await client.process_commands(message)


@client.command(name='help')
async def _help(ctx, *args):
    help_embed = discord.Embed(title='Commands list')
    help_embed.add_field(name='`!yasuna help`', value='Shows this message', inline=False)
    await ctx.channel.send(embed=help_embed)


async def init(*args, **kwargs):
    pass


def run():
    client.run(private_keys['bot_token'])
