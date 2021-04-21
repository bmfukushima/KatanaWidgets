import os

from Katana import UI4
from qtpy.QtWidgets import QVBoxLayout

from cgwidgets.widgets import PiPWidget
from cgwidgets.utils import getJSONData
from .utils import getConstructors, getSaveData

class PiPOrganizerTab(UI4.Tabs.BaseTab):
    NAME = "PiP Organizer"
    def __init__(self, parent=None):
        super(PiPOrganizerTab, self).__init__(parent)
        # EXAMPLE: Add additional constructors/save locations
        """
        # get Katana constructors
        test_file_path = os.path.dirname(__file__) + "/ExampleConstructors.json"
        katana_constructors = getConstructors(test_file_path)

        # get save data
        test_save_path = os.path.dirname(__file__) + '/.test.json'
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

        # create pip widget
        self.main_widget = PiPWidget(self, save_data=sava_data, widget_types=widget_constructors)

        # add PiPWidget to Katana tab
        QVBoxLayout(self)
        self.layout().addWidget(self.main_widget)

