"""
SuperToolFormWidget
--> NodeGroupFormWidget
--> HideTitleGroupFormWidget
--> QT4FormWidgets.GroupFormWidget
--> QT4FormWidgets.FormWidget
--> QtWidget
"""

from qtpy.QtWidgets import (QWidget, QVBoxLayout)
from qtpy.QtCore import Qt, QEvent

try:
    from Katana import UI4, Utils
except ModuleNotFoundError:
    pass
# local import... because PYTHONPATH is not registered yet
from .AbstractSuperToolEditor import AbstractSuperToolEditor

from cgwidgets.widgets import ShojiModelViewWidget
from cgwidgets.utils import getWidgetAncestor

from Utils2 import paramutils


class TwoFacedSuperToolWidget(AbstractSuperToolEditor):
    """
    This is the top level layout that encompasses all of the super tools
    in the which will have two faces, design, and use.  The design portion
    of the layout can have more faces as well ( custom tab ).  The design
    portion at a bare minimum should always have the tab for creating a GUI
    for the user.


    TwoFacedWidget
    VBox
        |-- DesignWidget ( ShojiModelViewWidget )
        |       |-- tab_content_layout ( StackedLayout )
        |           |-- User Params ( Create GUI)
        |           |-- Triggers ( Setup Signals )
        |           |-- Node Edit ( Nodegraph / params )
        |-- Resizer

    TODO:
        *   Get toggle button into wrench icon
                --> Edit user parameters toggle?
        *   Wrench Icon | Publish/Edit modes?
                NodeActionDelegate.UpdateWrenchMenuWithDelegates(menu, node, hints)
        *   View widget doesn't exist anymore?
    """
    DESIGN = 0
    VIEW = 1

    def __init__(self, parent, node):
        super(TwoFacedSuperToolWidget, self).__init__(parent, node)
        # create main layout
        QVBoxLayout(self)
        self.layout().setAlignment(Qt.AlignTop)

        self._design_widget = ShojiModelViewWidget()
        self._design_widget.setObjectName('design widget')
        self.layout().addWidget(self._design_widget)

        # setup resize handlers
        self.insertResizeBar()
        self.removeResizeEventFilter()

        form_widget = TwoFacedSuperToolWidget.getFormWidget(self)
        form_widget.installEventFilter(self)

        self._user_params_widget = UserParametersWidget(self)
        self.designWidget().insertShojiWidget(
            0, column_data={'name':"Params (User)"}, widget=self.userParametersWidget())

    def showEvent(self, event):
        # blocks the show event of the TwoFacedSuperToolWidget if the user params are active
        selection = self.designWidget().getAllSelectedItems()
        if 0 < len(selection):
            if selection[0].name() == "Params (User)" and self.displayMode() == TwoFacedSuperToolWidget.DESIGN:
                return

        self.setDisplayMode(self.displayMode())

        # update layout
        form_widget = TwoFacedSuperToolWidget.getFormWidget(self)

        popdownWidget = form_widget.getPopdownWidget()
        popdownWidget.layout().setAlignment(Qt.AlignTop)

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

            # special handler for Params (User)
            selection = self.designWidget().getAllSelectedItems()
            if 0 < len(selection):
                if selection[0].name() == "Params (User)":
                    self.removeResizeEventFilter()
                    self.designWidget().show()
                    self.designWidget().delegateScrollArea().hide()
                    self.resizeBarWidget().hide()
                    self.setFixedHeight(self.designWidget().header_height)
                    return

            # set design view
            self.installResizeEventFilter()
            self.designWidget().show()
            self.resizeBarWidget().show()
            self.designWidget().setHeaderWidgetToDefaultSize()
        elif display_mode == TwoFacedSuperToolWidget.VIEW:
            self.setFixedHeight(1)
            self.removeResizeEventFilter()
            self.designWidget().hide()
            self.resizeBarWidget().hide()

    """ UTILS """
    @staticmethod
    def getFormWidget(widget):
        """ Gets the FormWidget, which is the container widget that holds the parameter
        title, options, etc

        Args:
            widget (QWidget): to start recursively searching from

        Returns (SuperToolFormWidget)"""
        from UI4.FormMaster.Editors import NodeGroup
        return getWidgetAncestor(widget, NodeGroup.SuperToolFormWidget)

    """ WIDGETS """
    def userParametersWidget(self):
        return self._user_params_widget

    def designWidget(self):
        return self._design_widget

    def setDesignWidget(self, design_widget):
        self._design_widget = design_widget

    def eventFilter(self, obj, event):
        """ Updates the headers width on resize so that they always stay in alignment"""
        if event.type() == QEvent.Resize:
            selection = self.designWidget().getAllSelectedItems()
            if 0 < len(selection):
                if selection[0].name() == "Params (User)":
                    # get attrs
                    viewport = AbstractSuperToolEditor.getKatanaQtScrollAreaViewport(self)
                    scrollarea = viewport.parent()
                    vertical_scrollbar = scrollarea.verticalScrollBar()

                    # get dimensions
                    margins = 5
                    width = viewport.width() - margins
                    if vertical_scrollbar.isVisible():
                        width -= vertical_scrollbar.width()

                    # set size
                    self.setFixedWidth(width)

        return False

class UserParametersWidget(QWidget):
    def __init__(self, parent=None):
        super(UserParametersWidget, self).__init__(parent)
        QVBoxLayout(self)
        # two_faced_supertool_widget = getWidgetAncestor(self, TwoFacedSuperToolWidget)
        #paramutils.createParamAtLocation("user", two_faced_supertool_widget.node(), paramutils.GROUP)
        #user_param = two_faced_supertool_widget.createKatanaParam("user")
        #self.layout().addWidget(user_param)

    """ EVENTS """
    def showEvent(self, event):
        self._is_frozen = True

        # hide design area and leave header
        two_faced_supertool_widget = getWidgetAncestor(self, TwoFacedSuperToolWidget)
        two_faced_supertool_widget.removeResizeEventFilter()
        #two_faced_supertool_widget.installEventFilter(self)

        two_faced_supertool_widget.setFixedHeight(two_faced_supertool_widget.designWidget().header_height)
        two_faced_supertool_widget.designWidget().delegateScrollArea().hide()
        two_faced_supertool_widget.resizeBarWidget().hide()

        # override width
        form_widget = TwoFacedSuperToolWidget.getFormWidget(self)
        form_widget.setMinimumWidth(10)
        form_widget.setMaximumWidth(2000)

        self._is_frozen = False

        return QWidget.showEvent(self, event)

    def hideEvent(self, event):
        if not self._is_frozen:
            two_faced_supertool_widget = getWidgetAncestor(self, TwoFacedSuperToolWidget)
            two_faced_supertool_widget.installResizeEventFilter()
            #two_faced_supertool_widget.removeEventFilter(self)

            two_faced_supertool_widget.designWidget().delegateScrollArea().show()
            two_faced_supertool_widget.resizeBarWidget().show()
            two_faced_supertool_widget.designWidget().setHeaderWidgetToDefaultSize()

        return QWidget.hideEvent(self, event)
    #
    # def eventFilter(self, obj, event):
    #     from qtpy.QtCore import QEvent
    #     if event.type() == QEvent.Resize:
    #         """
    #         Updates the size of the GUI to match that of the parameters pane...
    #         no more of these random af scroll bars everywhere.
    #
    #         # todo automatic size updates
    #         # horizontal scrollbar disabled in __init__
    #         # need to track all of these down... hard coded right now
    #             height =
    #                 hscrollbar.height()
    #                 + margins.top()
    #                 + margins.bottom()
    #                 + frame.height()
    #             width =
    #                 vscrollbar.width()
    #                 + margins.left()
    #                 + margins.right()
    #         """
    #
    #         # get attrs
    #         viewport = AbstractSuperToolEditor.getKatanaQtScrollAreaViewport(self)
    #         scrollarea = viewport.parent()
    #         vertical_scrollbar = scrollarea.verticalScrollBar()
    #
    #         # get dimensions
    #         margins = 5
    #         width = viewport.width() - margins
    #         if vertical_scrollbar.isVisible():
    #             width -= vertical_scrollbar.width()
    #         #
    #         # if horizontal_scrollbar.isVisible():
    #         #     height -= horizontal_scrollbar.height()
    #
    #         # set size
    #         self.setFixedWidth(width)
    #         print('setting width to ', width)
    #
    #     return False