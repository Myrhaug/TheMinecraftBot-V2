import datetime
import discord
from discord.ext import commands
from discord import  app_commands
from CodeUtils import embeds
import json
import mcrcon

bot_owner_id = None
servers = None
server_member_role_name = None
bot_name = None

def config_reload():
    global servers, server_member_role_name, bot_name, bot_owner_id
    with open('config.json', 'r') as config:
        config = json.load(config)
    bot_owner_id = int(config["bot_owner_id"])
    servers = config["servers"]
    server_member_role_name = config["server_member_role_name"]
    bot_name = config["bot_name"]

class mccommands(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    config_reload()

    @app_commands.command(name="mc-setname",description="this command connects your Minecraft account to your Discord account")
    async def mcsetname(self, interaction: discord.Interaction, mcname: str):
        config_reload()
        try:
            discord_name = str(interaction.user.name)
            if is_mcname_permission_allowed(discord_name):
                await interaction.response.send_message(embed=embeds.MCWhitelistaddEmbed())
                await check_json(discord_name)
                await save_to_json(discord_name, mcname)
                print(f"|🗄|{datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S')}| - saved DC: {discord_name} MC: {mcname} to json")
                await add_to_whitelist(discord_name, mcname)
                print(f"|🖥|{datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S')}| - added {mcname} to whitelist")
            else:
                await interaction.response.send_message(embed=embeds.MCNotAllowed())
        except Exception as e:
            await interaction.response.send_message(embed=embeds.MCError())
            print(f"|❌|{datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S')}| - {e}")

async def check_json(discord_name):
    config_reload()
    data = {}
    try:
        with open('user_data.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        pass

    minecraft_name = data[discord_name]["minecraft_name"]
    if minecraft_name != "":
        for server in servers:
            print(f"|🔍|{datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S')}| - Checked Json File and deleted the old {minecraft_name} from the whitelist - server:" + server["friendly_name"])
            rcon = mcrcon.MCRcon(host=str(server["server_ip"]), password=str(server["server_rcon_password"]), port=int(server["server_rcon_port"]))
            rcon.connect()
            rcon.command(f'whitelist remove {minecraft_name}')
            rcon.command(f'kick {minecraft_name} Du bist nicht mehr auf der Whitelist!')
            rcon.disconnect()
    else:
        print(f"|🔍|{datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S')}| - Checked Json File and no old user name was found")



async def save_to_json(discord_name, minecraft_name):
    data = {}
    try:
        with open('user_data.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        pass

    data[discord_name] = {"minecraft_name": minecraft_name, "permission": True}

    with open('user_data.json', 'w') as file:
        json.dump(data, file, indent=4)


async def add_to_whitelist(discord_name, minecraft_name):
    config_reload()
    for server in servers:
        rcon = mcrcon.MCRcon(host=str(server["server_ip"]), password=str(server["server_rcon_password"]), port=int(server["server_rcon_port"]))
        rcon.connect()
        rcon.command(f'whitelist add {minecraft_name}')
        rcon.disconnect()

def is_mcname_permission_allowed(member):
    with open('user_data.json', 'r') as file:
        data = json.load(file)

    discord_name = str(member)
    if discord_name in data:
        return data[discord_name]["permission"]

    return False