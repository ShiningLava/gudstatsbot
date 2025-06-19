import discord
import logging
import logging.handlers
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents)
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
token = 'Enter Token Here'
discord_id = 0 # Enter Discord ID here

@tree.command(
    name="marco",
    description="marco",
    guild=discord.Object(id=discord_id)
)
async def marco(interaction):
    await interaction.response.send_message("polo")

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=discord_id))
    print("Ready!")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Shh')

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Assume client refers to a discord.Client subclass...
# Suppress the default configuration since we have our own
client.run(token, log_handler=None)
