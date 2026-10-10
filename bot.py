import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv
from rules import RULES, RULES_INTRO, RULES_TITLE

class EmbedHelp(commands.HelpCommand):
    """A !help command that replies with an embed instead of plain text."""

    async def send_bot_help(self, mapping):
        """!help on its own: every command, grouped by category."""
        bot = self.context.bot
        prefix = self.context.clean_prefix
        available = {command.name: command for command in bot.commands if not command.hidden}

        embed = discord.Embed(
            title=f"{bot.user.name} commands",
            description=f"Use `{prefix}help <command>` for more detail on one command.",
            colour=EMBED_COLOUR,
        )
        listed = set()
        for category, names in HELP_CATEGORIES.items():
            lines = []
            for name in names:
                command = available.get(name)
                if command:
                    lines.append(self.describe(command, prefix))
                    listed.add(name)
            if lines:
                embed.add_field(name=category, value="\n".join(lines), inline=False)

        # any command not in HELP_CATEGORIES goes here, so new commands never go missing
        others = [self.describe(command, prefix) for name, command in sorted(available.items()) if name not in listed]
        if others:
            embed.add_field(name="Other", value="\n".join(others), inline=False)

        embed.set_thumbnail(url=bot.user.display_avatar.url)
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        """!help <command>: the full description of one command."""
        prefix = self.context.clean_prefix
        usage = f"{prefix}{command.qualified_name} {command.signature}".strip()
        embed = discord.Embed(title=usage, description=command.help or "No description yet.", colour=EMBED_COLOUR)
        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error):
        """!help <something that isn't a command>."""
        await self.get_destination().send(error)

    @staticmethod
    def describe(command, prefix):
        """One line for the list: `!rule <number>` - Show one rule by its number..."""
        usage = f"{prefix}{command.name} {command.signature}".strip()
        return f"`{usage}` - {command.short_doc or 'No description yet.'}"

load_dotenv()  # reads DISCORD_TOKEN from your .env file
TOKEN = os.getenv("DISCORD_TOKEN")

BOT_DESCRIPTION = "A small bot built with Python and discord.py."
EMBED_COLOUR = discord.Colour.red()
BANNER_PATH = Path(__file__).parent / "assets" / "rules_banner.webp"

# intents say which events the bot wants to hear about
# message_content lets it read the text of messages, so it can see "!ping"
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=EmbedHelp(command_attrs={"help": "Show this list, or details about one command."}),
)
start_time = datetime.now(timezone.utc)  # remembered so we can work out the uptime

# which commands appear under which heading in !help
# a command that isn't listed here still shows up, under "Other"
HELP_CATEGORIES = {
    "General": ["ping", "info", "help"],
    "Members": ["userinfo", "avatar"],
    "Rules": ["rules", "rule"],
}


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
    elif isinstance(error, (commands.BadArgument, commands.MissingRequiredArgument)):
        await ctx.send(f"I couldn't understand that. Try `!help {ctx.command}` to see how to use it.")
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