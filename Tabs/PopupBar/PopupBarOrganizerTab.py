import os

from Katana import UI4
from qtpy.QtWidgets import QVBoxLayout

from cgwidgets.widgets import PopupBarOrganizerWidget
from cgwidgets.utils import getJSONData
from .utils import getConstructors, getSaveData
from Utils2 import getFontSize

class PopupBarOrganizerTab(UI4.Tabs.BaseTab):
    NAME = "Popup Bar Designer"

    def __init__(self, parent=None):
        super(PopupBarOrganizerTab, self).__init__(parent)
        # EXAMPLE: Add additional constructors/save locations
        """
        # get additional constructors (widgets to be created)
        test_file_path = os.path.dirname(__file__) + "/etc/ExampleConstructors.json"
        katana_constructors = getConstructors(test_file_path)

        # create save location
        test_save_path = os.path.dirname(__file__) + '/etc/ExampleSaveLocation.json'
        test_save_data = {"Test": {
            "file_path": test_save_path,
            "locked": False}
        }
        save_data = getSaveData(test_save_data)
        """
        # get constructors
        widget_constructors = getConstructors()

        # get save directories
        sava_data = getSaveData()

        # create popup_bar widget
        self.main_widget = PopupBarOrganizerWidget(self, save_data=sava_data, widget_types=widget_constructors)

        # add PiPWidget to Katana tab
        QVBoxLayout(self)
        self.layout().addWidget(self.main_widget)

