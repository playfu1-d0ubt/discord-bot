import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv
from rules import RULES, RULES_INTRO, RULES_TITLE


load_dotenv()  # reads DISCORD_TOKEN from your .env file
TOKEN = os.getenv("DISCORD_TOKEN")

BOT_DESCRIPTION = "A small bot built with Python and discord.py."
EMBED_COLOUR = discord.Colour.red()
BANNER_PATH = Path(__file__).parent / "assets" / "rules_banner.webp"

# intents say which events the bot wants to hear about
# message_content lets it read the text of messages, so it can see "!ping"
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
start_time = datetime.now(timezone.utc)  # remembered so we can work out the uptime

def latency_ms():
    """The bot's delay to Discord as text, like '42 ms'."""
    latency = bot.latency
    if math.isnan(latency):  # happens if we ask before the bot has fully connected
        return "unknown"
    return f"{round(latency * 1000)} ms"


def format_uptime():
    """Turn the time since the bot started into text like '2h 5m 10s'."""
    seconds = int((datetime.now(timezone.utc) - start_time).total_seconds())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if days or hours:
        parts.append(f"{hours}h")
    if days or hours or minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    """Reply with a friendly message instead of failing silently."""
    if isinstance(error, commands.CommandNotFound):
        return  # ignore unknown commands quietly
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send("That command only works inside a server.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("I couldn't find that member.")
    else:
        print(f"Error in !{ctx.command}: {error}")
        await ctx.send("Something went wrong with that command.")


@bot.command()
async def ping(ctx):
    """Check the bot is alive and see how fast it responds."""
    await ctx.send(f"pong ({latency_ms()})")

@bot.command()
@commands.guild_only()
async def info(ctx):
    """Show details about the bot and this server."""
    guild = ctx.guild
    embed = discord.Embed(title=f"About {bot.user.name}", description=BOT_DESCRIPTION, colour=EMBED_COLOUR)

    embed.add_field(
        name="Bot",
        value=(
            f"Latency: {latency_ms()}\n"
            f"Uptime: {format_uptime()}\n"
            f"Servers: {len(bot.guilds)}\n"
            f"discord.py: {discord.__version__}"
        ),
        inline=False,
    )
    embed.add_field(
        name=f"Server: {guild.name}",
        value=(
            f"Owner: <@{guild.owner_id}>\n"
            f"Members: {guild.member_count}\n"
            f"Channels: {len(guild.text_channels)} text, {len(guild.voice_channels)} voice\n"
            f"Created: {discord.utils.format_dt(guild.created_at, 'D')}"
        ),
        inline=False,
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    await ctx.send(embed=embed)

@bot.command()
@commands.guild_only()
async def userinfo(ctx, member: discord.Member = None):
    """Show details about a member (yourself if you don't name anyone)."""
    member = member or ctx.author
    embed = discord.Embed(title=member.display_name, colour=EMBED_COLOUR)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Username", value=member.name, inline=True)
    embed.add_field(name="Top role", value=member.top_role.name, inline=True)
    joined = discord.utils.format_dt(member.joined_at, "D") if member.joined_at else "Unknown"
    embed.add_field(name="Joined the server", value=joined, inline=False)
    embed.add_field(name="Account created", value=discord.utils.format_dt(member.created_at, "D"), inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def avatar(ctx, member: discord.Member = None):
    """Show a member's avatar (yours if you don't name anyone)."""
    member = member or ctx.author
    embed = discord.Embed(title=f"{member.display_name}'s avatar", colour=EMBED_COLOUR)
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def rules(ctx):
    """Show all the server rules."""
    embed = discord.Embed(title=RULES_TITLE, description=RULES_INTRO, colour=EMBED_COLOUR)
    for number, text in enumerate(RULES, start=1):
        embed.add_field(name=f"Law {number}", value=text, inline=False)
    if BANNER_PATH.exists():
        # attach the picture, then point the embed at the attachment
        banner = discord.File(BANNER_PATH, filename=BANNER_PATH.name)
        embed.set_image(url=f"attachment://{BANNER_PATH.name}")
        await ctx.send(embed=embed, file=banner)
    else:
        await ctx.send(embed=embed)


@bot.command()
async def rule(ctx, number: int):
    """Show one rule by its number, like: !rule 2"""
    if not 1 <= number <= len(RULES):
        await ctx.send(f"There's no law {number}. Pick a number from 1 to {len(RULES)}.")
        return
    embed = discord.Embed(title=f"Law {number}", description=RULES[number - 1], colour=EMBED_COLOUR)
    await ctx.send(embed=embed)

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