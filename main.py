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
        parse_response = parse_pokebot_message(message)
        if parse_response == "alpha":
            await message.channel.send("New alpha found!")
        if parse_response == "stinker":
            await message.channel.send("New stinker found!")

        #total_ivs = parse_pokebot_message(message)
        #current_highest_iv = check_highest_iv()
        #new_highest_iv = compare_highest_iv(current_highest_iv, total_ivs)
        #if new_highest_iv:
        #    await message.channel.send('New highest IV pokemon recorded')

        #current_lowest_iv = check_lowest_iv()
        #new_lowest_iv = compare_lowest_iv(current_lowest_iv, total_ivs)
        #if new_lowest_iv:
        #    await message.channel.send('New lowest IV pokemon recorded :(')

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
            from_db_rebuild = True
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

def compare_highest_iv(current_highest_iv, total_ivs):
    current_highest_shiny_dict = current_highest_iv[0]
    formatted_current_highest_iv = current_highest_shiny_dict[1]
    if int(total_ivs) > int(formatted_current_highest_iv):
        print("NEW HIGHEST IV FOUND!")
        return True

def compare_lowest_iv(current_lowest_iv, total_ivs):
    current_lowest_shiny_dict = current_lowest_iv[0]
    formatted_current_lowest_iv = current_lowest_shiny_dict[1]
    if int(total_ivs) < int(formatted_current_lowest_iv):
        print("New lowest IV found :(")
        return True

#def compare_alpha_species(current_alpha, total_ivs, species):
#    print(f"current alpha = {current_alpha}")
#    current_alpha_species = current_alpha[0]
#    print(f"species being analyzed: {species}")
#    print(f"current alpha species: {current_alpha_species}")
#    current_alpha_ivs = current_alpha[1]
#    print(f"current alpha ivs for {species}: {current_alpha_ivs}\n")
#    print(f"int(total_ivs): {int(total_ivs)}")
#    print(f"int(current_alpha_ivs): {int(current_alpha_ivs)}\n")
#    if int(total_ivs) > (current_alpha_ivs):
#        print("New alpha found!")
#        return True


def compare_alpha_species(current_alpha, message_id):
    current_alpha_id = int(current_alpha[7])
    #print(f"current message id: {message_id}")
    #print(f"current alpha id: {current_alpha_id}")
    if message_id == current_alpha_id:
        print("New Alpha Found!")
        return True

def compare_stinker_species(current_stinker, message_id):
    current_stinker_id = int(current_stinker[7])
    if message_id == current_stinker_id:
        print("New Stinker Found!")
        return True

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
    # get the id of the last inserted row
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
    if message.content.startswith("Encountered a"):
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

        #print(f"species: {species}")
        #try:
        #    current_alpha = check_current_alpha(species)
        #    new_alpha_species = compare_alpha_species(current_alpha, total_ivs, species)
        #    if new_alpha_species:
        #        print(f"NEW ALPHA FOUND: {species} with {total_ivs} IVs")
        #except:
        #    print("Exception in checking database. Ignore this message if it's building the database")

        generate_pokebot_entry(shiny_value, total_ivs, held_item, species, target_phase_encounters, total_phase_encounters, phase_same_pokemon_streak, message_id)

        current_alpha = check_current_alpha(species)
        new_alpha = compare_alpha_species(current_alpha, message_id)
        #current_stinker = check_current_stinker(species)
        #new_stinker = compare_stinker_species(current_stinker, message_id)
        if new_alpha:
            print("alpha")
            return "alpha"
        current_stinker = check_current_stinker(species)
        new_stinker = compare_stinker_species(current_stinker, message_id)
        if new_stinker:
            print("stinker")
            return "stinker"


        #return total_ivs

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
