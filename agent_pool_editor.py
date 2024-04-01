#!/usr/bin/env python3

import sys

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import assets

PLAYER_DATA_PATH = "./players.json"
AGENT_ICON_DATA_PATH = "./agent_icons.json"


class AgentWidget(QWidget):
    def __init__(self, editor, player_name, agent_name):
        super().__init__()
        self.editor_ = editor
        self.player_name = player_name
        self.agent_name = agent_name

        self.layout = QHBoxLayout()
        self.icon_agent = QLabel()
        self.icon_agent.setPixmap(self.editor_.agent_icons[agent_name])
        self.checkbox = QCheckBox()

        self.checkbox.stateChanged.connect(lambda: self.cb_state_changed())

        self.layout.addWidget(self.icon_agent)
        self.layout.addWidget(self.checkbox)
        self.layout.setStretch(1, 1)
        self.setLayout(self.layout)

    # Called when an agent's checkbox is changed
    def cb_state_changed(self):
        self.editor_.set_player_agent_availability(
            self.player_name, self.agent_name, self.get_state())

    # Sets the agent's checkbox state
    def set_state(self, state):
        self.checkbox.setChecked(state)

    # Retrieves the agent's checkbox state
    def get_state(self):
        return True if self.checkbox.checkState() == Qt.CheckState.Checked else False


class PlayerWidget(QWidget):
    def __init__(self, editor, player_name):
        super().__init__()
        self.editor_ = editor
        self.player_name = player_name

        self.layout = QHBoxLayout()
        self.label_player = QLabel(self.player_name)
        self.label_player.setMinimumWidth(50)
        self.widget_map_agents = {}

        # Add AgentWidget for each agent in the game
        self.layout.addWidget(self.label_player)
        for key in self.editor_.players[player_name]["agent_pool"]:
            self.widget_map_agents[key] = AgentWidget(
                self.editor_, self.player_name, key)
            self.layout.addWidget(self.widget_map_agents[key])
            self.widget_map_agents[key].set_state(
                self.editor_.players[self.player_name]["agent_pool"][key])
        self.layout.setStretch(0, 1)

        self.setLayout(self.layout)


class MainWindow(QWidget):
    def __init__(self, editor):
        super().__init__()
        self.editor_ = editor

        # Set up the main layout
        self.layout_main = QVBoxLayout()

        # Set up the control layout
        self.layout_control = QHBoxLayout()
        self.edit_player_name = QLineEdit()
        self.button_add = QPushButton("Add")
        self.button_remove = QPushButton("Remove")
        self.button_save = QPushButton("Save")
        self.layout_control.addWidget(self.edit_player_name)
        self.layout_control.addWidget(self.button_add)
        self.layout_control.addWidget(self.button_remove)
        self.layout_control.addWidget(self.button_save)
        self.layout_control.setStretch(0, 1)

        # Connect 'on click' signals to callback functions
        self.button_add.clicked.connect(self.cb_button_add)
        self.button_remove.clicked.connect(self.cb_button_remove)
        self.button_save.clicked.connect(self.cb_button_save)

        # Set up the player list
        self.layout_players = QVBoxLayout()
        self.layout_players.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.widget_map_players = {}
        for key in self.editor_.players:
            self.widget_map_players[key] = PlayerWidget(self.editor_, key)
            self.layout_players.addWidget(self.widget_map_players[key])

        self.layout_main.addLayout(self.layout_control)
        self.layout_main.addLayout(self.layout_players)
        self.setLayout(self.layout_main)

        self.setWindowTitle("VALORANT Agent Roulette | Editor")

    # Called when 'Add' button is clicked
    def cb_button_add(self):
        player_name = self.edit_player_name.text()

        if player_name in self.editor_.players:
            self.show_message_box("Error", "Player already in list!")
            return

        self.editor_.add_player(player_name)
        self.add_player_widget(player_name)

    # Called when 'Remove' button is clicked
    def cb_button_remove(self):
        player_name = self.edit_player_name.text()

        if not player_name in self.editor_.players:
            self.show_message_box("Error", "Player not in list!")
            return

        self.editor_.remove_player(player_name)
        self.remove_player_widget(player_name)

    # Called when 'Save' button is clicked
    def cb_button_save(self):
        self.editor_.save_player_data()
        self.show_message_box("Info", "Saved!")

    # Shows a message box
    def show_message_box(self, title, message):
        dlg = QMessageBox(self)

        dlg.setWindowTitle(title)
        dlg.setText(message)
        dlg.setFixedSize(800, 200)
        dlg.exec()

    # Adds a new player widget
    def add_player_widget(self, player_name):
        self.widget_map_players[player_name] = PlayerWidget(
            self.editor_, player_name)
        self.layout_players.addWidget(self.widget_map_players[player_name])

    # Removes the specified player widget
    def remove_player_widget(self, player_name):
        self.widget_map_players[player_name].hide()
        self.widget_map_players.pop(player_name)


class AgentPoolEditor():
    def __init__(self):
        self.players = assets.load_player_data(assets.PLAYER_DATA_PATH)
        self.schema = assets.load_schema(assets.SCHEMA_PATH)
        self.agent_icons = assets.load_agent_icons(
            AGENT_ICON_DATA_PATH, 32, 32)

    # Adds a player to the player list
    def add_player(self, player_name):
        self.players[player_name] = self.schema.copy()

    # Removes a player from the player list
    def remove_player(self, player_name):
        if not player_name in self.players:
            return

        self.players.pop(player_name)

    # Sets the availability of a player's agent
    def set_player_agent_availability(self, player_name, agent_name, state):
        if not player_name in self.players:
            return
        if not agent_name in self.players[player_name]["agent_pool"]:
            return

        self.players[player_name]["agent_pool"][agent_name] = state


def main():
    app = QApplication(sys.argv)
    editor = AgentPoolEditor()
    window = MainWindow(editor)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
