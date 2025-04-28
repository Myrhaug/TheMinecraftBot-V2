import datetime
import discord
from discord.ext import commands
from discord import app_commands
from CodeUtils import embeds
import json
import mcrcon

bot_owner_id = None
servers = None
server_member_role_name = None
server_admin_role_name = None
bot_name = None

def config_reload():
    global servers, server_member_role_name, bot_name, bot_owner_id, server_admin_role_name
    with open("config.json", 'r') as config:
        config = json.load(config)
    bot_owner_id = int(config["bot_owner_id"])
    servers = config["servers"]
    server_member_role_name = config["server_member_role_name"]
    server_admin_role_name = config.get("server_admin_role_name", "Admin")
    bot_name = config["bot_name"]

class mccommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mc-setname", description="This command connects your Minecraft account to your Discord account")
    async def setmcname(self, interaction: discord.Interaction, mcname: str):
        config_reload()
        try:
            discord_name = str(interaction.user.name)
            if is_mcname_permission_allowed(discord_name):
                await interaction.response.send_message(embed=embeds.MCWhitelistaddEmbed())
                await check_json(discord_name)
                await save_to_json(discord_name, mcname)
                print(f"[+] {datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S')} - saved DC: {discord_name} MC: {mcname} to json")
                await add_to_whitelist(mcname)
                print(f"[+] {datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S')} - added {mcname} to whitelist")
            else:
                await interaction.response.send_message(embed=embeds.MCNotAllowed(), ephemeral=True)
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embeds.MCError(), ephemeral=True)
            else:
                await interaction.followup.send(embed=embeds.MCError(), ephemeral=True)
            print(f"[-] {datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S')} - {e}")

    @app_commands.command(name="mc-reload", description="Reloads the Minecraft servers configuration.")
    async def mc_reload(self, interaction: discord.Interaction):
        config_reload()

        if not any(role.name == server_admin_role_name for role in interaction.user.roles):
            await interaction.response.send_message(embed=embeds.MCNotAllowed(), ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        for discord_id, user_info in load_user_data().items():
            minecraft_name = user_info.get("minecraft_name")
            if not minecraft_name:
                print(f"Skipping {discord_id}: No Minecraft name set.")
                continue

            for server in servers:
                if not is_user_registered_on_server(discord_id, server["friendly_name"]):
                    print(f"Adding {minecraft_name} to {server['friendly_name']} whitelist...")
                    await add_to_whitelist(minecraft_name)

        await interaction.followup.send(content="Reload complete!")

# Helper functions
def load_user_data():
    try:
        with open('user_data.json', 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                print("[WARNING] user_data.json was not a dictionary. Resetting...")
                return {}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        print("[WARNING] user_data.json not found or invalid. Returning empty data.")
        return {}

def is_user_registered_on_server(discord_id, server_name):
    data = load_user_data()
    user_info = data.get(discord_id, {})
    servers_registered = user_info.get("servers", {})
    return server_name in servers_registered

async def add_to_whitelist(minecraft_name):
    for server in servers:
        try:
            rcon = mcrcon.MCRcon(
                host=str(server["server_ip"]),
                password=str(server["server_rcon_password"]),
                port=int(server["server_rcon_port"])
            )
            rcon.connect()
            rcon.command(f'whitelist add {minecraft_name}')
            rcon.disconnect()
            print(f"[+] {minecraft_name} added to {server['friendly_name']}")
        except (ConnectionRefusedError, OSError) as e:
            print(f"[WARNING] RCON connection refused for {server['friendly_name']}: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error with server {server['friendly_name']}: {e}")

def is_mcname_permission_allowed(discord_name):
    try:
        with open('user_data.json', 'r') as file:
            data = json.load(file)
            if not isinstance(data, dict):
                return False
    except (FileNotFoundError, json.JSONDecodeError):
        return False

    if discord_name in data:
        return data[discord_name].get("permission", False)

    return False

async def check_json(discord_name):
    config_reload()
    try:
        with open('user_data.json', 'r') as file:
            data = json.load(file)
            if not isinstance(data, dict):
                data = {}
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    minecraft_name = data.get(discord_name, {}).get("minecraft_name", "")

    if minecraft_name:
        for server in servers:
            try:
                print(f"[INFO] Checking if old Minecraft name '{minecraft_name}' needs removal on {server['friendly_name']}...")
                rcon = mcrcon.MCRcon(
                    host=str(server["server_ip"]),
                    password=str(server["server_rcon_password"]),
                    port=int(server["server_rcon_port"])
                )
                rcon.connect()
                rcon.command(f'whitelist remove {minecraft_name}')
                rcon.command(f'kick {minecraft_name} You are no longer on the whitelist!')
                rcon.disconnect()
                print(f"[SUCCESS] Removed old Minecraft name '{minecraft_name}' from whitelist at server: {server['friendly_name']}")
            except Exception as e:
                print(f"[WARNING] Could not remove old user from server {server['friendly_name']}: {e}")
    else:
        print(f"[INFO] No old Minecraft name found for Discord user '{discord_name}'. Skipping removal.")

async def save_to_json(discord_name, mcname):
    data = {}
    try:
        with open('user_data.json', 'r') as file:
            data = json.load(file)
            if not isinstance(data, dict):
                print("[WARNING] user_data.json was not a dictionary. Resetting...")
                data = {}
    except (FileNotFoundError, json.JSONDecodeError):
        print("[WARNING] user_data.json not found or invalid. Creating new...")
        data = {}

    data[discord_name] = {"minecraft_name": mcname, "permission": True}

    with open('user_data.json', 'w') as file:
        json.dump(data, file, indent=4)
