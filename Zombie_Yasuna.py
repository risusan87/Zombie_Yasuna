import discord
import requests
from requests import request
from mcuuid import MCUUID
from discord.ext import commands
from discord.ext.commands.errors import CommandNotFound
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


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await ctx.channel.send('Hey Hey! Please type in so that I understand.'
                               ' To see the list of commands, type `!yasuna help`')
        return
    raise error


## COMMANDS
@client.command(name='help')
async def _help(ctx, *args):
    help_embed = discord.Embed(title='Commands list')
    help_embed.add_field(name='`!yasuna help`', value='Shows this message', inline=False)
    await ctx.channel.send(embed=help_embed)


@client.command(name='get')
async def channel_id(ctx, *args):
    if not len(args) >= 2:
        await ctx.channel.send('Usage: `!yasuna get channel id`')
        return
    if args[0] == 'channel' and args[1] == 'id':
        await ctx.channel.send('`{}` is the id for this channel'.format(ctx.channel.id))
    else:
        await ctx.channel.send('Usage: `!yasuna get channel id`')


@client.command()
async def search(ctx, *args):
    if len(args) == 0:
        await ctx.channel.send('Hey hey! please tell me on which player to look for!')
    embed = discord.Embed()
    mc_player = MCUUID(name=args[0])
    # check mcid provided
    try:
        mc_name = mc_player.name
        mc_uuid = mc_player.uuid
        mc_head = 'https://cravatar.eu/avatar/{}'.format(mc_uuid)
    except:
        embed.set_author(name='Whooooopsy!!',
                         icon_url='https://m.media-amazon.com/images/I/41ri3fE++eL._AC_SY355_.jpg')
        embed.add_field(name='No such player found by that name!',
                        value='Player name mistyped, or they changed to a new name perhaps?')
        await ctx.channel.send(embed=embed)
        return
    # check map and difficulty provided
    search_target = ['General']
    if len(args) >= 2:
        search_target = [
            'DeadEnd' if args[1].lower() in ['de', 'deadend'] else
            'BadBlood' if args[1].lower() in ['bb', 'badblood'] else
            'AlienArcadium' if args[1].lower() in ['aa', 'alienarcadium'] else
            'Genaral'
        ]
        if len(args) >= 3 and search_target[0] not in ['AlienArcadium', 'General']:
            search_target.append(
                'Normal' if args[2].lower() == 'normal' else
                'Hard' if args[2].lower() == 'hard' else
                'RIP' if args[2].lower() == 'rip' else
                'General'
            )
        else:
            search_target.append(
                'General'
            )
    # fetching status from hypixel api
    player_stats = requests.get(
        url='https://api.hypixel.net/player',
        params={
            'key': private_keys['hypixel_api_key'],
            'uuid': mc_uuid
        }
    ).json()
    try:
        player_stats = player_stats['player']['stats']['Arcade']
    except:
        await ctx.channel.send('Could not find Arcade stats for the player!')
        return
    zombie_stats = {
        "stats_type": ''.join(search_target),
        "Wins":
        (player_stats['wins_zombies'] if 'wins_zombies' in player_stats.keys() else 0)
        if search_target[0] == 'General' else
        (player_stats['wins_zombies_deadend'] if 'wins_zombies_deadend' in player_stats.keys() else 0)
        if search_target[0] == 'DeadEnd' and search_target[1] == 'General' else
        (player_stats['wins_zombies_deadend_normal'] if 'wins_zombies_deadend_normal' in player_stats.keys() else 0)
        if search_target[0] == 'DeadEnd' and search_target[1] == 'Normal' else
        (player_stats['wins_zombies_deadend_hard'] if 'wins_zombies_deadend_hard' in player_stats.keys() else 0)
        if search_target[0] == 'DeadEnd' and search_target[1] == 'Hard' else
        (player_stats['wins_zombies_deadend_rip'] if 'wins_zombies_deadend_rip' in player_stats.keys() else 0)
        if search_target[0] == 'DeadEnd' and search_target[1] == 'RIP' else
        (player_stats['wins_zombies_badblood'] if 'wins_zombies_badblood' in player_stats.keys() else 0)

    }
    JsonIO(file='data/zombie_statistics.json').overwrite(data=zombie_stats)
    # setting embed
    embed.set_author(
        name='{name}\'s {stats}'.format(
            name=mc_name,
            stats='General stats\n(Status change since last search)' if search_target[0] == 'General' else
            'stats for {map}{diff}\n(Status change since last search)'.format(
                map=search_target[0],
                diff='' if search_target[0] == 'AlienArcadium' else ' {}'.format(search_target[1])
            )
        ),
        icon_url=mc_head
    )
    embed.add_field(
        name='Wins',
        value=zombie_stats['Wins']
    )
    await ctx.channel.send(embed=embed)


##


async def init(*args, **kwargs):
    pass


def run():
    client.run(private_keys['bot_token'])
