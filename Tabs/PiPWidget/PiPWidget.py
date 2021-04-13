import os

from Katana import UI4
from qtpy.QtWidgets import QVBoxLayout

from cgwidgets.widgets import PiPWidget
from cgwidgets.utils import getJSONData


class PiPTab(UI4.Tabs.BaseTab):
    NAME = "PiPTab"
    def __init__(self, parent=None):
        super(PiPTab, self).__init__(parent)
        # get Katana PiP constructors
        constructors_file_path = os.path.dirname(__file__) + '/KatanaConstructors.json'
        katana_constructors = getJSONData(constructors_file_path)

        # create pip widget
        self.main_widget = PiPWidget(self, katana_constructors)

        # add PiPWidget to Katana tab
        QVBoxLayout(self)
        self.layout().addWidget(self.main_widget)