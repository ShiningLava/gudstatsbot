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
        pb_message_dict = parse_pokebot_message(message)
        if pb_message_dict:
            generate_pokebot_entry(pb_message_dict)
            new_alpha, new_hero, new_stinker, new_zero = alpha_stinker_zero_hero_check(pb_message_dict)
            species = pb_message_dict['species']
            total_ivs = pb_message_dict['total_ivs']
            new_species_found = new_species_check(pb_message_dict['species'])
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
            if new_alpha:
                await message.channel.send(f"New alpha {species} found!")
            if new_stinker:
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
            pb_message_dict = parse_pokebot_message(message)
            if pb_message_dict:
                generate_pokebot_entry(pb_message_dict)
                alpha_stinker_zero_hero_check(pb_message_dict)

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


@tree.command()
async def custom_db_search(inter: discord.Interaction, 
			  species: str | None,
			  total_ivs: str | None,
			  shiny_value: str | None,
			  held_item: str | None, held_item_operator: str | None,
			  phase_encounters: int | None,
			  phase_same_pkmn_streak: str | None,
			  receiving_user: str | None,
			  message_id: str | None,
			  order_by: str = 'total_ivs',
                          species_operator: str = '=',
                          total_ivs_operator: str = '=',
			  shiny_value_operator: str = '=',
			  phase_encounters_operator: str = '=',
			  phase_same_pkmn_streak_operator: str = '=',
			  receiving_user_operator: str = '=',
			  message_id_operator: str = '=',
                          order_by_operator: str = 'DESC',):
    """
    Custom database search

    Parameters
    ----------
    inter: discord.Interaction
        The interaction object
    column: str
        The column to echo
    """

    arguments_dict = {"species": species,
		     "total_ivs": total_ivs,
		     "held_item": held_item,
		     "shiny_value": shiny_value,
		     "phase_encounters": phase_encounters,
		     "phase_same_pkmn_streak": phase_same_pkmn_streak,
		     "receiving_user": receiving_user}

    arguments_operators_dict = {"species_operator": species_operator,
				"total_ivs_operator": total_ivs_operator,
				"held_item_operator": held_item_operator,
				"shiny_value_operator": shiny_value_operator,
				"phase_encounters_operator": phase_encounters_operator,
				"phase_same_pkmn_streat_operator": phase_same_pkmn_streak_operator,
				"receiving_user_operator": receiving_user_operator}

    order_dict = {"order_by": order_by,
                 "order_by_operator": order_by_operator}

    user_sql_options_list = []
    for key in arguments_dict:
        if not arguments_dict[key] == None:
            key_operator_string = f"{key}_operator"
            key_operator = arguments_operators_dict[key_operator_string]
            user_sql_options_list.append(f"{key} {key_operator} '{arguments_dict[key]}'")
    sql_list_formatted_1 = ' AND '.join(map(str, user_sql_options_list))
    user_where_string = f"WHERE {sql_list_formatted_1}"

    with sqlite3.connect("pokebot.db") as conn:
        cursor = conn.cursor()
        sqlite_select_query = f"SELECT * FROM pokebot {user_where_string} ORDER BY {order_dict['order_by']} {order_dict['order_by_operator']}"
        try:
            cursor.execute(sqlite_select_query)
            size = 10
            records = cursor.fetchmany(size)
        except Exception as e:
            print(e)
            pass

    try:
        await inter.response.send_message(f"Database query: {sqlite_select_query}\n\n{"\n\n".join(repr(x) for x in records)}")
    except Exception as e:
        print(e)
        await inter.response.send_message("database error")

@custom_db_search.autocomplete("total_ivs")
async def column_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    options = ["species", "total_ivs", "shiny_value", "held_item", "phase_encounters", "phase_same_pkmn_streak", "receiving_user", "message_id"]
    return [app_commands.Choice(name=option, value=option) for option in options if option.lower().startswith(current.lower())][:25]


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

def alpha_stinker_zero_hero_check(pb_message_dict):
    message_id = pb_message_dict['message_id']
    current_alpha = check_current_alpha(pb_message_dict['species'])
    new_alpha = compare_alpha_species(current_alpha, message_id)
    current_highest_iv = check_highest_iv()
    print(f"current_highest_iv: {current_highest_iv}")
    new_hero = compare_highest_iv(current_highest_iv, message_id)
    current_lowest_iv = check_lowest_iv()
    print(f"current_lowest_iv: {current_lowest_iv}")
    current_stinker = check_current_stinker(pb_message_dict['species'])
    new_stinker = compare_stinker_species(current_stinker, message_id)
    new_zero = compare_lowest_iv(current_lowest_iv, message_id)

    return new_alpha, new_hero, new_stinker, new_zero

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

def generate_pokebot_entry(pb_message_dict):
    try:
        with sqlite3.connect("pokebot.db") as conn:
            cursor.execute("""SELECT * FROM pokebot WHERE message_id=? """, (pb_message_dict['message_id'],))
            result = cursor.fetchone()
            if result:
                print("Message ID already found in database. Skipping entry...")
                return
            pokebot_entries = [
                (pb_message_dict['species'],
                pb_message_dict['total_ivs'],
                pb_message_dict['shiny_value'],
                pb_message_dict['held_item'],
                pb_message_dict['total_phase_encounters'],
                pb_message_dict['phase_same_pkmn_streak'],
                'user',
                pb_message_dict['message_id'])
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

        pb_message_dict = {}

        ## Extract 'Shiny Value'
        extracted_shiny_value_dict = fields_list[0]
        shiny_value = extracted_shiny_value_dict["value"]
        print(f"Shiny Value: {shiny_value}")
        pb_message_dict['shiny_value'] = shiny_value

        ## Extract Total IVs
        extracted_total_ivs_dict = fields_list[1]
        total_ivs = extracted_total_ivs_dict["name"]
        ## Trim excess data from Total IVs
        for character in 'IVs() ':
            total_ivs = total_ivs.replace(character, '')
        print(f"Total IVs: {total_ivs}")
        pb_message_dict['total_ivs'] = total_ivs

        ## Extract Held Item
        extracted_held_item_dict = fields_list[2]
        held_item = extracted_held_item_dict["value"]
        print(f"Held Item: {held_item}")
        pb_message_dict['held_item'] = held_item

        ## Extract Species
        extracted_species_dict = fields_list[3]
        species = extracted_species_dict["name"]
        ## Trim excess data from species
        species = species.replace(" Encounters", "")
        print(f"Species: {species}")
        pb_message_dict['species'] = species

        ## Extract Target Phase Encounters
        extracted_target_phase_encounters_dict = fields_list[4]
        target_phase_encounters = extracted_target_phase_encounters_dict["value"]
        print(f"Target Phase Encounters: {target_phase_encounters}")
        pb_message_dict['target_phase_encounters'] = target_phase_encounters

        ## Extract Total Phase Encounters
        extracted_total_phase_encounters_dict = fields_list[5]
        total_phase_encounters_raw = extracted_total_phase_encounters_dict["value"]
        ## Trim Total Phase Encounters
        total_phase_encounters_string = total_phase_encounters_raw.split(' ', 1)[0]
        total_phase_encounters_rate_string = total_phase_encounters_raw.split(' ', 1)[1]
        total_phase_encounters = int(total_phase_encounters_string.replace(",", ""))
        print(f"Total Phase Encounters: {total_phase_encounters}")
        print(f"Total Phase Encounters Hourly Rate: {total_phase_encounters_rate_string}")
        pb_message_dict['total_phase_encounters'] = total_phase_encounters

        ## Extract Phase Same Pokémon Streak
        extracted_phase_same_pkmn_streak_dict = fields_list[8]
        phase_same_pkmn_streak = extracted_phase_same_pkmn_streak_dict["value"]
        ## Trim excess data from Phase Same Pokémon Streak
        phase_same_pkmn_streak = phase_same_pkmn_streak.replace(" were encountered in a row!", "")
        pb_message_dict['phase_same_pkmn_streak'] = phase_same_pkmn_streak

        ## Receiving User
        #pb_message_dict[user] = user

        ## Message ID
        message_id = message.id
        pb_message_dict['message_id'] = message_id

        return pb_message_dict

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
