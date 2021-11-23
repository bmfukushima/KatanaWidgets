from qtpy.QtWidgets import QVBoxLayout

from Katana import UI4

from cgwidgets.widgets import ShojiLayout

from .GSVManagerTab import GSVViewWidget
from .IRFManagerTab import IRFActivationWidget as IRFViewWidget
from .BookmarkManagerTab import Tab as BookmarkViewWidget


class StateManagerTab(UI4.Tabs.BaseTab):
    NAME = "State Manager"
    def __init__(self, parent=None):
        super(StateManagerTab, self).__init__(parent)
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

