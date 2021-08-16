import discord
import requests
import time
import math
from requests import request
from mcuuid import MCUUID
from discord.ext import commands
from discord.ext.commands.errors import CommandNotFound
from utils.JsonIO import JsonIO

private_keys = JsonIO('data/private_keys.json').read().result()
client = commands.Bot(command_prefix=private_keys['prefix'], help_command=None)
debugging = False


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


# COMMANDS
@client.command(name='help')
async def _help(ctx, *args):
    help_embed = discord.Embed(title='Commands list')
    help_embed.add_field(
        name='`!yasuna search <mcid> [map] [difficulty]`',
        value='Shows statistics for zombies.\n'
              'Arguments: map and difficulty are optional.',
        inline=False
    )
    help_embed.add_field(
        name='`!yasuna help`',
        value='Shows this message',
        inline=False
    )
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
        await debug('Process done with an error. Returning null', ctx.channel)
        return
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
    search_target = ['General', 'General']
    if len(args) >= 2:
        search_target = [
            'DeadEnd' if args[1].lower() in ['de', 'deadend'] else
            'BadBlood' if args[1].lower() in ['bb', 'badblood'] else
            'AlienArcadium' if args[1].lower() in ['aa', 'alienarcadium'] else
            'General'
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

    def stats_for(base_key: str) -> int:
        key = '{base}{map}{diff}'.format(
            base=base_key,
            map='' if search_target[0] == 'General' else
            '_deadend' if search_target[0] == 'DeadEnd' else
            '_badblood' if search_target[0] == 'BadBlood' else
            '_alienarcadium',
            diff='' if search_target[0] in ['General', 'AlienArcadium'] else
            '_normal' if search_target[1] == 'Normal' else
            '_hard' if search_target[1] == 'Hard' else
            '_rip' if search_target[1] == 'RIP' else
            ''
        )
        return player_stats[key] if key in player_stats.keys() else 0

    zombie_stats = {
        "Wins": stats_for('wins_zombies'),
        "Rounds survived": stats_for('total_rounds_survived_zombies'),
        "Windows repaired": stats_for('windows_repaired_zombies'),
        "Zombies killed": stats_for('zombie_kills_zombies'),
        "Knocked downs": stats_for('times_knocked_down_zombies'),
        "Deaths": stats_for('deaths_zombies'),
        "K/D ratio": round(
            stats_for('zombie_kills_zombies') / stats_for('deaths_zombies'), 2
        ) if stats_for('deaths_zombies') != 0 else -1,
        "Players revived": stats_for('players_revived_zombies'),
        "Doors opened": stats_for('doors_opened_zombies'),
        "Bullets shot": stats_for('bullets_shot_zombies') if search_target[0] == 'General' else -1,
        "Bullets hit": stats_for('bullets_hit_zombies') if search_target[0] == 'General' else -1,
        "Headshots hit": stats_for('headshots_zombies') if search_target[0] == 'General' else -1,
        "Gun accuracy": round(
            stats_for('bullets_hit_zombies') / stats_for('bullets_shot_zombies') * 100, 2
        ) if stats_for('bullets_shot_zombies') > 0 else -2 if search_target[0] != 'General' else -3,
        "Headshot accuracy": round(
            stats_for('headshots_zombies') / stats_for('bullets_shot_zombies') * 100, 2
        ) if stats_for('bullets_shot_zombies') > 0 else -2 if search_target[0] != 'General' else -3
    }
    game_type = '{map}{difficulty}'.format(
        map=search_target[0],
        difficulty=f'_{search_target[1]}' if search_target[0] not in ('AlienArcadium', 'General') else ''
    )
    record_io = JsonIO(file='data/zombie_statistics.json')
    last_rec = record_io.read().result()
    last_rec = last_rec[mc_uuid][game_type] if mc_uuid in last_rec and game_type in last_rec[mc_uuid] else -1
    delta_stats = {}
    for cat in zombie_stats:
        if last_rec == -1:
            delta_stats[cat] = '±0'
        else:
            val = zombie_stats[cat] - last_rec[cat]
            delta_stats[cat] = '{}{}'.format(
                '+' if val > 0 else '±0' if val == 0 else '',
                str(round(val, 2)) if val != 0 else ''
            )

    record_io.write(
        data={
            mc_uuid: {
                game_type: zombie_stats
            }
        },
        forceWrite=True
    )
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
    for cat in zombie_stats.keys():
        if zombie_stats[cat] != -1 and zombie_stats[cat] != -2:
            embed.add_field(
                name=cat,
                value=
                (f'{zombie_stats[cat]}% ({delta_stats[cat]}%)' if zombie_stats[cat] != -3 else 'N/A')
                if cat in ['Gun accuracy', 'Headshot accuracy'] else
                '{:,} ({})'.format(zombie_stats[cat], delta_stats[cat]),
                inline=False if cat in ['Gun accuracy', 'Headshot accuracy'] else True
            )
    await ctx.channel.send(embed=embed)


##


async def debug_start(starting_mess: str, channel: discord.TextChannel):
    if debugging:
        await channel.send(f'`Debug: {starting_mess}`')
        return time.time()


async def debug_end(end_mess: str, channel: discord.TextChannel, timestamp: float):
    if debugging:
        time_took = round((time.time() - timestamp) * 1000, 2)
        await channel.send(f'`Debug: {end_mess} (took {time_took} millis)`')


async def debug(mess: str, channel: discord.TextChannel):
    if debugging:
        await channel.send(f'`Debug: {mess}`')


async def init(*args, **kwargs):
    pass


def run():
    client.run(private_keys['bot_token'])
