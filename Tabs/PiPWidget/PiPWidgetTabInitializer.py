import os

from qtpy.QtWidgets import QVBoxLayout

from Katana import UI4

from cgwidgets.utils import getJSONData
from cgwidgets.widgets import PiPWidget

from .utils import getConstructors, getSaveData

# # built ins
# built_ins_file_path = os.path.dirname(__file__) + '/.PiPWidgets.json'
#
# # user
# user_save_path = os.environ["HOME"] + '/.katana/.PiPWidgets.json'
#
# save_data = {
#     "KatanaBebop": {
#         "file_path": built_ins_file_path,
#         "locked": False},
#     "User": {
#         "file_path": user_save_path,
#         "locked": False}
# }
# get Katana PiP constructors
widget_constructors = getConstructors()

# get save data
save_data = getSaveData()

pip_tabs = []

for file_name in save_data.keys():
    file_path = save_data[file_name]["file_path"]
    widget_data = getJSONData(file_path)
    for pip_widget_name in widget_data.keys():
        pip_tab_data = {}

        pip_tab_data["file_name"] = file_name
        pip_tab_data["widget_name"] = pip_widget_name

        def createConstructor(save_data, widget_constructors, file_name, widget_name):
            """
            Creates the Tab constructor for Katana.
            Args:
                save_data (dict): JSON data of Save Directories
                widget_constructors (dict): JSON data of constructors for different widgets
                    available in the PiPWidget
                file_name (str): name of file that this PiP Tab is stored in
                widget_name (str): name of PiP Widget

            Returns (QWidget): to be constructed when Katana initializes a tab

            """
            class PiPDisplayTab(UI4.Tabs.BaseTab):
                FILE_NAME = file_name
                WIDGET_NAME = widget_name
                def __init__(self, parent=None, save_data=save_data, widget_types=widget_constructors):
                    super(PiPDisplayTab, self).__init__(parent)
                    QVBoxLayout(self)
                    self.main_widget = PiPWidget(widget_types=widget_types, save_data=save_data)
                    self.layout().addWidget(self.main_widget)

                    self.main_widget.setDisplayWidget(PiPDisplayTab.FILE_NAME, PiPDisplayTab.WIDGET_NAME)
                    self.main_widget.setCreationMode(PiPWidget.DISPLAY)

            constructor = PiPDisplayTab
            return constructor

        pip_tab_data["constructor"] = createConstructor(save_data, widget_constructors, file_name, pip_widget_name)
        pip_tabs.append(pip_tab_data)