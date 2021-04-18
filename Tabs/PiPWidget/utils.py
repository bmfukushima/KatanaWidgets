import os

from cgwidgets.utils import getJSONData

def getConstructors(*args):
    """
    Retuns all of the widgets that are available to to be used in the PiPWidget.

    Args:
        *args (file paths): json files paths can be added as args to be loaded
            into the widgets as useable widgets for the user to look at in the PiPWidget

            {"widget name": "constructor code",
            "widget name": "constructor code",
            "widget name": "constructor code",}

    """

    constructors = {}

    # get Katana PiP constructors
    constructors_file_path = os.path.dirname(__file__) + '/KatanaConstructors.json'
    katana_constructors = getJSONData(constructors_file_path)
    constructors.update(katana_constructors)

    # get args provided
    for path in args:
        constructor = getJSONData(path)
        constructors.update(constructor)

    return constructors


# example of creating additional constructors
# widget_types = {
#     "QLabel": """
# from qtpy.QtWidgets import QLabel
# widget = QLabel(\"TEST\") """,
#     "QPushButton":"""
# from qtpy.QtWidgets import QPushButton
# widget = QPushButton(\"TESTBUTTON\") """
# }
#
# import json
# file_path = "/media/ssd01/dev/katana/KatanaWidgets/Tabs/PiPWidget/.PiPWidgetsTest.json"
# if file_path:
#     # Writing JSON data
#     with open(file_path, 'w') as f:
#         json.dump(widget_types, f)