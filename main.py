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
        parse_response, new_species_found, species, total_ivs, new_hero, new_zero = parse_pokebot_message(message)
        if new_species_found:
            total_species = total_species_in_dex()
            if new_hero:
                await message.channel.send(f"New species discovered: {species}\nTotal species discovered: {total_species}/386\nNew hero found: {species} with {total_ivs} IVs")
                return
            if new_zero:
                await message.channel.send(f"New species discovered: {species}\nTotal species discovered: {total_species}/386\nNew zero found: {species} with {total_ivs} IVs")
                return
            else:
                await message.channel.send(f"New species discovered: {species}\nTotal species discovered: {total_species}/386")
                return
        if new_hero:
            await message.channel.send(f"New Hero found! {species} with {total_ivs} IVs!")
            return
        if new_zero:
            await message.channel.send(f"New Zero found... {species} with {total_ivs} IVs...")
            return
        if parse_response == "alpha":
            await message.channel.send(f"New alpha {species} found!")
        if parse_response == "stinker":
            await message.channel.send(f"New stinker {species} found!")

@tree.command(
    name="database_rebuild",
    description="Rebuild the Pokebot database",
    guild=discord.Object(id=guild_id),
)
async def database_rebuild(interaction):
    channel = client.get_channel(int(target_channel))
    await interaction.response.defer()
    async for message in channel.history(limit=10000):
        if message.author.id == (int(target_user_1)):
            parse_pokebot_message(message)

    await interaction.followup.send("Pokebot database has been successfully updated!")

@tree.command(
    name="highest_iv",
    description="Returns the entry with the highest total IVs",
    guild=discord.Object(id=guild_id),
)
async def highest_iv(interaction):
    channel = client.get_channel(int(target_channel))
    await interaction.response.defer()
    highest_iv_in_db = check_highest_iv()
    await interaction.followup.send(f"Here's the highest IV Pokemon: {highest_iv_in_db}")

@tree.command(
    name="lowest_iv",
    description="Returns the entry with the lowest total IVs",
    guild=discord.Object(id=guild_id),
)
async def lowest_iv(interaction):
    channel = client.get_channel(int(target_channel))
    await interaction.response.defer()
    lowest_iv_in_db = check_lowest_iv()
    await interaction.followup.send(f"Here's the lowest IV Pokemon: {lowest_iv_in_db}")

def total_species_in_dex():
    with sqlite3.connect("pokebot.db") as conn:
        cursor = conn.cursor()
        sqlite_select_query = """SELECT * FROM pokebot"""
        try:
            cursor.execute(sqlite_select_query)
            records = cursor.fetchall()
            encountered_species_list = []
            for record in records:
                species = record[0]
                if species not in encountered_species_list:
                    encountered_species_list.append(species)
            return len(encountered_species_list)
        except:
            pass

def check_highest_iv():
    with sqlite3.connect("pokebot.db") as conn:
        cursor = conn.cursor()
        sqlite_select_query = """SELECT * FROM pokebot ORDER BY total_ivs DESC"""
        try:
            cursor.execute(sqlite_select_query)
            size = 1
            records = cursor.fetchmany(size)
            return records
        except:
            pass

def check_lowest_iv():
    with sqlite3.connect("pokebot.db") as conn:
        cursor = conn.cursor()
        sqlite_select_query = """SELECT * FROM pokebot ORDER BY total_ivs ASC"""
        try:
            cursor.execute(sqlite_select_query)
            size = 1
            records = cursor.fetchmany(size)
            return records
        except:
            pass

def compare_highest_iv(current_highest_iv, message_id):
    try:
        current_highest_iv_dict = current_highest_iv[0]
        current_highest_id = int(current_highest_iv_dict[7])
        if message_id == current_highest_id:
            print("New Hero found!")
            return True
    except Exception as e:
        print(e)

def compare_lowest_iv(current_lowest_iv, message_id):
    try:
        current_lowest_iv_dict = current_lowest_iv[0]
        current_lowest_id = int(current_lowest_iv_dict[7])
        if message_id == current_lowest_id:
            print("New Zero found...")
            return True
    except Exception as e:
        print(e)

def compare_alpha_species(current_alpha, message_id):
    try:
        current_alpha_id = int(current_alpha[7])
        if message_id == current_alpha_id:
            print("New Alpha Found!")
            return True
    except Exception as e:
        print("Alpha for this species likely doesn't exist")

def compare_stinker_species(current_stinker, message_id):
    try:
        current_stinker_id = int(current_stinker[7])
        if message_id == current_stinker_id:
            print("New Stinker Found!")
            return True
    except Exception as e:
            print("Stinker for this species likely doesn't exist")

def check_current_alpha(species):
    with sqlite3.connect("pokebot.db") as conn:
        cursor = conn.cursor()
        sqlite_select_query = f"""SELECT * FROM pokebot WHERE species = '{species}' ORDER BY total_ivs DESC"""
        try:
            records = cursor.execute(sqlite_select_query)
            records = cursor.fetchone()
            print(f"here's the fetched record for {species} with the highest IVs: {records}")
            return records
        except Exception as e:
            print(e)

def check_current_stinker(species):
    with sqlite3.connect("pokebot.db") as conn:
        cursor = conn.cursor()
        sqlite_select_query = f"""SELECT * FROM pokebot WHERE species = '{species}' ORDER BY total_ivs ASC"""
        try:
            records = cursor.execute(sqlite_select_query)
            records = cursor.fetchone()
            print(f"here's the fetched record for {species} with the lowest IVs: {records}")
            return records
        except Exception as e:
            print(e)

def new_species_check(species):
    with sqlite3.connect("pokebot.db") as conn:
        cursor = conn.cursor()
        sqlite_select_query = f"""SELECT * FROM pokebot WHERE species = '{species}'"""
        try:
            records = cursor.execute(sqlite_select_query)
            records = cursor.fetchall()
            counter = 0
            for record in records:
                counter += 1
            if counter < 2:
                print(f"New species discovered! {species}")
                return True
            if counter >=2:
                return False
        except Exception as e:
            print(e)

def add_pokebot_entry(conn, entry):
    sql = '''INSERT INTO pokebot(species,
            total_ivs,
            shiny_value,
            held_item,
            phase_encounters,
            phase_same_pkmn_streak,
            receiving_user,
            message_id)
             VALUES(?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, entry)
    conn.commit()
    return cur.lastrowid

def generate_pokebot_entry(shiny_value, total_ivs, held_item, species, target_phase_encounters, total_phase_encounters, phase_same_pokemon_streak, message_id):
    try:
        with sqlite3.connect("pokebot.db") as conn:
            cursor.execute("""SELECT * FROM pokebot WHERE message_id=? """, (message_id,))
            result = cursor.fetchone()
            if result:
                print("Message ID already found in database. Skipping entry...")
                return
            pokebot_entries = [
                (species, total_ivs, shiny_value, held_item, target_phase_encounters, phase_same_pokemon_streak, 'user', message_id)
            ]
            pokebot_table_sql = """ CREATE TABLE pokebot(species VARCHAR(30),
                total_ivs INT,
                shiny_value INT,
                held_item VARCHAR(30),
                phase_encounters INT,
                phase_same_pkmn_streak INT,
                receiving_user VARCHAR(30),
                message_id VARCHAR(50))
                """
            try:
                cursor.execute(pokebot_table_sql)
            except sqlite3.Error as e:
                pass
            for entry in pokebot_entries:
                entry_id = add_pokebot_entry(conn, entry)
                print(f'Created entry with id {entry_id}\n')
    except sqlite3.Error as e:
        print("error opening database", e)

def parse_pokebot_message(*args):
    message = args[0]
    if message.content.startswith("Encountered a") or message.content.startswith("Received a"):
        print("\npokebot shiny or anti-shiny detected")
        cursor = sqliteConnection.cursor()
        embed_content_in_dict = message.embeds[0].to_dict()
        fields_list = embed_content_in_dict["fields"]

        ## Extract 'Shiny Value'
        extracted_shiny_value_dict = fields_list[0]
        shiny_value = extracted_shiny_value_dict["value"]
        print(f"Shiny Value: {shiny_value}")

        ## Extract Total IVs
        extracted_total_ivs_dict = fields_list[1]
        total_ivs = extracted_total_ivs_dict["name"]
        ## Trim excess data from Total IVs
        for character in 'IVs() ':
            total_ivs = total_ivs.replace(character, '')
        print(f"Total IVs: {total_ivs}")

        ## Extract Held Item
        extracted_held_item_dict = fields_list[2]
        held_item = extracted_held_item_dict["value"]
        print(f"Held Item: {held_item}")

        ## Extract Species
        extracted_species_dict = fields_list[3]
        species = extracted_species_dict["name"]
        ## Trim excess data from species
        species = species.replace(" Encounters", "")
        print(f"Species: {species}")

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
        ## Trim excess data from Phase Same Pokémon Streak
        phase_same_pokemon_streak = phase_same_pokemon_streak.replace(" were encountered in a row!", "")

        ## Receiving User

        ## Message ID
        message_id = message.id

        generate_pokebot_entry(shiny_value, total_ivs, held_item, species, target_phase_encounters, total_phase_encounters, phase_same_pokemon_streak, message_id)

        current_alpha = check_current_alpha(species)
        new_alpha = compare_alpha_species(current_alpha, message_id)
        current_highest_iv = check_highest_iv()
        print(f"current_highest_iv: {current_highest_iv}")
        new_hero = compare_highest_iv(current_highest_iv, message_id)
        current_lowest_iv = check_lowest_iv()
        print(f"current_lowest_iv: {current_lowest_iv}")
        new_zero = compare_lowest_iv(current_lowest_iv, message_id)

        new_species_found = new_species_check(species)
        if new_alpha:
            return "alpha", new_species_found, species, total_ivs, new_hero, new_zero
        current_stinker = check_current_stinker(species)
        new_stinker = compare_stinker_species(current_stinker, message_id)
        if new_stinker:
            return "stinker", new_species_found, species, total_ivs, new_hero, new_zero
    else:
        pass

def initial_create_db():
    try:
        with sqlite3.connect("pokebot.db") as conn:
            pokebot_table_sql = """ CREATE TABLE pokebot(
                species VARCHAR(30),
                total_ivs INT,
                shiny_value INT,
                held_item VARCHAR(30),
                phase_encounters INT,
                phase_same_pkmn_streak INT,
                receiving_user VARCHAR(30),
                message_id VARCHAR(50))
                """
            try:
                cursor.execute(pokebot_table_sql)
            except sqlite3.Error as e:
                pass
    except Exception as e:
        print(e)

def main():
    initial_create_db()
    client.run(token)

if __name__ == "__main__":
    main()
