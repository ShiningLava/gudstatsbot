#from typing import Optional
import discord
from discord import app_commands
import sqlite3
import json

with open('config.json', 'r') as g:
    config = json.load(g)

token = config['token']
guild_id = config['guild_id']
target_user_1 = config['target_user_1']
intents = discord.Intents.default()
sqliteConnection = sqlite3.connect('pokebot.db')
cursor = sqliteConnection.cursor()

#print('Check if pokemon table exists in the database:')
#listOfTables = cursor.execute(
#"SELECT name FROM sqlite_master WHERE type='table'
#AND name='pokemon'; ").fetchall()

#if listOfTables == []:
#    print('Pokemon table not found!')
#    sqliteConnection = sqlite3.connect('pokebot.db')
#    cursor = sqliteConnection.cursor()
#    sql_command = ""CREATE TABLE pokemon (
#    species varchar(30),
#    total_ivs int,
#    hp int,
#    attack int,
#    defense int,
#    special_attack int,
#    special_defense int,
#    speed int,
#    nature varchar(20),
#    shiny_value int,
#    held_item varchar(50),
#    phase_encounters int,
#    phase_same_pkmn_Streak int,
#    receiving_user varchar(100)
#    );""
#    cursor.execute(sql_command)

#else:
#    print('Pokemon table found, continuing...')

#sql_test_table = "CREATE TABLE IF NOT EXISTS testing2(species varchar(30));"

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
        self.tree.copy_global_to(guild=discord.Object(id=guild_id))
        await self.tree.sync(guild=discord.Object(id=guild_id))
        print("Global slash commands updated for GudStatsBot")


def add_pokebot_entry(conn, entry):
    # insert table statement
    sql = '''INSERT INTO pokebot_test(species,total_ivs,hp,attack,defense,special_attack,special_defense,speed,nature,shiny_value,held_item,phase_encounters,phase_same_pkmn_streak,receiving_user)
             VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
    
    # create a cursor
    cur = conn.cursor()

    # execute the INSERT statement
    cur.execute(sql, entry)

    # commit the changes
    conn.commit()

    # get the id of the last inserted row
    #return cur.lastrowid

def main():
    print("main")
    try:
        with sqlite3.connect("pokebot.db") as conn:
            ## define pokebot_entries
            pokebot_entries = [
                ('species', 1, 1, 1, 1, 1, 1, 1, 'nature', 1, 'item', 1, 1, 'user')
            ]
            try:
                
                cursor.execute("CREATE TABLE pokebot_test(species VARCHAR(30), total_ivs INT, hp INT, attack INT, defense INT, special_attack INT, special_defense INT, speed INT, nature VARCHAR(30), shiny_value INT, held_item VARCHAR(30), phase_encounters INT, phase_same_pkmn_streak INT, receiving_user VARCHAR(30))")
                print("pokebot_test table not detected. Creating...")
            except sqlite3.Error as error:
                print("failed to execute the above query, ", error)

            for entry in pokebot_entries:
                entry_id = add_pokebot_entry(conn, entry)
                print(f'Created entry with id {entry_id}')
    except sqlite3.Error as e:
        print(e)

client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    #if message.author.id == (1261431264796213269):
    if message.author.id == (int(target_user_1)):
        print('Pokebot message detected')
        cursor = sqliteConnection.cursor()
#        with sqlite3.connect('pokebot.db') as conn:
#            cursor = conn.cursor()
#            print("Connected to the database")

#            res = cursor.execute("SELECT * FROM sqlite_master")
#            print(res.fetchone())

#            print("checking if testing_columns table exists in databse")
#            try:
#                cursor.execute("CREATE TABLE testing_columns(species, coolness)")
#                print("testing_columns table not detected. Creating...")
#            except sqlite3.Error as error:
#                print("failed to execute the above query, ", error)

#            print("adding entry to database")
#            cursor.execute("" 
#                INSERT INTO testing_columns VALUES
#                    ('Sableye', 10)
#            "")

#            conn.commit()
#            print('Database updated')


            ## TESTING DELETE LATER
#            res = cursor.execute("SELECT * FROM sqlite_master")
#            print(res.fetchone())
        main()

client.run(token)

#def main():
#    print("main")
#    try:
#        with sqlite3.connect("pokebot.db") as conn:
#            ## define pokebot_entries
#            pokebot_entries = [
#                ('species', 1, 1, 1, 1, 1, 1, 1, 'nature', 1, 'item', 1, 1, 'user')
#            ]

#            for entry in pokebot_entries:
#                entry_id = add_pokebot_entry(conn, entry)
#                print(f'Created entry with id {entry_id}')
#    except sqlite3.Error as e:
#        print(e)

#if __name__ == "__main__":
#    main()
