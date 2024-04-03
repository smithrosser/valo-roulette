#!/usr/bin/env python3

import sys
import random
import math

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtMultimedia import QSoundEffect

import assets

AGENT_RANDOM_WEIGHT = 2


class RouletteWorker(QObject):
    change_icon = pyqtSignal()
    play_sound = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, mute):
        super().__init__()
        self.is_muted = mute

    # Emits a signal quickly at first, then gradually slower --
    # simulates a spinning roulette wheel (a bit ganky but it works)
    def run(self):
        delay = 50.0

        for i in range(30):
            self.change_icon.emit()
            if not self.is_muted:
                self.play_sound.emit()

            QThread.msleep(math.floor(delay))
            if i > 5:
                delay *= 1.11

        self.finished.emit()


class WeaponWidget(QWidget):
    def __init__(self, vr, weapon_class):
        super().__init__()
        self.vr_ = vr
        self.weapon_class = weapon_class

        self.current_weapon = ""

        self.layout = QVBoxLayout()
        self.icon_weapon = QLabel("?",)
        self.icon_weapon.setFont(self.vr_.font_large)
        self.icon_weapon.setFixedSize(220, 220)
        self.icon_weapon.setStyleSheet("border: 1px solid #aaaaaa")
        self.icon_weapon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.button_roll = QPushButton("Roll " + self.weapon_class)

        self.button_roll.clicked.connect(self.cb_roll_clicked)

        self.layout.addWidget(self.icon_weapon)
        self.layout.addWidget(self.button_roll)
        self.setLayout(self.layout)

    def cb_roll_clicked(self):
        # Create worker thread to 'spin' through different guns
        self.thread = QThread()
        self.worker = RouletteWorker(False)

        # Connect signals to relevant callbacks
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.change_icon.connect(
            self.cb_roulette_worker_randomize_weapon)
        self.worker.play_sound.connect(
            self.cb_roulette_worker_play_sound)
        self.worker.finished.connect(
            lambda: self.button_roll.setEnabled(True))
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.button_roll.setEnabled(False)
        self.thread.start()

    def cb_roulette_worker_randomize_weapon(self):
        self.set_random_weapon()

    def cb_roulette_worker_play_sound(self):
        self.vr_.sounds["click"].play()

    def set_random_weapon(self):
        weapon_pool = self.vr_.weapons[self.weapon_class]

        weapon = random.choice(weapon_pool)
        while self.current_weapon == weapon:
            weapon = random.choice(weapon_pool)
        self.current_weapon = weapon

        self.icon_weapon.setPixmap(
            self.vr_.weapon_icons[self.current_weapon])


class LobbyPlayerWidget(QWidget):
    def __init__(self, vr, player_name):
        super().__init__()
        self.vr_ = vr  # Reference to main ValoRoulette class
        self.player_name = player_name

        # Set up player widget
        self.layout = QHBoxLayout()
        self.label_player = QLabel(player_name)
        self.label_player.setMinimumHeight(125)
        self.label_player.setFont(self.vr_.font_large)
        self.button_roll = QPushButton("Roll")
        self.button_roll.setMinimumHeight(50)

        self.icon_agent = QLabel("?")
        self.icon_agent.setFont(self.vr_.font_large)
        self.icon_agent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_agent.setMinimumSize(125, 125)
        self.icon_agent.setStyleSheet("border: 1px solid #aaaaaa")

        # Connect 'clicked' signals to their callback functions
        self.button_roll.clicked.connect(lambda: self.cb_roll_clicked(False))

        self.layout.addWidget(self.label_player)
        self.layout.addWidget(self.button_roll)
        self.layout.addWidget(self.icon_agent)
        self.layout.setStretch(0, 1)
        self.setLayout(self.layout)

    # Called when 'Roll' button is clicked
    def cb_roll_clicked(self, mute):
        # Create worker thread to 'spin' through different agents
        self.thread = QThread()
        self.worker = RouletteWorker(mute)

        # Connect signals to relevant callbacks
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.change_icon.connect(
            self.cb_roulette_worker_randomize_agent)
        self.worker.play_sound.connect(self.cb_roulette_worker_play_sound)
        self.worker.finished.connect(
            lambda: self.button_roll.setEnabled(True))
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Disable 'roll' button until finished, start thread
        self.button_roll.setEnabled(False)
        self.thread.start()

    # Called every time roulette wheel 'clicks' -- picks a random agent, displays it
    def cb_roulette_worker_randomize_agent(self):
        random_agent = self.vr_.get_random_agent(self.player_name)

        self.vr_.set_player_agent(self.player_name, random_agent)
        self.set_agent_icon(random_agent)

    # Play a click sound!
    def cb_roulette_worker_play_sound(self):
        self.vr_.sounds["click"].play()

    # Sets the agent icon
    def set_agent_icon(self, agent_name):
        self.icon_agent.setPixmap(self.vr_.agent_icons[agent_name])


class LobbyWidget(QWidget):
    def __init__(self, vr):
        super().__init__()
        self.vr_ = vr  # Reference to main ValoRoulette class

        # Main layout
        self.layout_main = QVBoxLayout()
        self.layout_main.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Lobby control layout (add/clear players)
        self.layout_lobby_control = QHBoxLayout()
        self.combo_players = QComboBox()
        self.button_add = QPushButton("Add")
        self.button_clear = QPushButton("Clear")
        self.checkbox_dealers_choice = QCheckBox("Dealer's Choice")
        self.checkbox_optimal_comps = QCheckBox("Prefer optimal comp for")
        self.combo_maps = QComboBox()

        self.layout_roulette = QHBoxLayout()

        # Lobby player list layout
        self.layout_lobby = QVBoxLayout()
        self.layout_lobby.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.widget_map_lobby_players = {}

        # Lobby weapons layout
        self.layout_weapons = QVBoxLayout()
        self.layout_weapons.addWidget(WeaponWidget(self.vr_, "primary"))
        self.layout_weapons.addWidget(WeaponWidget(self.vr_, "sidearm"))
        self.layout_weapons.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Connect 'clicked' signals to their callback functions
        self.button_add.clicked.connect(self.cb_add_clicked)
        self.button_clear.clicked.connect(self.cb_clear_clicked)
        self.checkbox_dealers_choice.stateChanged.connect(
            self.cb_dealers_choice_state_changed)
        self.checkbox_optimal_comps.stateChanged.connect(
            self.cb_optimal_comps_state_changed)

        # Add widgets to layouts
        self.layout_lobby_control.addWidget(self.combo_players)
        self.layout_lobby_control.addWidget(self.button_add)
        self.layout_lobby_control.addWidget(self.button_clear)
        self.layout_lobby_control.addWidget(self.checkbox_dealers_choice)
        self.layout_lobby_control.addWidget(self.checkbox_optimal_comps)
        self.layout_lobby_control.addWidget(self.combo_maps)
        self.layout_lobby_control.setStretch(0, 1)

        # Update combobox from player data & update lobby player list
        self.populate_player_combobox()
        self.populate_map_combobox()
        self.update_lobby_widget()

        # Disable optimal comps for now
        self.combo_maps.setEnabled(False)
        self.checkbox_optimal_comps.setEnabled(False)

        # Add player/weapon roulette layouts side-by-side
        self.layout_roulette.addLayout(self.layout_lobby)
        self.layout_roulette.addLayout(self.layout_weapons)
        self.layout_roulette.setStretch(0, 1)

        # Add layouts to main widget
        self.layout_main.addLayout(self.layout_lobby_control)
        self.layout_main.addLayout(self.layout_roulette)
        self.setLayout(self.layout_main)

    # Called when 'Clear' button is clicked
    def cb_clear_clicked(self):
        self.vr_.clear_lobby()
        self.update_lobby_widget()

    # Called when 'Add' button is clicked
    def cb_add_clicked(self):
        if len(self.vr_.current_lobby) >= 5:
            return

        new_player = self.combo_players.currentText()
        self.vr_.add_player_to_lobby(new_player)
        self.update_lobby_widget()

    def cb_dealers_choice_state_changed(self):
        self.vr_.is_dealers_choice_enabled = True if self.checkbox_dealers_choice.checkState(
        ) == Qt.CheckState.Checked else False

    def cb_optimal_comps_state_changed(self):
        self.vr_.is_optimal_comp_enabled = True if self.checkbox_optimal_comps.checkState(
        ) == Qt.CheckState.Checked else False

    # Adds players to the 'players' dropdown menu
    def populate_player_combobox(self):
        for key in self.vr_.players:
            self.combo_players.addItem(key)

    def populate_map_combobox(self):
        maps = ["Ascent", "Lotus", "Icebox",
                "Sunset", "Split", "Bind", "Breeze"]

        for map in maps:
            self.combo_maps.addItem(map)

    # Updates the lobby based on players present
    def update_lobby_widget(self):
        # Remove widgets for players that aren't in current lobby (make temp copy to avoid runtime error)
        temp_widgets = self.widget_map_lobby_players.copy()
        for key in self.widget_map_lobby_players:
            if not key in self.vr_.current_lobby:
                self.widget_map_lobby_players[key].hide()
                temp_widgets.pop(key)
        self.widget_map_lobby_players = temp_widgets

        # Add widgets for players in lobby that don't have them yet
        for key in self.vr_.current_lobby:
            if not key in self.widget_map_lobby_players:
                self.widget_map_lobby_players[key] = LobbyPlayerWidget(
                    self.vr_, key)
                self.layout_lobby.addWidget(self.widget_map_lobby_players[key])


class MainWindow(QWidget):
    def __init__(self, vr):
        super().__init__()
        self.vr_ = vr  # Reference to main ValoRoulette class

        self.layout_main = QStackedLayout()
        self.widget_lobby = LobbyWidget(self.vr_)

        self.layout_main.addWidget(self.widget_lobby)
        self.setLayout(self.layout_main)
        self.setMinimumWidth(700)
        self.setWindowTitle("VALORANT Agent Roulette")


class ValoRoulette:
    def __init__(self):
        # Player/lobby data
        self.players = assets.load_player_data(assets.PLAYER_DATA_PATH)
        self.weapons = assets.load_weapons(assets.WEAPON_DATA_PATH)
        self.agent_icons = assets.load_agent_icons(
            assets.AGENT_ICON_DATA_PATH, 125, 125)
        self.weapon_icons = assets.load_weapon_icons(
            assets.AGENT_ICON_DATA_PATH)
        self.sounds = assets.load_sounds()

        self.current_lobby = {}
        self.is_dealers_choice_enabled = False
        self.is_optimal_comp_enabled = False

        self.font_large = QFont("Segoe UI")
        self.font_large.setPointSize(18)

    # Add a player to current lobby
    def add_player_to_lobby(self, player_name):
        if len(self.current_lobby) >= 5:
            return
        if player_name in self.current_lobby:
            return

        self.current_lobby[player_name] = self.players[player_name]

    # Remove a player from current lobby
    def remove_player_from_lobby(self, player_name):
        if not player_name in self.current_lobby:
            return

        self.current_lobby.pop(player_name)

    # Clears the lobby
    def clear_lobby(self):
        self.current_lobby.clear()

    # Returns a list of available agents
    def get_player_agent_pool(self, player_name):
        agent_pool = []

        # Loop through player's agent_pool
        for key in self.players[player_name]["agent_pool"]:
            # Add to agent_pool list if available
            if self.players[player_name]["agent_pool"][key] == True and not self.is_agent_taken(key):
                # Weight agents over dealer's choice more
                for i in range(AGENT_RANDOM_WEIGHT):
                    agent_pool.append(key)

        if self.is_dealers_choice_enabled and not self.players[player_name]["selected"] == "Dealer":
            agent_pool.append("Dealer")

        return agent_pool

    # Checks if agent is already taken in the lobby
    def is_agent_taken(self, agent_name):
        for key in self.current_lobby:
            if self.current_lobby[key]["selected"] == agent_name:
                return True

        return False

    # Selects a random agent from a player's agent pool
    def get_random_agent(self, player_name):
        agent_pool = self.get_player_agent_pool(player_name)
        return random.choice(agent_pool)

    def set_player_agent(self, player_name, agent_name):
        if not player_name in self.current_lobby:
            return

        self.current_lobby[player_name]["selected"] = agent_name


def main():
    app = QApplication(sys.argv)
    vr = ValoRoulette()
    window = MainWindow(vr)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
