from typing import Optional

import discord
from discord import app_commands
import sqlite3

MY_GUILD = discord.Object(id=0)  # replace with your guild id
token = '' # replace with your token

sqliteConnection = sqlite3.connect('pokebot.db')
cursor = sqliteConnection.cursor()

print('Check if pokemon table exists in the database:')
listOfTables = cursor.execute(
"""SELECT name FROM sqlite_master WHERE type='table'
AND name='pokemon'; """).fetchall()

if listOfTables == []:
    print('Pokemon table not found!')
    sqliteConnection = sqlite3.connect('pokebot.db')
    cursor = sqliteConnection.cursor()
    sql_command = """CREATE TABLE pokemon (
    species varchar(30),
    total_ivs int,
    hp int,
    attack int,
    defense int,
    special_attack int,
    special_defense int,
    speed int,
    nature varchar(20),
    shiny_value int,
    held_item varchar(50),
    phase_encounters int,
    phase_same_pkmn_Streak int,
    receiving_user varchar(100)
    );"""
    cursor.execute(sql_command)
    #conn.commit()

else:
    print('Pokemon table found, continuing...')

sql_test_table = """CREATE TABLE IF NOT EXISTS testing2(species varchar(30));"""

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    #if message.author.id == (1261431264796213269):
    if message.author.id == (223895172675534848):
        print('Pokebot message detected')
        cursor = sqliteConnection.cursor()
        listoftesttables = cursor.execute(
        """SELECT name FROM sqlite_master WHERE type='table'
        AND name='test'; """).fetchall()
        with sqlite3.connect('pokebot.db') as conn:
            cursor = conn.cursor()
            print("Connected to the database")
            cursor.execute('CREATE TABLE IF NOT EXISTS testing_columns (species VARCHAR(30), coolness smallint);')
            #print('CREATE TABLE IF NOT EXISTS test (species varchar(30));')
            #try:
                #cursor.execute('ALTER TABLE test ADD COLUMN "species";')
                #cursor.execute('INSERT INTO test VALUES (sableye);')
            #except Exception as e:
                #print (e)
            #cursor.execute('INSERT INTO test(species) VALUES(Sableye);')
            species = "sableye"
            cursor.execute("INSERT INTO testing_columns (species, coolness) VALUES (?, ?)", ("Sableye", 10))
            cursor.execute(sql_test_table)
            conn.commit()


client.run(token)
