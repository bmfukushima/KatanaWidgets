from qtpy.QtWidgets import QVBoxLayout

from Katana import UI4

from cgwidgets.utils import getJSONData
from cgwidgets.widgets import PiPWidget

from .utils import getConstructors, getSaveData


def createConstructor(save_data, widget_constructors, file_name, widget_name):
    """
    Creates the Tab constructor for Katana.
    Args:
        save_data (dict): JSON data of Save Directories
        widget_constructors (dict): JSON data of constructors for different widgets
            available in the PiPWidget
        file_name (str): name of file that this PiP Tab is stored in
        widget_name (str): name of PiP Widget

    Returns (QWidget): constructor to be used when Katana initializes a tab

    """

    class PiPDisplayTab(UI4.Tabs.BaseTab):
        FILE_NAME = file_name
        WIDGET_NAME = widget_name

        def __init__(self, parent=None, save_data=save_data, widget_types=widget_constructors):
            super(PiPDisplayTab, self).__init__(parent)

            # create PiP Widget
            self.main_widget = PiPWidget(widget_types=widget_types, save_data=save_data)
            self.main_widget.setDisplayWidget(PiPDisplayTab.FILE_NAME, PiPDisplayTab.WIDGET_NAME)
            self.main_widget.setCreationMode(PiPWidget.DISPLAY)

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
for file_name in save_data.keys():
    file_path = save_data[file_name]["file_path"]
    widget_data = getJSONData(file_path)

    # for each PiP Tab in the file
    for pip_widget_name in widget_data.keys():
        # setup pip tab data
        pip_tab_data = {}
        pip_tab_data["file_name"] = file_name
        pip_tab_data["widget_name"] = pip_widget_name
        pip_tab_data["constructor"] = createConstructor(save_data, widget_constructors, file_name, pip_widget_name)

        # append data to global tabs list
        pip_tabs.append(pip_tab_data)