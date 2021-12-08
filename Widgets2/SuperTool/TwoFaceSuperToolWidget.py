from qtpy.QtWidgets import (QWidget, QStackedWidget, QVBoxLayout, QLabel, QStackedLayout)

try:
    from Katana import UI4
except ModuleNotFoundError:
    pass
# local import... because PYTHONPATH is not registered yet
from .AbstractSuperToolEditor import AbstractSuperToolEditor

from cgwidgets.widgets import ShojiModelViewWidget
from cgwidgets.utils import getWidgetAncestor


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
        # create main layout
        QVBoxLayout(self)
        self._design_widget = ShojiModelViewWidget()
        self._design_widget.setObjectName('design widget')
        self.layout().addWidget(self._design_widget)

        # setup resize handlers
        self.insertResizeBar()
        self.removeResizeEventFilter()

        self._user_params_widget = UserParametersWidget(self)
        self.getDesignWidget().insertShojiWidget(
            0, column_data={'name':"Params (User)"}, widget=self.userParametersWidget())

    def showEvent(self, event):
        self.setDisplayMode(self.displayMode())
        return AbstractSuperToolEditor.showEvent(self, event)

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
        if display_mode == TwoFacedSuperToolWidget.DESIGN:
            self.getDesignWidget().show()
            self.installResizeEventFilter()
            self.resizeBarWidget().show()
            self.getDesignWidget().setHeaderWidgetToDefaultSize()
        elif display_mode == TwoFacedSuperToolWidget.VIEW:
            self.setFixedHeight(1)
            self.removeResizeEventFilter()
            self.getDesignWidget().hide()
            self.resizeBarWidget().hide()

    """ WIDGETS """
    def userParametersWidget(self):
        return self._user_params_widget

    def getDesignWidget(self):
        return self._design_widget

    def setDesignWidget(self, design_widget):
        self._design_widget = design_widget

    def getViewWidget(self):
        return self._view_widget

    def setHeaderViewWidget(self, view_widget):
        self._view_widget = view_widget


class UserParametersWidget(QWidget):
    def __init__(self, parent=None):
        super(UserParametersWidget, self).__init__(parent)

    """ EVENTS """
    #TODO: copy paste from TwoFacedSuperToolWidget.setDisplayMode
    def showEvent(self, event):
        two_faced_supertool_widget = getWidgetAncestor(self, TwoFacedSuperToolWidget)
        two_faced_supertool_widget.setFixedHeight(1)
        two_faced_supertool_widget.removeResizeEventFilter()
        two_faced_supertool_widget.resizeBarWidget().hide()

        return QWidget.showEvent(self, event)

    def hideEvent(self, event):
        two_faced_supertool_widget = getWidgetAncestor(self, TwoFacedSuperToolWidget)
        two_faced_supertool_widget.installResizeEventFilter()
        two_faced_supertool_widget.resizeBarWidget().show()
        two_faced_supertool_widget.getDesignWidget().setHeaderWidgetToDefaultSize()
        return QWidget.hideEvent(self, event)