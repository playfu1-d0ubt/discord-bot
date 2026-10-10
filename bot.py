import os
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()  # reads DISCORD_TOKEN from your .env file
TOKEN = os.getenv("DISCORD_TOKEN")

# intents say which events the bot wants to hear about
# message_content lets it read the text of messages, so it can see "!ping"
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
async def ping(ctx):
    """Reply with pong."""
    await ctx.send("pong")


def main():
    if not TOKEN:
        sys.exit("Error: DISCORD_TOKEN not found. Add it to your .env file.")
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        sys.exit("Error: Discord rejected the token. Check DISCORD_TOKEN in .env (you may need to reset it).")
    except discord.PrivilegedIntentsRequired:
        sys.exit("Error: turn on 'Message Content Intent' on the Bot tab in the Discord Developer Portal.")


if __name__ == "__main__":
    main()