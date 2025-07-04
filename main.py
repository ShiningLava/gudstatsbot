import discord
from discord import app_commands
import sqlite3
import json
from discord.ext import commands

with open('config.json', 'r') as g:
    config = json.load(g)

token = config['token']
#guild_id = config['guild_id']
guild_id = 120731559874527232
target_user_1 = config['target_user_1']
sqliteConnection = sqlite3.connect('pokebot.db')
cursor = sqliteConnection.cursor()

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

#@tree.command(
#    name="echo",
#    description="Echoes a message.",
#    guild=discord.Object(id=guild_id)
#)
#async def echo(interaction):
#    await interaction.response.send_message("echo")

#class MyClient(discord.Client):
#    def __init__(self, *, intents: discord.Intents):
#        super().__init__(intents=intents)
#        self.tree = app_commands.CommandTree(self)

#    async def setup_hook(self):
#        # This copies the global commands over to your guild.
#        print("--0-0-0-0-0-0-0-0000-0---0-0-00-0--0-0--00---0-00-00-0-0-0-0-")
#        self.tree.copy_global_to(guild=discord.Object(id=120731559874527232))
#        await self.tree.sync(guild=discord.Object(id=120731559874527232))
#        print("Global slash commands updated for GudStatsBot")


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    tree.copy_global_to(guild=discord.Object(id=120731559874527232))
    await tree.sync(guild=discord.Object(id=120731559874527232))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.author.id == (int(target_user_1)):
        print('Pokebot message detected')
        cursor = sqliteConnection.cursor()
        generate_pokebot_entry()

@tree.command(
    name="echo",
    description="Echoes a message.",
    guild=discord.Object(id=guild_id)
)
async def echo(interaction):
    await interaction.response.send_message("echo")

def add_pokebot_entry(conn, entry):
    sql = '''INSERT INTO pokebot_test(species,total_ivs,hp,attack,defense,special_attack,special_defense,speed,nature,shiny_value,held_item,phase_encounters,phase_same_pkmn_streak,receiving_user)
             VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, entry)
    conn.commit()
    # get the id of the last inserted row
    return cur.lastrowid

def generate_pokebot_entry():
    try:
        with sqlite3.connect("pokebot.db") as conn:
            pokebot_entries = [
                ('species', 1, 1, 1, 1, 1, 1, 1, 'nature', 1, 'item', 1, 1, 'user')
            ]
            pokebot_test_table_sql = """ CREATE TABLE pokebot_test(species VARCHAR(30),
                total_ivs INT,
                hp INT,
                attack INT,
                defense INT,
                special_attack INT,
                special_defense INT,
                speed INT,
                nature VARCHAR(30),
                shiny_value INT,
                held_item VARCHAR(30),
                phase_encounters INT,
                phase_same_pkmn_streak INT,
                receiving_user VARCHAR(30))
                """
            try:
                cursor.execute(pokebot_test_table_sql)
            except sqlite3.Error as e:
                pass
                #print("", e)
            for entry in pokebot_entries:
                entry_id = add_pokebot_entry(conn, entry)
                print(f'Created entry with id {entry_id}')
    except sqlite3.Error as e:
        print("error opening database", e)

def main():

#    @client.event
#    async def on_ready():
#        print(f'Logged in as {client.user} (ID: {client.user.id})')

#    @client.event
#    async def on_message(message):
#        if message.author == client.user:
#            return
#        if message.author.id == (int(target_user_1)):
#            print('Pokebot message detected')
#            cursor = sqliteConnection.cursor()
#            generate_pokebot_entry()

#    @tree.command(
#        name="echo",
#        description="Echoes a message.",
#        guild=discord.Object(id=guild_id)
#    )
#    async def echo(interaction):
#        await interaction.response.send_message("echo")

    client.run(token)

if __name__ == "__main__":
    main()
