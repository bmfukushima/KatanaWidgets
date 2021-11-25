"""
TODO
    *   Extract BookmarkManagerTab to abstraction layer
            - organizer
            - new state/folder
                New State Item
                New Folder Item
"""

from qtpy.QtWidgets import QVBoxLayout, QWidget

from Katana import UI4

from cgwidgets.widgets import ShojiLayout, ShojiModelViewWidget, ModelViewWidget, ButtonInputWidget

from Widgets2 import AbstractStateManagerTab

from .GSVManagerTab import GSVViewWidget
from .IRFManagerTab import IRFActivationWidget as IRFViewWidget
from .BookmarkManagerTab import Tab as BookmarkViewWidget


class StateManagerTab(UI4.Tabs.BaseTab):
    NAME = "State Manager"
    def __init__(self, parent=None):
        super(StateManagerTab, self).__init__(parent)

        # setup widgets
        self._view_widget = StateManagerViewWidget(self)
        self._editor_widget = StateManagerEditorWidget(self)

        # setup main layout
        QVBoxLayout(self)
        self._main_widget = ShojiModelViewWidget(self)
        self._main_widget.insertShojiWidget(0, column_data={"name":"View"}, widget=self._view_widget)
        self._main_widget.insertShojiWidget(1, column_data={"name":"Edit"}, widget=self._editor_widget)

        self.layout().addWidget(self._main_widget)

    """ WIDGETS """
    def mainWidget(self):
        return self._main_widget

    def viewWidget(self):
        return self._view_widget

    def editorWidget(self):
        return self._editor_widget


class StateManagerOrganizerWidget(ModelViewWidget):
    def __init__(self, parent=None):
        super(StateManagerOrganizerWidget, self).__init__(parent)


class StateManagerEditorWidget(AbstractStateManagerTab):
    def __init__(self, parent=None):
        super(StateManagerEditorWidget, self).__init__(parent)

        # setup organizer
        self._state_organizer_widget = StateManagerOrganizerWidget(self)
        self.setOrganizerWidget(self._state_organizer_widget)

        # setup events
        self._create_new_state_widget = ButtonInputWidget(
            title="New State", user_clicked_event=self.createNewState)
        self._create_new_folder_widget = ButtonInputWidget(
            title="New Folder", user_clicked_event=self.createNewFolder)

        self.addUtilsButton(self._create_new_state_widget)
        self.addUtilsButton(self._create_new_folder_widget)


    def createNewState(self, widget):
        print('create new state')
        pass

    def createNewFolder(self, widget):
        print('create new folder')
        pass


class StateManagerViewWidget(ShojiLayout):
    def __init__(self, parent=None):
        super(StateManagerViewWidget, self).__init__(parent)
        self._main_layout = ShojiLayout(self)
        self._gsv_view = GSVViewWidget(self)
        self._irf_view = IRFViewWidget(self)
        self._bookmarks_view = BookmarkViewWidget(self)
        self._state_view = StateManagerEditorWidget(self)

        self._main_layout.addWidget(self._state_view)
        self._main_layout.addWidget(self._gsv_view)
        self._main_layout.addWidget(self._irf_view)
        self._main_layout.addWidget(self._bookmarks_view)
        self._main_layout.setSizes([100, 100, 100, 100])

        # setup main layout
        QVBoxLayout(self)
        self.layout().addWidget(self._main_layout)

