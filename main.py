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

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=discord.Object(id=guild_id))
        await self.tree.sync(guild=discord.Object(id=guild_id))
        print("Global slash commands updated for GudStatsBot")

def add_pokebot_entry(conn, entry):
    sql = '''INSERT INTO pokebot_test(species,total_ivs,hp,attack,defense,special_attack,special_defense,speed,nature,shiny_value,held_item,phase_encounters,phase_same_pkmn_streak,receiving_user)
             VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''

    cur = conn.cursor()
    cur.execute(sql, entry)
    conn.commit()

    # get the id of the last inserted row
    #return cur.lastrowid

def main():
    print("main")
    try:
        with sqlite3.connect("pokebot.db") as conn:
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

    if message.author.id == (int(target_user_1)):
        print('Pokebot message detected')
        cursor = sqliteConnection.cursor()
        main()

client.run(token)

#if __name__ == "__main__":
#    main()
