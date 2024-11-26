"""
Initiative Tracker by Izaaq Ahmad Izham
TODO:
- Make UI to allow for easily adding new characters/monsters, like a small window for a form.
- Make UI for main application [DONE]
- Have a library of pre-made monsters
- Use a .json file to store player and monster data [DONE]
- Maybe monsters don't have checkbox, but when clicked on in "Queue" they are removed? Clicking just adds another monster [DONE]
"""

import json
import random
import sys
from PyQt5 import QtCore, QtWidgets, uic

MONSTERS_FILE = "data/monsters.json"
PLAYERS_FILE = "data/players.json"
MAIN_UI_FILE = "ui/initiativeTracker.ui"
NEW_CHAR_UI_FILE = "ui/newCharForm.ui"


class InitiativeItemWidget(QtWidgets.QWidget):
    def __init__(self, data, name=None, parent=None):
        super().__init__(parent)
        self.data = data
        self.name = name

        self.label = QtWidgets.QLabel(self.name)
        self.setupLayout()

    def setupLayout(self) -> None:
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def getData(self) -> dict:
        return self.data

    def getName(self) -> str:
        return self.name


class MonsterItemWidget(InitiativeItemWidget):
    clicked = QtCore.pyqtSignal(object)

    def __init__(self, data, name=None, parent=None):
        super().__init__(data, name=name, parent=parent)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self)
        super().mousePressEvent(event)


class PlayerItemWidget(InitiativeItemWidget):
    checkboxStateChanged = QtCore.pyqtSignal(object)

    def __init__(self, data, hasCheckbox=True, parent=None):
        name = "{0} ({1})".format(data["char_name"], data["player_name"])
        super().__init__(data, name=name, parent=parent)
        self.hasCheckbox = hasCheckbox

        if self.hasCheckbox:
            self.checkbox = QtWidgets.QCheckBox()
            self.checkbox.stateChanged.connect(self.onCheckboxStateChanged)
            self.layout().insertWidget(0, self.checkbox)

    def onCheckboxStateChanged(self, _) -> None:
        self.checkboxStateChanged.emit(self)

    def isChecked(self) -> bool:
        return self.hasCheckbox and self.checkbox.isChecked()

    def mousePressEvent(self, event) -> None:
        if self.hasCheckbox:
            self.checkbox.toggle()

        super().mousePressEvent(event)


class NewCharacterForm(QtWidgets.QDialog):
    def __init__(self, charList, isPlayer=True, parent=None):
        super().__init__(parent)
        uic.loadUi(NEW_CHAR_UI_FILE, self)

        self.charList = charList
        self.isPlayer = isPlayer
        self.file = MONSTERS_FILE
        if self.isPlayer:
            self.file = PLAYERS_FILE

        self.initUI()

    def initUI(self) -> None:
        """
        Initialise UI
        """
        self.playerLabel.setHidden(not self.isPlayer)
        self.playerLineEdit.setHidden(not self.isPlayer)
        self.saveButton.clicked.connect(self.save)

    def save(self) -> None:
        if not self.charLineEdit.text():
            print("Character name was not added. Please add.")
            return

        if not self.dexLineEdit.text():
            print("Dexterity was not added. Please add.")
            return

        data = {"char_name": self.charLineEdit.text(), "dex": int(self.dexLineEdit.text())}
        if self.isPlayer:
            if not self.playerLineEdit.text():
                print("Player name was not added. Please add.")
                return

            data["player_name"] = self.playerLineEdit.text()

        # Check for duplicates
        for character in self.charList:
            if character == data:
                print("Character {} already exists. Duplicate not added.".format(data["char_name"]))
                return

        self.charList.append(data)

        # Write to file
        with open(self.file, "w") as jsonFile:
            json.dump(self.charList, jsonFile, indent=4)

        self.accept()


class InitiativeTracker(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(MAIN_UI_FILE, self)
        self.monsterCounts = {}
        self.playerList = []
        self.monsterList = []

        self.updateLists()
        self.initUI()

    def initUI(self) -> None:
        """
        Initialise UI.
        """
        self.setWindowTitle("Izaaq's Initiative Tracker")

        self.addPlayerButton.clicked.connect(lambda: self.addNewChar(self.playerList, isPlayer=True))
        self.addMonsterButton.clicked.connect(lambda: self.addNewChar(self.monsterList, isPlayer=False))
        self.initiativeButton.clicked.connect(self.calculateInitiative)

    def updateLists(self):
        """
        Update the monster and player lists. Called when the file gets updated.
        """
        with open(PLAYERS_FILE) as playerData:
            self.playerList = json.load(playerData)

        with open(MONSTERS_FILE) as monsterData:
            self.monsterList = json.load(monsterData)

        self.populatePlayerListWidget()
        self.populateMonsterListWidget()

    def addNewChar(self, charList: list, isPlayer: bool) -> None:
        """
        Adds a new character to the database, whether it be monster or player.
        :param charList: [dict]. A list of dictionary entries representing data of new character.
        :param isPlayer: bool. Whether the character added is a PC or not.
        :return:
        """
        newCharForm = NewCharacterForm(charList, isPlayer=isPlayer, parent=self)

        if newCharForm.exec_() == QtWidgets.QDialog.Accepted:
            self.updateLists()

    def populatePlayerListWidget(self) -> None:
        """
        Populate player list widget.
        """
        self.playerListWidget.clear()
        for character in self.playerList:
            item = QtWidgets.QListWidgetItem()

            playerWidget = PlayerItemWidget(character)
            playerWidget.checkboxStateChanged.connect(self.onCheckboxStateChanged)
            item.setSizeHint(playerWidget.sizeHint())
            self.playerListWidget.addItem(item)
            self.playerListWidget.setItemWidget(item, playerWidget)

    def populateMonsterListWidget(self) -> None:
        """
        Populate monster list widget.
        """
        self.monsterListWidget.clear()
        for monster in self.monsterList:
            item = QtWidgets.QListWidgetItem()
            monsterWidget = MonsterItemWidget(monster, name=monster["char_name"])
            monsterWidget.clicked.connect(self.onMonsterItemClicked)
            item.setSizeHint(monsterWidget.sizeHint())

            self.monsterListWidget.addItem(item)
            self.monsterListWidget.setItemWidget(item, monsterWidget)

    def onCheckboxStateChanged(self, _) -> None:
        """
        Update the "Queue" item widget to include this item if checked, remove otherwise.
        """

        currentNames = set(
            self.selectedListWidget.itemWidget(self.selectedListWidget.item(i)).getName()
            for i in range(self.selectedListWidget.count())
        )

        itemsToAdd = []
        itemsToRemove = []

        for i in range(self.playerListWidget.count()):
            item = self.playerListWidget.item(i)
            itemWidget = self.playerListWidget.itemWidget(item)

            if itemWidget.isChecked() and itemWidget.getName() not in currentNames:
                itemsToAdd.append(itemWidget)

            else:
                if not itemWidget.isChecked():
                    for j in range(self.selectedListWidget.count()):
                        queueItem = self.selectedListWidget.item(j)
                        queueWidget = self.selectedListWidget.itemWidget(queueItem)

                        if queueWidget.getName() == itemWidget.getName():
                            itemsToRemove.append(queueItem)
                            break

        # Add new items to the list widget
        for itemWidget in itemsToAdd:
            selectedItem = QtWidgets.QListWidgetItem()
            newWidget = PlayerItemWidget(itemWidget.getData(), hasCheckbox=False)
            selectedItem.setSizeHint(newWidget.sizeHint())
            self.selectedListWidget.addItem(selectedItem)
            self.selectedListWidget.setItemWidget(selectedItem, newWidget)

        # Remove the selected items from the list widget
        for item in itemsToRemove:
            self.selectedListWidget.takeItem(self.selectedListWidget.row(item))

    def onMonsterItemClicked(self, widget: MonsterItemWidget) -> None:
        """
        Behaviour for when an item widget in the Monster List Widget is clicked on.
        :param widget: The widget which was clicked on.
        """
        monsterName = widget.data["char_name"]
        if monsterName not in self.monsterCounts:
            self.monsterCounts[monsterName] = 0

        self.monsterCounts[monsterName] += 1

        item = QtWidgets.QListWidgetItem()

        newName = "{0} #{1}".format(monsterName, self.monsterCounts[monsterName])
        newWidget = MonsterItemWidget(widget.data, name=newName)
        newWidget.clicked.connect(self.onQueueItemClicked)

        item.setSizeHint(newWidget.sizeHint())
        self.selectedListWidget.addItem(item)
        self.selectedListWidget.setItemWidget(item, newWidget)

    def onQueueItemClicked(self, widget: InitiativeItemWidget) -> None:
        """
        Behaviour to remove monster item widgets from queue when they are clicked on.
        :param widget: Widget that was clicked on.
        """
        listWidget = self.selectedListWidget

        for i in range(listWidget.count()):
            item = listWidget.item(i)
            itemWidget = listWidget.itemWidget(item)

            if itemWidget == widget:
                monsterName = widget.data["char_name"]
                self.monsterCounts[monsterName] -= 1
                if self.monsterCounts[monsterName] == 0:
                    del self.monsterCounts[monsterName]

                listWidget.takeItem(i)
                break

    def calculateInitiative(self) -> None:
        """
        Calculate initiative with all selected players and monsters.
        """
        initiatives = []
        for i in range(self.selectedListWidget.count()):
            itemWidget = self.selectedListWidget.itemWidget(self.selectedListWidget.item(i))
            data = itemWidget.getData()
            name = itemWidget.getName()
            dex = int(data["dex"])
            initiativeRoll = random.randint(1, 20) + calculateModifier(dex)
            initiatives.append((name, initiativeRoll))

        # Sort in descending order
        initiatives.sort(key=lambda x: x[1], reverse=True)
        self.initiativeListWidget.clear()
        for name, roll in initiatives:
            self.initiativeListWidget.addItem("{0} ({1})".format(name, roll))


def calculateModifier(abilityScore: int) -> int:
    """
    Calculate the modifier from the given ability score using DnD 5E's calculations.
    :param abilityScore: Ability score of character
    :return: Modifier of the given score.
    """
    return (abilityScore - 10) // 2


if __name__ == "__main__":
    try:
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication(sys.argv)
        window = InitiativeTracker()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print("ERROR: {}".format(e))
