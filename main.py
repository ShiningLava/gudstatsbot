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
        parse_pokebot_message(message)

@tree.command(
    name="database_rebuild",
    description="Rebuild the Pokebot database",
    guild=discord.Object(id=guild_id),
)
async def database_rebuild(interaction):
    channel = client.get_channel(int(target_channel))
    await interaction.response.defer()
    counter = 0
    async for message in channel.history(limit=10000):
        if message.author.id == (int(target_user_1)):
            counter += 1
            parse_pokebot_message(message)

    print(counter)

    #await interaction.response.send_message(f"Here's a number of something: {counter}")
    await interaction.followup.send(f"Here's a number of something: {counter}")

def add_pokebot_entry(conn, entry):
    sql = '''INSERT INTO pokebot_test(species,
            total_ivs,
            shiny_value,
            held_item,
            phase_encounters,
            phase_same_pkmn_streak,
            receiving_user)
             VALUES(?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, entry)
    conn.commit()
    # get the id of the last inserted row
    return cur.lastrowid

def generate_pokebot_entry(shiny_value, total_ivs, held_item, species, target_phase_encounters, total_phase_encounters, phase_same_pokemon_streak):
    try:
        with sqlite3.connect("pokebot.db") as conn:
            pokebot_entries = [
                (species, total_ivs, shiny_value, held_item, target_phase_encounters, phase_same_pokemon_streak, 'user')
            ]
            pokebot_test_table_sql = """ CREATE TABLE pokebot_test(species VARCHAR(30),
                total_ivs INT,
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
                print(f'Created entry with id {entry_id}\n')
    except sqlite3.Error as e:
        print("error opening database", e)

def parse_pokebot_message(message):
    print("parsing pokebot message")
    
    if message.content.startswith("Encountered a"):
        print("pokebot shiny or anti-shiny detected")
        cursor = sqliteConnection.cursor()
        #print(message.content)

        ## Disabled for testing, this should be reenabled to parse Pokebot embedded data
        embed_content_in_dict = message.embeds[0].to_dict()
        #embed_content_in_dict = {'footer': {'text': 'ID: chance is smelly but is also 500k encounters ahead of me | Pokémon Emerald (E)\nPokéBot Gen3 20250714.0'}, 'image': {'w>
        fields_list = embed_content_in_dict["fields"]

        ## Extract 'Shiny Value'
        extracted_shiny_value_dict = fields_list[0]
        shiny_value = extracted_shiny_value_dict["value"]
        print(f"Shiny Value: {shiny_value}")

        ## Extract Total IVs
        extracted_total_ivs_dict = fields_list[1]
        total_ivs = extracted_total_ivs_dict["name"]
        print(f"Total IVs: {total_ivs}")


        ## Trim excess data from Total IVs
        for character in 'IVs() ':
            total_ivs = total_ivs.replace(character, '')
        print(f"Total IVs trimmed: {total_ivs}")


        ## Extract Held Item
        extracted_held_item_dict = fields_list[2]
        held_item = extracted_held_item_dict["value"]
        print(f"Held Item: {held_item}")


        ## Extract Species
        extracted_species_dict = fields_list[3]
        species = extracted_species_dict["name"]
        print(f"Species: {species}")


        ## Trim excess data from species
        species = species.replace(" Encounters", "")
        print(f"Species trimmed: {species}")


        ## Extract Target Phase Encounters
        extracted_target_phase_encounters_dict = fields_list[4]
        target_phase_encounters = extracted_target_phase_encounters_dict["value"]
        print(f"Target Phase Encounters: {target_phase_encounters}")


        ## Extract Total Phase Encounters
        extracted_total_phase_encounters_dict = fields_list[5]
        total_phase_encounters = extracted_total_phase_encounters_dict["value"]
        print(f"Total Phase Encounters: {total_phase_encounters}")


        ## Extract Phase Same Pokémon Streak
        extracted_phase_same_pokemon_streak_dict = fields_list[8]
        phase_same_pokemon_streak = extracted_phase_same_pokemon_streak_dict["value"]
        print(f"Phase Same Pokémon Streak: {phase_same_pokemon_streak}")


        ## Trim excess data from Phase Same Pokémon Streak
        phase_same_pokemon_streak = phase_same_pokemon_streak.replace(" were encountered in a row!", "")
        print(f"Phase Same Pokémon Streak trimmed: {phase_same_pokemon_streak}\n")


        ## Receiving User

        generate_pokebot_entry(shiny_value, total_ivs, held_item, species, target_phase_encounters, total_phase_encounters, phase_same_pokemon_streak)
    else:
        pass

def main():
    client.run(token)

if __name__ == "__main__":
    main()
