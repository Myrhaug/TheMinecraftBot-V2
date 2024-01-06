import discord, datetime
from discord.ext import commands
from CodeUtils import embeds
import mccommands
import json
import mcrcon

bot_token = None
servers = None
server_member_role_name = None


def config_reload():
    global bot_token, servers, server_member_role_name
    with open('config.json', 'r') as config:
        config = json.load(config)
    bot_token = str(config["bot_token"])
    servers = config["servers"]
    server_member_role_name = config["server_member_role_name"]


config_reload()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    await bot.add_cog(mccommands.mccommands(bot))

    print(f'Logged in as {bot.user.name}')
    with open('config.json', 'r') as file:
        config_data = json.load(file)

    config_data['bot_name'] = bot.user.name

    with open('config.json', 'w') as file:
        json.dump(config_data, file, indent=4)

    print(f"|✅|{datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S')}| - All Cogs Loaded")

    await bot.tree.sync()
    print(f"|✅|{datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S')}| - bot.tree synced")



@bot.event
async def on_member_update(before, after):
    if server_member_role_name in [role.name for role in after.roles]:
        if server_member_role_name not in [role.name for role in before.roles]:
            await after.send(embed=embeds.MCaddUserEmbed())
            await set_mcname_permission(after, True)

    if server_member_role_name not in [role.name for role in after.roles]:
        if server_member_role_name in [role.name for role in before.roles]:
            await set_mcname_permission(after, False)
            await remove_from_whitelist(after)


async def remove_from_whitelist(member):
    config_reload()
    data = {}
    try:
        with open('user_data.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        pass

    discord_name = str(member)
    minecraft_name = data[discord_name]["minecraft_name"]

    for server in servers:
        rcon = mcrcon.MCRcon(host=str(server["server_ip"]), password=str(server["server_rcon_password"]), port=int(server["server_rcon_port"]))
        rcon.connect()
        rcon.command(f'whitelist remove {minecraft_name}')
        rcon.command(f'kick {minecraft_name} Du bist nicht mehr auf der Whitelist!')
        rcon.disconnect()
        print(f"|🖥|{datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S')}| - removed {minecraft_name} from the whitelist - server: " + server["friendly_name"] )


def is_mcname_permission_allowed(member):
    with open('user_data.json', 'r') as file:
        data = json.load(file)

    discord_name = str(member)
    if discord_name in data:
        return data[discord_name]["permission"]

    return False


async def set_mcname_permission(member, permission):
    with open('user_data.json', 'r+') as file:
        data = json.load(file)

        discord_name = str(member)
        if discord_name not in data:
            data[discord_name] = {"minecraft_name": "", "permission": False}

        data[discord_name]["permission"] = permission

        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()

bot.run(str(bot_token))
