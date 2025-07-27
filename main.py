import discord
from discord import app_commands
import sqlite3
import json
from discord.ext import commands

with open('config.json', 'r') as g:
    config = json.load(g)

token = config['token']
guild_id = config['guild_id']
target_user_1 = config['target_user_1']
target_channel = config['target_channel']
sqliteConnection = sqlite3.connect('pokebot.db')
cursor = sqliteConnection.cursor()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    tree.copy_global_to(guild=discord.Object(id=(int(guild_id))))
    await tree.sync(guild=discord.Object(id=(int(guild_id))))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.author.id == (int(target_user_1)):
        print('Pokebot message detected')
        cursor = sqliteConnection.cursor()
        generate_pokebot_entry()
        print(message.content)

        embed_content_in_dict = message.embeds[0].to_dict()
        fields_list = embed_content_in_dict["fields"]
        print(fields_list)
        extracted_shiny_value_dict = fields_list[0]
        print(extracted_shiny_value_dict)
        extracted_shiny_value = extracted_shiny_value_dict["value"]
        print(f"Shiny Value: {extracted_shiny_value}")

@tree.command(
    name="database_rebuild",
    description="Rebuild the Pokebot database",
    guild=discord.Object(id=guild_id),
)
async def database_rebuild(interaction):
    channel = client.get_channel(int(target_channel))
    counter = 0
    async for message in channel.history(limit=1000):
        if message.author.id == (int(target_user_1)):
            counter += 1

    await interaction.response.send_message(f"Here's a number of something: {counter}")

def add_pokebot_entry(conn, entry):
    sql = '''INSERT INTO pokebot_test(species,
            total_ivs,
            hp,
            attack,
            defense,
            special_attack,
            special_defense,
            speed,
            nature,
            shiny_value,
            held_item,
            phase_encounters,
            phase_same_pkmn_streak,
            receiving_user)
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
            for entry in pokebot_entries:
                entry_id = add_pokebot_entry(conn, entry)
                print(f'Created entry with id {entry_id}')
    except sqlite3.Error as e:
        print("error opening database", e)

def main():

    client.run(token)

if __name__ == "__main__":
    main()
