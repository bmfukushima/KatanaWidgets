import os

from Katana import UI4
from qtpy.QtWidgets import QVBoxLayout

from cgwidgets.widgets import PiPWidget
from cgwidgets.utils import getJSONData
from .utils import getConstructors

class PiPOrganizerTab(UI4.Tabs.BaseTab):
    NAME = "PiP Organizer"
    def __init__(self, parent=None):
        super(PiPOrganizerTab, self).__init__(parent)
        # get Katana PiP constructors
        # constructors_file_path = os.path.dirname(__file__) + '/KatanaConstructors.json'
        # katana_constructors = getJSONData(constructors_file_path)
        test_file_path = "/media/ssd01/dev/katana/KatanaWidgets/Tabs/PiPWidget/ExampleConstructors.json"
        katana_constructors = getConstructors(test_file_path)

        # setup katana save paths...
        # built ins
        built_ins_file_path = os.path.dirname(__file__) + '/.PiPWidgets.json'

        # user
        user_save_path = os.environ["HOME"] + '/.katana/.PiPWidgets.json'

        save_data = {
            "KatanaBebop": {
                "file_path": built_ins_file_path,
                "locked": False},
            "User": {
                "file_path": user_save_path,
                "locked": False}
        }
        # create pip widget
        self.main_widget = PiPWidget(self, save_data=save_data, widget_types=katana_constructors)

        # add PiPWidget to Katana tab
        QVBoxLayout(self)
        self.layout().addWidget(self.main_widget)

