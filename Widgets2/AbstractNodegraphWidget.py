from qtpy.QtWidgets import QWidget, QVBoxLayout, QApplication
from qtpy.QtCore import QEvent, Qt

try:
    from Katana import NodeGraphView, UI4, Utils
    from UI4.App import Tabs
except ModuleNotFoundError:
    pass


from cgwidgets.utils import getWidgetUnderCursor, getWidgetAncestorByObjectName


class AbstractNodegraphWidget(QWidget):
    """
    The abstract class for creating a stand alone Nodegraph.  This will need to
    have its event filter installed still to ensure that it is properly destroyed
    when the widget is closed.

    Default Katana nodegraph hierarchy ==>
        Tab with timeline --> Nodegraph Panel --> Nodegraph Widget
    Args:
        display_menus (bool): Determines if the main tabs menus should be hidden or not.

    Attributes:
        node (node): The node this is attached onto.  This is optional.
        panel (Nodegraph Panel): The panel the contains the nodegraph widget
        tab (tab with timeline): The parent of the nodegraph widget holding
            all of the menus and what not.
        widget (nodegraph widget): The actual nodegraph widget where users
            can manipulate nodes
    """

    def __init__(self, parent=None, display_menus=True, node=None):
        super(AbstractNodegraphWidget, self).__init__(parent)
        QVBoxLayout(self)

        # set up attrs
        self.setNode(node)
        self._is_scrolling = False

        # create node graph
        self._nodegraph_panel = self.createNodegraph()
        self._nodegraph_widget = self._nodegraph_panel.getNodeGraphWidget()
        self.layout().addWidget(self._nodegraph_panel)

        # setup nodegraph display
        panel = self.getPanel()

        self.panel_scroll_area = getWidgetAncestorByObjectName(self, "qt_scrollarea_viewport")

        # todo nodegraph destruction handlers
        # causes crash on NMC
        if self.panel_scroll_area:
            self.panel_scroll_area = self.panel_scroll_area.parent()

            # install event filters
            panel.installEventFilter(self)
            self.panel_scroll_area.viewport().installEventFilter(self)

        self.getWidget().installEventFilter(self)

        # display menus
        self.displayMenus(display_menus, panel)

    def createNodegraph(self):
        """
        Creates the the nodegraph widget.

        Returns (NodegraphWidget)
        """
        plugin = Tabs._LoadedTabPluginsByTabTypeName
        nodegraph_panel = plugin["Node Graph"].data(None)
        return nodegraph_panel

    @staticmethod
    def displayMenus(value, nodegraph_widget):
        """
        Determines if the main tabs menus should be hidden or not.

        Args:
            value (boolean): If False, this will return only the Nodegraph,
                if True, this will return the entire Nodegraph area.
            nodegraph_widget (NodegraphWidget.getPanel()):
                What widget to remove the menus from.  Note that this is not
                a widget in regard to this object, but the widget in regard to the
                Katana Nodegraph Object.
        """

        if value:
            ngw_menu_bar = nodegraph_widget.getMenuBar()
            ngw_menu_bar.show()

            nodegraph_widget.layout().itemAt(0).widget().show()

        if value is False:
            ngw_menu_bar = nodegraph_widget.getMenuBar()
            ngw_menu_bar.hide()

            nodegraph_widget.layout().itemAt(0).widget().hide()

    """ WHEEL EVENT OVERRIDES """
    def wheelEventFilter(self, obj, event):
        current_widget = getWidgetUnderCursor()
        if current_widget == self.getWidget():
            if event.type() == QEvent.Wheel:
                modifiers = event.modifiers()
                # block double scroll ( params panel event )
                if self.panel_scroll_area:
                    if obj == self.panel_scroll_area.viewport():
                        if modifiers == Qt.ControlModifier:
                            return False
                        return True

                # do scrolling ( Nodegraph event )
                if modifiers == Qt.ControlModifier:
                    self.enableScrollWheel(False)
                    return False
                else:
                    self.enableScrollWheel(True)
                    return False
                event.ignore()

    def enableScrollWheel(self, enable):
        """
        Determines if the scroll wheel should be allowed.  This is good to turn off
        especially for parameters due to the double scrolling effect
        """
        self._scroll_enabled = enable
        self.getWidget()._NodegraphWidget__zoomLayer._ZoomInteractionLayer__allowMouseWheel = enable

    def goToNode(self, node):
        """
        Sets the node graph to view the children of the specified node
        """
        self.getPanel()._NodegraphPanel__navigationToolbarCallback(node.getName(), 'useless')

    def eventFilter(self, obj, event):
        # wheel event
        should_return = self.wheelEventFilter(obj, event)
        if should_return: return True

        return False

    """ PROPERTIES """
    def setNode(self, node):
        self._node = node

    def getNode(self):
        return self._node

    def setPanel(self, nodegraph_panel):
        self._nodegraph_panel = nodegraph_panel

    def getPanel(self):
        return self._nodegraph_panel

    def setWidget(self, nodegraph_widget):
        self._nodegraph_widget = nodegraph_widget

    def getWidget(self):
        return self._nodegraph_widget


