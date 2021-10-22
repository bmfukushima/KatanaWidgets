import os

from cgwidgets.utils import getJSONData

def getAllTabTypes():
    """
    Gets a list of all of the different possible tab types.

    Returns (list): of tab names (strings)

    """
    from UI4.App import Tabs

    tabPluginSearchPaths = Tabs.GetTabPluginSearchPaths()
    tabTypeNamesByPath = {}
    tabs = []

    for tabTypeName in sorted(Tabs.GetAvailableTabTypeNames()):
        tabPluginPath = Tabs.GetTabPluginPath(tabTypeName)
        for tabPluginSearchPath in tabPluginSearchPaths:
            if tabPluginPath.startswith(tabPluginSearchPath):
                tabTypeNamesByPath.setdefault(tabPluginSearchPath, []).append(tabTypeName)

    for tabPluginSearchPath in tabPluginSearchPaths:
        tabTypeNames = tabTypeNamesByPath.get(tabPluginSearchPath)
        if not tabTypeNames:
            continue

        tabs += tabTypeNames

    return tabs


def getKatanaConstructors():
    """
    Gets all of the tabs, and returns them
    Returns:

    """
    tabs = getAllTabTypes()
    tab_data = {}

    for TAB_NAME in tabs:
        if TAB_NAME == "Node Graph":
            tab_data[TAB_NAME] = """
from Widgets2 import AbstractNodegraphWidget
widget=AbstractNodegraphWidget(self)"""
        else:
            tab_data[TAB_NAME] = """
from UI4.App import Tabs
tab_constructor = Tabs._LoadedTabPluginsByTabTypeName
widget = tab_constructor[\"{TAB_NAME}\"].data(None)""".format(TAB_NAME=TAB_NAME)

    return tab_data


def getConstructors(*args):
    """
    Retuns all of the widgets that are available to to be used in the PiPWidget.

    Args:
        *args (file paths): json files paths can be added as args to be loaded
            into the widgets as useable widgets for the user to look at in the PiPWidget

            {"widget name": "constructor code",
            "widget name": "constructor code",
            "widget name": "constructor code",}

            Note: Constructor code returns the instance of a widget defined as the variable "widget"
                ie. widget = QLabel()
    """

    constructors = {}

    # get Katana PiP constructors
    #constructors_file_path = os.path.dirname(__file__) + '/KatanaConstructors.json'
    #katana_constructors = getJSONData(constructors_file_path)
    katana_constructors = getKatanaConstructors()
    constructors.update(katana_constructors)

    # get args provided
    for path in args:
        constructor = getJSONData(path)
        constructors.update(constructor)

    return constructors


def getSaveData(*args):
    """
    Gets all of the save file locations/data associated with the PiP Tab

    Args:
        *args (dict): Additional save locations can be provided as dicts in the following format
            {"Dir Name: {
                "file_path": "/path/to/dir/something.json",
                "locked": bool}}
    Returns (dict):
        {"Dir Name: {
            "file_path": "/path/to/dir/something.json",
            "locked": bool},
        "KatanaBebop": {
            "file_path": built_ins_file_path,
            "locked": False},
        "User": {
            "file_path": user_save_path,
            "locked": False}}

    """
    # built ins
    built_ins_file_path = os.path.dirname(__file__) + '/.PiPWidgets.json'

    # user
    user_save_path = os.environ["HOME"] + '/.katana/.PiPWidgets.json'

    # default save data
    save_data = {
        "KatanaBebop": {
            "file_path": built_ins_file_path,
            "locked": False},
        "User": {
            "file_path": user_save_path,
            "locked": False}
    }

    # args data
    for arg in args:
        save_data.update(arg)

    return save_data


# example of creating additional constructors
widget_types = {
    "QLabel": """
from qtpy.QtWidgets import QLabel
widget = QLabel(\"TEST\") """,
    "QPushButton":"""
from qtpy.QtWidgets import QPushButton
widget = QPushButton(\"TESTBUTTON\") """
}

import json
file_path = os.path.dirname(__file__) + "ExampleConstructors.json"
if file_path:
    # Writing JSON data
    with open(file_path, 'w') as f:
        json.dump(widget_types, f)