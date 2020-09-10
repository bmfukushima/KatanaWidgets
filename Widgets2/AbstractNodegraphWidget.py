from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QEvent, Qt

from Katana import NodeGraphView, UI4, Utils


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

        # create node graph
        self.setTab(self.__createNodegraph())

        # setup nodegraph display
        #widget = self.getWidget()
        widget = self.getPanel()
        self.displayMenus(display_menus, widget)
        # self.setFocusPolicy(Qt.WheelFocus)
        # self.getWidget().setFocusPolicy(Qt.WheelFocus)
        # self.getTab().setFocusPolicy(Qt.WheelFocus)
        # self.getPanel().setFocusPolicy(Qt.WheelFocus)


    @staticmethod
    def __createNodegraph():
        """
        Creates the the nodegraph widget.

        Returns (NodegraphWidget)
        """
        tab_with_timeline = UI4.App.Tabs.CreateTab('Node Graph', None)
        nodegraph_tab = tab_with_timeline

        return nodegraph_tab

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

        if value is False:
            ngw_menu_bar = nodegraph_widget.getMenuBar()
            ngw_menu_bar.setParent(None)

            nodegraph_widget.layout().itemAt(0).widget().hide()

    def enableScrollWheel(self, enable):
        """
        Determines if the scroll wheel should be allowed.  This is good to turn off
        especially for parameters due to the double scrolling effect
        """
        self.getWidget()._NodegraphWidget__zoomLayer._ZoomInteractionLayer__allowMouseWheel = enable

    def goToNode(self, node):
        """
        Sets the node graph to view the children of the specified node
        """
        self.getPanel()._NodegraphPanel__navigationToolbarCallback(node.getName(), 'useless')

    """ SETUP NODEGRAPH DESTRUCTION HANDLER """
    def setupDestroyNodegraphEvent(self, widget_list=None):
        """
        Sets up all of the handlers for when the Nodegraph is destroyed.
        Don't necessarily want this during the hide/show event as that could
        a larger head ache than its worth.

        Args:
            widget_list (list): of widgets to install the destruction handler on
            enabled (bool): whether or not these should be turned on or not.
        """
        # node delete
        Utils.EventModule.RegisterCollapsedHandler(
            self.nodeDelete, 'node_delete', None
        )

        # new scene
        Utils.EventModule.RegisterCollapsedHandler(
            self.loadBegin, 'nodegraph_loadBegin', None
        )

        # additional widgets closed to destroy this...
        for widget in widget_list:
            widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        event_type = event.type()
        if event_type == QEvent.Close:
            self.destroyNodegraph()
            obj.removeEventFilter(self)
            return True

        return super(AbstractNodegraphWidget, self).eventFilter(obj, event)

    def nodeDelete(self, args):
        node = self.getNode()
        if node:
            if args[0][2]['node'] == node:
                self.destroyNodegraph()

    def loadBegin(self, args):
        self.destroyNodegraph()
        try:
            self.destroyNodegraph()
        except AttributeError:
            # on init this will suppress the logged message
            pass

    def destroyNodegraph(self):
        """
        Purges all metadata from the Nodegraph.  If you don't do this,
        holy warning messages batman!  But it doesn't crash ;).

        Essentially there is a private class attr on the Node Graph Widget called
        __nodegraphWidgetList which needs to have the nodegraph removed from it,
        or else it will let you know that its been destroyed
        """
        # get node graph widget
        nodegraph_widget = self.getWidget()

        # clean up
        NodeGraphView.CleanupModule(self)
        nodegraph_widget.cleanup()

    """ EVENTS """
    def closeEvent(self, event):
        self.destroyNodegraph()
        return QWidget.closeEvent(self, event)

    """ PROPERTIES """
    def setNode(self, node):
        self._node = node

    def getNode(self):
        return self._node

    def setPanel(self, nodegraph_panel):
        self._nodegraph_panel = nodegraph_panel

    def getPanel(self):
        return self._nodegraph_panel

    def setTab(self, nodegraph_tab):
        self.layout().addWidget(nodegraph_tab)
        self._nodegraph_tab = nodegraph_tab
        self.setPanel(nodegraph_tab.getWidget())
        self.setWidget(self.getPanel().getNodeGraphWidget())

    def getTab(self):
        return self._nodegraph_tab

    def setWidget(self, nodegraph_widget):
        self._nodegraph_widget = nodegraph_widget

    def getWidget(self):
        return self._nodegraph_widget


