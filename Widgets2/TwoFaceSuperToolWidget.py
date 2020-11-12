from qtpy.QtWidgets import (
    QWidget, QStackedWidget, QVBoxLayout, QLabel,
)

try:
    from Katana import UI4
except ModuleNotFoundError:
    pass
# local import... because PYTHONPATH is not registered yet
from .AbstractSuperToolEditor import AbstractSuperToolEditor

from cgwidgets.widgets import TansuModelViewWidget


class TwoFacedSuperToolWidget(AbstractSuperToolEditor):
    """
    This is the top level layout that encompasses all of the super tools
    in the which will have two faces, design, and use.  The design portion
    of the layout can have more faces as well ( custom tab ).  The design
    portion at a bare minimum should always have the tab for creating a GUI
    for the user.


    TwoFacedWidget
    VBox
        |-- QStackedWidget
        |       |-- ViewWidget ( QWidget )
                        User view widget
        |       |-- DesignWidget ( TansuModelViewWidget )
        |               |-- tab_content_layout ( StackedLayout )
        |                   |-- User Params ( Create GUI)
        |                   |-- Triggers ( Setup Signals )
        |                   |-- Node Edit ( Nodegraph / params )
        |-- Resizer

    TODO:
        *   Get toggle button into wrench icon
                --> Edit user parameters toggle?
        *   Wrench Icon | Publish/Edit modes?
                NodeActionDelegate.UpdateWrenchMenuWithDelegates(menu, node, hints)
    """
    def __init__(self, parent, node):
        super(TwoFacedSuperToolWidget, self).__init__(parent, node)

        # create main layout
        QVBoxLayout(self)

        # create stacked widget
        self.main_widget = QStackedWidget(self)
        self._design_widget = TansuModelViewWidget()
        self._design_widget.setObjectName('design widget')
        self._view_widget = TwoFacedViewWidget(self)
        self.main_widget.addWidget(self._design_widget)
        self.main_widget.addWidget(self._view_widget)

        # setup main layout
        resize_widget = UI4.Widgets.VBoxLayoutResizer(self)
        self.layout().addWidget(self.main_widget)
        self.layout().addWidget(resize_widget)

    """ PROPERTIES ( WIDGET )"""
    def getDesignWidget(self):
        return self._design_widget

    def setDesignWidget(self, design_widget):
        self._design_widget = design_widget

    def getViewWidget(self):
        return self._view_widget

    def setHeaderWidget(self, view_widget):
        self._view_widget = view_widget


class TwoFacedViewWidget(QWidget):
    """
    This is the main display for the user.  This should be dynamically populated
    from the UI created in the Design Widget
    """
    def __init__(self, parent=None):
        super(TwoFacedViewWidget, self).__init__(parent)
        QVBoxLayout(self)
        self.layout().addWidget(QLabel('View Widget'))

