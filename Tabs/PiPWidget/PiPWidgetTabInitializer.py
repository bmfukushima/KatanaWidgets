from qtpy.QtWidgets import QVBoxLayout

from Katana import UI4

from cgwidgets.utils import getJSONData
from cgwidgets.widgets import PiPOrganizerWidget, PiPDisplayWidget

from .utils import getConstructors, getSaveData


def createConstructor(filepath, pip_widget_name):
    """
    Creates the Tab constructor for Katana.
    Args:
        save_data (dict): JSON data of Save Directories
        widget_constructors (dict): JSON data of constructors for different widgets
            available in the PiPWidget
        filepath (str): name of file that this PiP Tab is stored in
        pip_widget_name (str): name of PiP Widget

    Returns (QWidget): constructor to be used when Katana initializes a tab

    """

    class PiPDisplayTab(UI4.Tabs.BaseTab):
        FILEPATH = filepath
        PIP_WIDGET_NAME = pip_widget_name

        def __init__(self, parent=None):
            super(PiPDisplayTab, self).__init__(parent)

            # create PiP Widget
            self.main_widget = PiPDisplayWidget()
            self.main_widget.loadPiPWidgetFromFile(PiPDisplayTab.FILEPATH, PiPDisplayTab.PIP_WIDGET_NAME)

            #self.main_widget.setDisplayWidget(PiPDisplayTab.FILE_NAME, PiPDisplayTab.WIDGET_NAME)
            #self.main_widget.setCreationMode(PiPOrganizerWidget.DISPLAY)

            # create main layout
            QVBoxLayout(self)
            self.layout().addWidget(self.main_widget)

    return PiPDisplayTab


# get Katana PiP constructors
widget_constructors = getConstructors()

# get save data
save_data = getSaveData()

pip_tabs = []

# for each PiP Save File
for filename in save_data.keys():
    filepath = save_data[filename]["file_path"]
    widget_data = getJSONData(filepath)

    # for each PiP Tab in the file
    for pip_widget_name in widget_data.keys():
        # setup pip tab data
        pip_tab_data = {}
        pip_tab_data["filepath"] = filepath
        pip_tab_data["filename"] = filename
        pip_tab_data["pip_widget_name"] = pip_widget_name
        pip_tab_data["constructor"] = createConstructor(filepath, pip_widget_name)

        # append data to global tabs list
        pip_tabs.append(pip_tab_data)