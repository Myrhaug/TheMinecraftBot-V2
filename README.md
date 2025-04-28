# Discord Minecraft Whitelist Bot

## Description

This is a small Discord bot that allows you to easily manage your Minecraft server whitelist.
Adding someone to your whitelist is as simple as letting them run a slash command or by managing their roles.
The bot is easily configured through the config.json file and uses mcrcon for communication with Minecraft servers.

## Setup

1. Download the bot files or copy the Git.
2. Open the config.json file and enter:
    *   Your Discord bot token
    *   Your bot owner ID
    *   Server connection details
    *   The configured Discord roles for members and admins
3. Install the required dependencies:
    *   pip install -r requirements.txt
4. Start the bot.
5. Invite the bot to your Discord server.

You're done! It's that easy.

## How to Use

For Players:
Use the slash command /mc-setname and enter your Minecraft username.
The bot will automatically add you to the whitelist on all configured servers.
If your membership role is removed, the bot will automatically remove you from the whitelist and kick you if you are online.

For Admins:
Use the slash command /mc-reload to reload and sync all user whitelists if changes are made to config.json or if new servers are added.
Only users with the configured Admin role can use /mc-reload.

## Features
✅ Supports multiple Minecraft servers
✅ Easy configuration through config.json
✅ Automatic removal of players when role is removed
✅ /mc-setname command for self-registration
✅ /mc-reload command for admins to sync whitelists
✅ Robust error handling and logging
✅ Lightweight and easy to host
