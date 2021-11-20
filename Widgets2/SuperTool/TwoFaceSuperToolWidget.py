from qtpy.QtWidgets import (QWidget, QStackedWidget, QVBoxLayout, QLabel, QStackedLayout)

try:
    from Katana import UI4
except ModuleNotFoundError:
    pass
# local import... because PYTHONPATH is not registered yet
from .AbstractSuperToolEditor import AbstractSuperToolEditor

from cgwidgets.widgets import ShojiModelViewWidget


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
        |       |-- DesignWidget ( ShojiModelViewWidget )
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
    DESIGN = 0
    VIEW = 1

    def __init__(self, parent, node):
        super(TwoFacedSuperToolWidget, self).__init__(parent, node)
        print('init')
        # create main layout
        QStackedLayout(self)
        self.layout().setStackingMode(QStackedLayout.StackOne)
        # create stacked widget
        self._design_widget = ShojiModelViewWidget()
        self._design_widget.setObjectName('design widget')
        self._view_widget = TwoFacedViewWidget(self)
        self.layout().addWidget(self._design_widget)
        self.layout().addWidget(self._view_widget)

        # setup main layout
        self.insertResizeBar()
        print('init')

    def showEvent(self, event):
        return_val = AbstractSuperToolEditor.showEvent(self, event)
        self.setDisplayMode(self.displayMode())
        return return_val

    """ PROPERTIES """
    def displayMode(self):
        return self.node().getParameter("display_mode").getValue(0)

    def setDisplayMode(self, display_mode):
        """ Sets how this widget should be displayed

        Note:
            Doing some really janky stuff here with the hide/show due to widgets
            overlapping during the show event.  

        Args:
            display_mode (TwoFacedSuperToolWidget.DISPLAYMODE): int value
                DESIGN | VIEW
        """
        self.node().getParameter("display_mode").setValue(display_mode, 0)
        self.layout().setCurrentIndex(display_mode)
        if display_mode == TwoFacedSuperToolWidget.DESIGN:
            self.resizeBarWidget().show()
            self.getViewWidget().hide()
            self.getDesignWidget().show()
        elif display_mode == TwoFacedSuperToolWidget.VIEW:
            self.getViewWidget().show()
            self.getDesignWidget().hide()
            self.resizeBarWidget().hide()
        else:
            self.getViewWidget().show()
            self.getDesignWidget().hide()
            self.resizeBarWidget().hide()

    def getDesignWidget(self):
        return self._design_widget

    def setDesignWidget(self, design_widget):
        self._design_widget = design_widget

    def getViewWidget(self):
        return self._view_widget

    def setHeaderViewWidget(self, view_widget):
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

