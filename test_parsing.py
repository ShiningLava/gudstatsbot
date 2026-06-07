"""
Tests for the Pokebot message-parsing pipeline (variable_cleanup branch).

Goal: validate that an incoming Pokebot encounter message is parsed correctly
and that the right rows land in the database -- WITHOUT touching Discord.

This branch splits the pipeline into three functions (vs. the old one-shot):

    parse_pokebot_message(message)      -> pb_message_dict (or None)
    generate_pokebot_entry(dict)        -> inserts a row (idempotent on id)
    alpha_stinker_zero_hero_check(dict) -> (new_personal_alpha, new_global_alpha,
                                            new_hero, new_personal_stinker,
                                            new_global_stinker, new_zero)

The bot only reads three things off an incoming message:

    message.content              -> str   (also where the <@user> mention lives)
    message.embeds[0].to_dict()  -> dict  (the encounter embed)
    message.id                   -> int

so we fake exactly those. No gateway, no network. The DB is a throwaway
pokebot.db inside a pytest temp dir (we chdir into it before importing main.py,
because main.py opens "pokebot.db" by relative path at import time).

The make_embed() layout below mirrors the REAL embed structure visible in
main.py's `pokebot_test` command (9 fields, IVs/species carried in the field
*name*), so these fixtures are ground truth, not guesses.
"""

import importlib
import json
import os
import sqlite3
import sys
import asyncio

import pytest

# Capture the repo dir NOW, before any fixture chdir's away from it.
REPO_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Fake Discord objects (duck-typed; importing main.py needs discord.py, but the
# message/channel we feed it do not).
# ---------------------------------------------------------------------------
class FakeEmbed:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data


class FakeAuthor:
    def __init__(self, author_id):
        self.id = author_id


class FakeChannel:
    """Records anything the bot tries to send instead of hitting Discord."""
    def __init__(self):
        self.sent = []

    async def send(self, *args, **kwargs):
        self.sent.append((args, kwargs))


class FakeMessage:
    def __init__(self, *, content, embed=None, message_id=1, author_id=0, channel=None):
        self.content = content
        self.embeds = [FakeEmbed(embed)] if embed is not None else []
        self.id = message_id
        self.author = FakeAuthor(author_id)
        self.channel = channel


def make_embed(
    *,
    shiny_value="3",
    total_ivs="106",
    held_item="None",
    species="Wurmple",
    target_phase="305",
    total_phase="1,634 (260/h)",
    streak="9 Poochyena were encountered in a row!",
):
    """A realistic 9-field Pokebot encounter embed (mirrors `pokebot_test`).

    Field indices match what parse_pokebot_message() reads:
      [0] shiny value (value)         [1] IVs   (in name, "IVs (106)")
      [2] held item (value)           [3] species (in name, "<species> Encounters")
      [4] target phase enc. (value)   [5] total phase enc. (value, "1,634 (260/h)")
      [6],[7] empty spacer fields      [8] same-pokemon streak (value)
    """
    return {
        "fields": [
            {"name": "Shiny Value", "value": shiny_value},                   # 0
            {"name": f"IVs ({total_ivs})", "value": "<iv-table>"},           # 1 (name)
            {"name": "Held item", "value": held_item},                       # 2
            {"name": f"{species} Encounters", "value": "x (1)"},             # 3 (name)
            {"name": f"{species} Phase Encounters", "value": target_phase},  # 4
            {"name": "Phase Encounters", "value": total_phase},              # 5
            {"name": "Empty Field", "value": "Empty Field"},                 # 6
            {"name": "Empty Field", "value": "Empty Field"},                 # 7
            {"name": "Phase Same Pokemon Streak", "value": streak},          # 8
        ]
    }


def build_message(
    *,
    species="Wurmple",
    total_ivs="106",
    shiny_value="3",
    held_item="None",
    target_phase="305",
    total_phase="1,634 (260/h)",
    streak="9 Poochyena were encountered in a row!",
    user="223895172675534848",
    message_id=1,
    prefix="Encountered a",
    author_id=0,
    channel=None,
):
    """A complete fake encounter message ready to feed the pipeline."""
    content = f"{prefix} {species}!"
    if user is not None:
        content += f"\n<@{user}>"
    return FakeMessage(
        content=content,
        embed=make_embed(
            species=species,
            total_ivs=total_ivs,
            shiny_value=shiny_value,
            held_item=held_item,
            target_phase=target_phase,
            total_phase=total_phase,
            streak=streak,
        ),
        message_id=message_id,
        author_id=author_id,
        channel=channel,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def bot(tmp_path_factory):
    """Import main.py against a throwaway working directory.

    main.py reads config.json and opens pokebot.db (both relative) at import
    time, so we set up a temp cwd with a synthetic config first. target_user_1
    here doubles as the 'Pokebot' author id used by the on_message tests.
    """
    workdir = tmp_path_factory.mktemp("botcwd")
    (workdir / "config.json").write_text(
        json.dumps(
            {
                "token": "test-token-not-real",
                "guild_id": "123456789012345678",
                "target_user_1": "111111111111111111",
                "target_channel": "222222222222222222",
            }
        )
    )
    original_cwd = os.getcwd()
    os.chdir(workdir)
    sys.path.insert(0, REPO_DIR)
    try:
        module = importlib.import_module("main")
        yield module
    finally:
        os.chdir(original_cwd)


# The Pokebot author id the bot listens for (matches target_user_1 above).
POKEBOT_AUTHOR_ID = 111111111111111111


@pytest.fixture(autouse=True)
def fresh_table(bot):
    """Give every test an empty pokebot table."""
    conn = sqlite3.connect("pokebot.db")
    conn.execute("DROP TABLE IF EXISTS pokebot")
    conn.commit()
    conn.close()
    bot.initial_create_db()
    yield


def fetch_all_rows():
    conn = sqlite3.connect("pokebot.db")
    try:
        return conn.execute(
            "SELECT species, total_ivs, shiny_value, held_item, "
            "phase_encounters, phase_same_pkmn_streak, receiving_user, message_id "
            "FROM pokebot"
        ).fetchall()
    finally:
        conn.close()


def record(bot, **kw):
    """parse -> generate (the order on_message uses); returns the parsed dict."""
    pb = bot.parse_pokebot_message(build_message(**kw))
    bot.generate_pokebot_entry(pb)
    return pb


# ---------------------------------------------------------------------------
# Stage 1: parse_pokebot_message -> dict  (the important input-parsing piece)
# ---------------------------------------------------------------------------
def test_parse_returns_full_dict(bot):
    pb = bot.parse_pokebot_message(
        build_message(
            species="Wurmple",
            total_ivs="106",
            shiny_value="3",
            held_item="None",
            target_phase="305",
            total_phase="1,634 (260/h)",
            streak="9 Poochyena were encountered in a row!",
            user="223895172675534848",
            message_id=555,
        )
    )
    assert pb == {
        "shiny_value": "3",
        "total_ivs": "106",
        "held_item": "None",
        "species": "Wurmple",
        "target_phase_encounters": "305",
        "total_phase_encounters": 1634,          # parsed from "1,634 (260/h)"
        "phase_same_pkmn_streak": "9 Poochyena",  # trailing phrase trimmed
        "user": "223895172675534848",
        "message_id": 555,
    }


def test_parse_extracts_user_from_mention(bot):
    pb = bot.parse_pokebot_message(
        build_message(user="223895172675534848", message_id=556)
    )
    assert pb["user"] == "223895172675534848"


def test_parse_defaults_user_when_no_mention(bot):
    pb = bot.parse_pokebot_message(build_message(user=None, message_id=557))
    assert pb["user"] == "user"


def test_parse_ignores_non_encounter_message(bot):
    assert bot.parse_pokebot_message(
        FakeMessage(content="gm everyone", embed=None, message_id=2)
    ) is None


def test_parse_accepts_received_prefix(bot):
    pb = bot.parse_pokebot_message(
        build_message(species="Charmander", prefix="Received a", message_id=558)
    )
    assert pb is not None
    assert pb["species"] == "Charmander"


def test_parse_raises_indexerror_on_short_embed(bot):
    """Regression: a real captured message (see `user_string_test`) had only 6
    fields (0-5), but parse_pokebot_message reads fields_list[8] unconditionally
    and outside any try/except. A short embed therefore raises IndexError
    straight out of parse -> no DB entry, no reply. This documents the hazard;
    flip to a graceful skip if/when the bot guards the index.
    """
    short_embed = {
        "fields": [
            {"name": "Shiny Value", "value": "3"},
            {"name": "IVs (10)", "value": "x"},
            {"name": "Held item", "value": "None"},
            {"name": "Bulbasaur Encounters", "value": "x"},
            {"name": "Bulbasaur Phase Encounters", "value": "1"},
            {"name": "Phase Encounters", "value": "1 (2/h)"},  # valid, so [8] is the failure
        ]
    }
    msg = FakeMessage(
        content="Encountered a Bulbasaur!\n<@223895172675534848>",
        embed=short_embed,
        message_id=7001,
    )
    with pytest.raises(IndexError):
        bot.parse_pokebot_message(msg)


# ---------------------------------------------------------------------------
# Stage 2: generate_pokebot_entry -> DB row
# ---------------------------------------------------------------------------
def test_generate_inserts_parsed_row(bot):
    """Note SQLite column affinity: INT columns coerce clean numeric strings to
    ints; a streak like '2 Bulbasaur' isn't a clean int so it stays text, and
    message_id (VARCHAR) keeps its text form.
    """
    pb = bot.parse_pokebot_message(
        build_message(
            species="Bulbasaur",
            total_ivs="146",
            shiny_value="3",
            held_item="Oran Berry",
            total_phase="1,234 (5678/h)",
            streak="2 Bulbasaur were encountered in a row!",
            user="223895172675534848",
            message_id=1001,
        )
    )
    bot.generate_pokebot_entry(pb)

    rows = fetch_all_rows()
    assert len(rows) == 1
    species, total_ivs, shiny, held, phase_enc, streak, user, mid = rows[0]
    assert species == "Bulbasaur"
    assert total_ivs == 146                 # "146" -> INT affinity -> 146
    assert shiny == 3                       # "3"   -> INT affinity -> 3
    assert held == "Oran Berry"
    assert phase_enc == 1234                # total_phase_encounters
    assert streak == "2 Bulbasaur"          # not a clean int -> stays text
    assert user == "223895172675534848"
    assert str(mid) == "1001"               # VARCHAR column keeps it as text


def test_generate_entry_is_idempotent(bot):
    """Re-processing the same message (e.g. /database_rebuild) inserts once."""
    pb = bot.parse_pokebot_message(build_message(species="Bulbasaur", message_id=3001))
    bot.generate_pokebot_entry(pb)
    bot.generate_pokebot_entry(pb)

    conn = sqlite3.connect("pokebot.db")
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM pokebot WHERE message_id = ?", ("3001",)
        ).fetchone()[0]
    finally:
        conn.close()
    assert count == 1


# ---------------------------------------------------------------------------
# Stage 3: alpha_stinker_zero_hero_check -> flags
# returns (new_personal_alpha, new_global_alpha, new_hero,
#          new_personal_stinker, new_global_stinker, new_zero)
# (hero/zero come back as None when false -- a known quirk -- so assert by
#  truthiness rather than identity.)
# ---------------------------------------------------------------------------
def test_first_encounter_is_alpha_hero_zero_globally_and_personally(bot):
    pb = record(bot, species="Bulbasaur", total_ivs="100",
                user="223895172675534848", message_id=4001)
    (personal_alpha, global_alpha, hero,
     personal_stinker, global_stinker, zero) = bot.alpha_stinker_zero_hero_check(pb)

    assert global_alpha and personal_alpha
    assert hero and zero
    assert global_stinker and personal_stinker
    assert bot.new_species_check("Bulbasaur") is True


def test_lower_second_encounter_is_stinker_and_zero_not_hero(bot):
    record(bot, species="Bulbasaur", total_ivs="150",
           user="223895172675534848", message_id=5001)
    pb2 = record(bot, species="Bulbasaur", total_ivs="50",
                 user="223895172675534848", message_id=5002)
    (personal_alpha, global_alpha, hero,
     personal_stinker, global_stinker, zero) = bot.alpha_stinker_zero_hero_check(pb2)

    assert not global_alpha and not personal_alpha
    assert not hero                 # not the highest IV anymore
    assert zero                     # is the lowest IV overall
    assert global_stinker and personal_stinker
    assert bot.new_species_check("Bulbasaur") is False


# ---------------------------------------------------------------------------
# on_message: the crash regression + a happy-path end-to-end
# ---------------------------------------------------------------------------
def test_on_message_handles_non_encounter_without_crashing(bot):
    """Regression: the old branch unpacked parse_pokebot_message(...) directly,
    so a None return (non-encounter) raised TypeError inside on_message. This
    branch guards with `if pb_message_dict:`, so a non-encounter from the
    watched author must now no-op cleanly (no send, no exception).
    """
    channel = FakeChannel()
    msg = FakeMessage(
        content="just chatting, not an encounter",
        embed=None,
        message_id=9001,
        author_id=POKEBOT_AUTHOR_ID,   # == target_user_1, so on_message processes it
        channel=channel,
    )
    asyncio.run(bot.on_message(msg))   # must not raise
    assert channel.sent == []


def test_on_message_new_species_announces_and_records(bot):
    """Happy path end-to-end: a brand-new species encounter records a row and
    posts exactly one announcement -- all without Discord."""
    channel = FakeChannel()
    msg = build_message(
        species="Bulbasaur",
        total_ivs="100",
        user="223895172675534848",
        message_id=9100,
        author_id=POKEBOT_AUTHOR_ID,
        channel=channel,
    )
    asyncio.run(bot.on_message(msg))

    assert len(fetch_all_rows()) == 1
    assert len(channel.sent) == 1
    announcement = channel.sent[0][0][0]   # first positional arg of channel.send
    assert "Bulbasaur" in announcement
