import os
import json

from qtpy.QtWidgets import QVBoxLayout

from Katana import UI4

from cgwidgets.utils import getJSONData
from cgwidgets.widgets import PopupBarDisplayWidget

from .utils import getConstructors, getSaveData


def createConstructor(filepath, popup_bar_widget_name):
    """
    Creates the Tab constructor for Katana.

    Args:
        save_data (dict): JSON data of Save Directories
        widget_constructors (dict): JSON data of constructors for different widgets
            available in the PiPWidget
        filepath (str): name of file that this PiP Tab is stored in
        popup_bar_widget_name (str): name of PiP Widget

    Returns (QWidget): constructor to be used when Katana initializes a tab

    """

    class PopupBarDisplayTab(UI4.Tabs.BaseTab):
        FILEPATH = filepath
        PIP_WIDGET_NAME = popup_bar_widget_name
        _is_popup_widget = True

        def __init__(self, parent=None):
            super(PopupBarDisplayTab, self).__init__(parent)

            # create PiP Widget
            self._popup_bar_display_widget = PopupBarDisplayWidget()
            self._popup_bar_display_widget.loadPopupDisplayFromFile(PopupBarDisplayTab.FILEPATH, PopupBarDisplayTab.PIP_WIDGET_NAME)

            # create main layout
            QVBoxLayout(self)
            self.layout().addWidget(self._popup_bar_display_widget)

        def popupBarDisplayWidget(self):
            return self._popup_bar_display_widget

        def popupBarWidget(self):
            return self.popupBarDisplayWidget().popupBarWidget()

        def widgets(self):
            return self.popupBarDisplayWidget().widgets()

        def enlargedWidget(self):
            return self.popupBarWidget().enlargedWidget()

        def isEnlarged(self):
            return self.popupBarWidget().isEnlarged()

        def displayMode(self):
            return self.popupBarWidget().displayMode()

        def closeEnlargedView(self):
            self.popupBarWidget().closeEnlargedView()

    return PopupBarDisplayTab


# get Katana PiP constructors
widget_constructors = getConstructors()

# get save data
save_data = getSaveData()

popup_bar_tabs = []

# for each PiP Save File
for filename in save_data.keys():
    filepath = save_data[filename]["file_path"]
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump({}, f)
    widget_data = getJSONData(filepath)

    # for each PiP Tab in the file
    for popup_bar_widget_name in widget_data.keys():
        # setup popup_bar tab data
        popup_bar_tab_data = {}
        popup_bar_tab_data["filepath"] = filepath
        popup_bar_tab_data["filename"] = filename
        popup_bar_tab_data["popup_bar_widget_name"] = popup_bar_widget_name
        popup_bar_tab_data["constructor"] = createConstructor(filepath, popup_bar_widget_name)

        # append data to global tabs list
        popup_bar_tabs.append(popup_bar_tab_data)