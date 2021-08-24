import asyncio

import discord
import requests
import json
import time
import math
from requests import request
from mcuuid import MCUUID
from discord.ext import commands, tasks
from discord.ext.commands.errors import CommandNotFound
from utils.JsonIO import JsonIO
from utils import DataEncription

with open(mode='rb', file='data/private_keys.json') as file_f:
    raw = DataEncription.decrypt(file_f.read(), 'data').decode()
    private_keys = json.loads(raw)
client = commands.Bot(command_prefix=private_keys['prefix'], help_command=None)
debugging = False


@client.event
async def on_ready():
    await init()
    update_online_status.start()
    await client.change_presence(activity=discord.Game(name="Alien Arcadium solo"))
    print('ready')


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.channel.id == 877512494468444211 and not message.content.startswith('!yasuna mcid'):
        await queue_delete(message)
        return
    await client.process_commands(message)


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        if ctx.channel.id == 877512494468444211:
            return
        await ctx.channel.send('Hey Hey! Please type in so that I understand.'
                               ' To see the list of commands, type `!yasuna help`')
        return
    raise error


# Task
@tasks.loop(seconds=60)
async def update_online_status():
    mcid_io = JsonIO('data/mcid.json')
    mcid_data = mcid_io.read().result()
    embed_id = JsonIO('data/profile.json').read().result()['online_embed_id']
    t_channel = client.get_channel(id=877512494468444211)
    embed = discord.Embed(title='Current online status of players')
    if len(mcid_data) == 0:
        embed.add_field(
            name='O-no!',
            value='Looks like theres noone in the list of mcid!'
        )

    for str_usr_id in mcid_data:
        player_stats = requests.get(
            url='https://api.hypixel.net/status',
            params={
                'key': private_keys['hypixel_api_key'],
                'uuid': mcid_data[str_usr_id]['uuid']
            }
        ).json()
        this_guild = client.get_guild(id=740308010517135470)
        online_role = discord.utils.get(this_guild.roles, name='Online')
        offline_role = discord.utils.get(this_guild.roles, name='Offline')
        try:
            status = online_role if player_stats['session']['online'] else offline_role
        except:
            status = offline_role
        try:
            user = await client.fetch_user(int(str_usr_id))
        except:
            user = str_usr_id
        embed.add_field(
            name=mcid_data[str_usr_id]['name'],
            value=f'{user if isinstance(user, str) else user.mention} - {status.mention}',
            inline=False
        )
    t_embed = await t_channel.fetch_message(embed_id)
    await t_embed.edit(embed=embed)
    pass


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


@client.command()
async def mcid(ctx, *args):
    t_channel = client.get_channel(id=877512494468444211)
    if ctx.channel.id != t_channel.id:
        await ctx.message.delete()
        return
    mcid_io = JsonIO('data/mcid.json')
    if len(args) > 0:
        mcid_data = mcid_io.read().result()
        if args[0] == 'set' and len(args) > 1:
            if str(ctx.author.id) in mcid_data:
                mess = await t_channel.send(f'You already set your mcid as {mcid_data[str(ctx.author.id)]["name"]}. \n'
                                            f'Type `!yasuna mcid remove` to remove mcid you set')
                await queue_delete(mess, ctx.message)
                return
            mc_player = MCUUID(name=args[1])
            try:
                mc_uuid = mc_player.uuid
                mc_name = mc_player.name
            except:
                mess = await t_channel.send(f'Player {args[1]} could not be found :(')
                await queue_delete(mess, ctx.message)
                return
            mcid_io.write(
                data={
                    str(ctx.author.id): {
                        "name": mc_name,
                        "uuid": mc_uuid
                    }
                }
            ).result()
            mess = await t_channel.send(f'Your mcid is set as {mc_name}')
            await queue_delete(mess, ctx.message)
            return
        elif args[0] == 'remove':
            if str(ctx.author.id) not in mcid_data:
                mess = await t_channel.send('You have not set your mcid yet.\n'
                                            'Type `!yasuna mcid set <your_mcid>` to set your mcid')
                await queue_delete(mess, ctx.message)
                return
            mcid_io.write(data={
                str(ctx.author.id): -1
            },
            removeMode=True).result()
            mess = await t_channel.send('Your mcid is removed.')
            await queue_delete(mess, ctx.message)
            return
        elif args[0] == 'force':
            if discord.utils.get(ctx.guild.roles, name='admin') not in ctx.author.roles:
                await queue_delete(ctx.message)
                return
            if len(args) > 2:
                mc_player = MCUUID(name=args[2])
                try:
                    mc_name = mc_player.name
                    mc_uuid = mc_player.uuid
                except:
                    mess = await t_channel.send(f'Player {args[2]} could not be found.')
                    await queue_delete(mess, ctx.message)
                    return
                if args[1] == 'add':
                    if mc_name in mcid_data:
                        mess = await t_channel.send(f'Player {mc_name} is already in the list.')
                        await queue_delete(mess, ctx.message)
                        return
                    mcid_io.write(
                        data={
                            mc_name: {
                                'name': mc_name,
                                'uuid': mc_uuid
                            }
                        }
                    ).result()
                    mess = await t_channel.send(f'{mc_name} is added')
                    await queue_delete(mess, ctx.message)
                    return
                elif args[1] == 'remove':
                    if mc_name not in mcid_data:
                        mess = await t_channel.send(f'Player {mc_name} is not in the list.')
                        await queue_delete(mess, ctx.message)
                        return
                    mcid_io.write(
                        data={
                            mc_name: -1
                        },
                        removeMode=True
                    ).result()
                    mess = await t_channel.send(f'{mc_name} is removed.')
                    await queue_delete(mess, ctx.message)
                    return
            mess = await t_channel.send('Usage: `!yasuna mcid force <add|remove> <mcid>`')
            await queue_delete(mess, ctx.message)
            return
    mess = await t_channel.send('Usage: `!yasuna mcid <set|remove> [your_mcid]`')
    await queue_delete(mess, ctx.message)
    return


@client.command(name='get')
async def channel_id(ctx, *args):
    if not len(args) >= 2:
        await ctx.channel.send('Usage: `!yasuna get channel id`')
        return
    if args[0] == 'channel' and args[1] == 'id':
        await ctx.channel.send('`{}` is the id for this channel'.format(ctx.channel.id))
    elif args[0] == 'guild' and args[1] == 'id':
        await ctx.channel.send(f'{ctx.guild.id} is the id for this guild')
    else:
        await ctx.channel.send('Usage: `!yasuna get channel id`')


@client.command()
async def role(ctx, *args):
    if len(args) > 1:
        if args[1].lower() in ['de', 'deadend']:
            t_role = discord.utils.get(ctx.guild.roles, name='Dead End')
        elif args[1].lower() in ['bb', 'badblood']:
            t_role = discord.utils.get(ctx.guild.roles, name='Bad Blood')
        elif args[1].lower() in ['aa', 'alienarcadium']:
            t_role = discord.utils.get(ctx.guild.roles, name='Alien Arcadium')
        elif args[1].lower() in ['zombiezzz']:
            t_role = discord.utils.get(ctx.guild.roles, name='zombiezzz')
        elif args[1].lower() in ['skyblocker']:
            t_role = discord.utils.get(ctx.guild.roles, name='Skyblocker')
        else:
            await ctx.channel.send('Please specify one of: DE, BB, AA, or zombiezzz')
        if args[0] == 'add':
            if t_role in ctx.author.roles:
                await ctx.channel.send('I think you already have that role')
                return
            await ctx.author.add_roles(t_role)
            await ctx.channel.send(f'@{t_role.name} is added to {ctx.author.mention}')
        if args[0] == 'remove':
            if t_role not in ctx.author.roles:
                await ctx.channel.send('You don\'t have the role to remove.')
                return
            await ctx.author.remove_roles(t_role)
            await ctx.channel.send(f'@{t_role.name} is now removed from {ctx.author.mention}')
    else:
        await ctx.channel.send('Usage: `!yasuna role <add|remove> <de|bb|aa|zombiezzz>`')


@client.command()
async def search(ctx, *args):
    if len(args) == 0:
        await ctx.channel.send('Hey hey! please tell me on which player to look for!')
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


@client.command()
async def skyblock(ctx, *args):
    await ctx.channel.send('Fetching from api.')
    dat = requests.get(
        url='https://api.hypixel.net/resources/skyblock/collections',
        params={
            'key': private_keys['hypixel_api_key']
        }
    ).json()
    JsonIO('data/skyblock.json').write(data=dat)
##


async def queue_delete(*messages):
    await asyncio.sleep(10)
    for m in messages:
        await m.delete()


async def init(*args, **kwargs):
    profile_io = JsonIO('data/profile.json')
    online_embed = discord.Embed(title='Online')
    online_channel = client.get_channel(id=877512494468444211)
    oe_id = await online_channel.send(embed=online_embed)

    fin_data = {
        'online_embed_id': oe_id.id
    }
    profile_io.write(data=fin_data, forceWrite=True).result()

def run():
    client.run(private_keys['bot_token'])
