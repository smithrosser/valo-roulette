import json
import os

from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtGui import QPixmap

PLAYER_DATA_PATH = "./players.json"
SCHEMA_PATH = "./schema.json"
AGENT_ICON_DATA_PATH = "./agent_icons.json"
CLICK_SOUND_PATH = "./res/click.wav"


def load_player_data(path):
    player_data = {}

    # Create empty 'players.json' if it doesn't exist
    if not os.path.exists(path):
        save_player_data(player_data, path)

    player_data_file = open(path, "r")
    player_data = json.load(player_data_file)
    player_data_file.close()

    return player_data


def save_player_data(player_data, path):
    output_str = ""

    player_data_file = open(path, "w")
    output_str = json.dumps(player_data, indent=4, sort_keys=True)
    player_data_file.write(output_str)
    player_data_file.close()


def load_schema(path):
    schema = {}

    schema_file = open(path)
    schema = json.load(schema_file)
    schema_file.close()

    return schema


def load_agent_icons(path, width, height):
    agent_icons = {}
    agent_icon_paths = {}

    agent_icons_file = open(path, "r")
    agent_icon_paths = json.load(agent_icons_file)
    agent_icons_file.close()

    for key in agent_icon_paths:
        agent_icons[key] = QPixmap(agent_icon_paths[key]).scaled(width, height)

    return agent_icons


def load_sounds():
    sounds = {}

    sounds["click"] = QSoundEffect()
    sounds["click"].setSource(
        QUrl.fromLocalFile(CLICK_SOUND_PATH))
    sounds["click"].setVolume(0.25)

    return sounds
