import os
from cgwidgets.utils import getJSONData
from cgwidgets.widgets import PiPWidget

from .utils import getConstructors

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
# # get Katana PiP constructors
# constructors_file_path = os.path.dirname(__file__) + '/KatanaConstructors.json'
# katana_constructors = getJSONData(constructors_file_path)
katana_constructors = getConstructors()
#print(katana_constructors)
pip_tabs = []

for file_name in save_data.keys():
    file_path = save_data[file_name]["file_path"]
    widget_data = getJSONData(file_path)
    for pip_widget_name in widget_data.keys():
        pip_tab_data = {}

        pip_tab_data["file_name"] = file_name
        pip_tab_data["widget_name"] = pip_widget_name

        def createConstructor(save_data, katana_constructors, file_name, widget_name):
            """
            Creates the Tab constructor for Katana.
            Args:
                save_data (dict):
                katana_constructors (dict):
                file_name (str):
                widget_name (str):

            Returns (QWidget): to be constructed when Katana initializes a tab

            """
            class PiPDisplayTab(PiPWidget):
                FILE_NAME = file_name
                WIDGET_NAME = widget_name
                def __init__(self, parent=None, save_data=save_data, widget_types=katana_constructors):
                    super(PiPDisplayTab, self).__init__(parent=parent, save_data=save_data, widget_types=widget_types)

                    self.setDisplayWidget(PiPDisplayTab.FILE_NAME, PiPDisplayTab.WIDGET_NAME)
                    self.setCreationMode(PiPWidget.DISPLAY)

            constructor = PiPDisplayTab
            return constructor

        # how to dynamically create constructor?
        pip_tab_data["constructor"] = createConstructor(save_data, katana_constructors, file_name, pip_widget_name)

        pip_tabs.append(pip_tab_data)
        print('creating... ', pip_tab_data)