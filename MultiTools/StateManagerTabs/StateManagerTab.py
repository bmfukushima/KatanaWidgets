"""
TODO
    GSVManager
        - View Scroll area
        - Auto update on creation of new GSVs / edit
"""

from qtpy.QtWidgets import QVBoxLayout, QWidget

from Katana import UI4

from cgwidgets.widgets import ShojiLayout, ShojiModelViewWidget, ModelViewWidget

from Widgets2 import AbstractStateManagerTab

from .GSVManagerTab import GSVViewWidget
from .IRFManagerTab import IRFActivationWidget as IRFViewWidget
from .BookmarkManagerTab import Tab as BookmarkViewWidget


class StateManagerTab(AbstractStateManagerTab):
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


class StateManagerEditorWidget(QWidget):
    def __init__(self, parent=None):
        super(StateManagerEditorWidget, self).__init__(parent)
        QVBoxLayout(self)
        from qtpy.QtWidgets import QLabel
        self.layout().addWidget(QLabel("test"))
        self._main_widget = ModelViewWidget(self)


class StateManagerViewWidget(ShojiLayout):
    def __init__(self, parent=None):
        super(StateManagerViewWidget, self).__init__(parent)
        self._main_layout = ShojiLayout(self)
        self._gsv_view = GSVViewWidget(self)
        self._irf_view = IRFViewWidget(self)
        self._bookmarks_view = BookmarkViewWidget(self)

        self._main_layout.addWidget(self._gsv_view)
        self._main_layout.addWidget(self._irf_view)
        self._main_layout.addWidget(self._bookmarks_view)
        self._main_layout.setSizes([100, 100, 100])

        # setup main layout
        QVBoxLayout(self)
        self.layout().addWidget(self._main_layout)

