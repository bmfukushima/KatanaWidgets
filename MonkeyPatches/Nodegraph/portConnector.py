""" This is an evolution of the "~" key connection in Katana.
This is actived with the Alt+~ and will do a few things:
    No active port selection:
        1 ) Find the nearest node
        2a) If there is only one output port, select it
        2b) If there are multiple output ports, popup a display to the user to select an output port
    If there is an active port selection:
        1 ) Find nearest node
        2a) If there is only one input port, unconnected, connect it
        2b) If there is only one input port, and it is connected, prompt the user to override the connection
        2c) If there are multiple input ports, prompt the user to select an input port to connect to.  If the user
                selects a port that has a connection, prompt the user to override the connection.

Alt: Recursive selection
Ctrl: Hide warning
TODO
    *   Override for port types
    *   Network Material Create
    *   Multi port connection
            Output Port
                Select all Connections
                Reconnect to another output port
            Input Port
                Select all connections
                Reconnect to another node
            Shift
                Add to link selection
            Smarter detection when links are selected

"""
from qtpy.QtWidgets import QFrame, QVBoxLayout, QLabel, QApplication
from qtpy.QtCore import Qt

from Katana import Utils, QT4Widgets, QT4GLLayerStack, NodegraphAPI, DrawingModule, ResourceFiles, KatanaPrefs, logging, PrefNames, UI4
from UI4.Tabs.NodeGraphTab.Layers.LinkConnectionLayer import LinkConnectionLayer

from cgwidgets.widgets import ButtonInputWidgetContainer, ButtonInputWidget, FrameInputWidgetContainer
from cgwidgets.utils import centerWidgetOnCursor, setAsBorderless, setAsTransparent, getWidgetUnderCursor, isCursorOverWidget
from Utils2 import nodeutils, portutils, getFontSize, nodegraphutils
from Utils2.widgetutils import katanaMainWindow


OUTPUT_PORT = 0
INPUT_PORT = 1


class OverridePortWarningButtonPopupWidget(QFrame):
    def __init__(self, node, connection_port, selected_ports, is_recursive_selection=False, parent=None):
        super(OverridePortWarningButtonPopupWidget, self).__init__(parent)
        # setup attrs

        self._selected_ports = selected_ports

        # setup layout
        QVBoxLayout(self)
        self._button_widget = OverridePortWarningButtonWidget(node, connection_port, selected_ports, is_recursive_selection=is_recursive_selection)
        self.layout().addWidget(self._button_widget)

        # setup display
        setAsBorderless(self)
        # self.setContentsMargins(10, 10, 10, 10)
        self.setStyleSheet("""QFrame{border: 1px solid rgba(128,128,255,255); margin: 2px}""")
        if not PortConnector.isSelectionActive():
            PortConnector.showNoodle(selected_ports)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            # PortConnector.showNoodle(self._selected_ports)
            self.close()
        if event.key() == 96:
            self._button_widget.connectPortsEvent()
        ButtonInputWidget.keyPressEvent(self, event)

    def closeEvent(self, event):
        katanaMainWindow().activateWindow()
        ButtonInputWidget.closeEvent(self, event)

    def leaveEvent(self, event):
        if not isCursorOverWidget(self):
            self.close()
        return ButtonInputWidget.leaveEvent(self, event)


class OverridePortWarningButtonWidget(ButtonInputWidget):
    """ Popup displayed to the user when they attempt to connect a port that already has a connection

    Args:
        node (node):
        input_port (port):
        selected_ports (port):

    Attributes:
        show_noodle (bool): determines if the noodle should be shown on exit
        input_port (port):
        output_port (port)
    """
    def __init__(self, node, connection_port, selected_ports, is_recursive_selection=False, parent=None):
        super(OverridePortWarningButtonWidget, self).__init__(parent=parent)

        # setup attrs
        self._is_recursive_selection = is_recursive_selection
        self._connection_port = connection_port
        self._selected_ports = selected_ports
        self._show_noodle = False
        self._node = node
        self.setIsToggleable(False)

        # setup display
        self.setText("-- OVERRIDE CONNECTION -- \n {node} | {port}".format(node=node.getName(), port=self._connection_port.getName()))
        self.setFixedHeight(getFontSize() * 5)
        setAsBorderless(self)

        # setup events
        self.setUserClickedEvent(self.connectPortsEvent)

    def node(self):
        return self._node

    def connectPortsEvent(self, *args):
        for selected_port in self._selected_ports:
            self._connection_port.connect(selected_port)
        PortConnector.hideNoodle()

        if self._is_recursive_selection:
            self.parent().hide()
            QApplication.processEvents()
            katanaMainWindow().activateWindow()
            katanaMainWindow().setFocus()
            PortConnector.actuateSelection(
                PortConnector.activeNodegraphWidget(), node=self.node(), port_type=self._selected_ports[0].getType())

        self.parent().close()


class MultiPortPopupMenuWidget(FrameInputWidgetContainer):
    def __init__(self, node, port_type=OUTPUT_PORT, selected_ports=None, display_warning=True, is_selection_active=None, is_recursive_selection=False, parent=None):
        super(MultiPortPopupMenuWidget, self).__init__(parent)
        # setup attrs
        self._node = node
        #self._show_noodle = False
        self._selected_ports = selected_ports
        self.setTitle(node.getName())
        self.setIsHeaderEditable(False)
        self.setDirection(Qt.Vertical)

        # create widgets
        self._title_widget = QLabel(node.getName())
        self._title_widget.setAlignment(Qt.AlignCenter)
        self._ports_widget = MultiPortPopupMenu(
            node,
            port_type=port_type,
            selected_ports=selected_ports,
            display_warning=display_warning,
            is_selection_active=is_selection_active,
            is_recursive_selection=is_recursive_selection,
            parent=self
        )
        self.addInputWidget(self._ports_widget)

        # setup display
        nodeutils.setGlowColor(node, (0.5, 0.5, 1))
        setAsBorderless(self)
        setAsTransparent(self._ports_widget)
        self.setStyleSheet("""QFrame{border: 1px solid rgba(128,128,255,255); margin: 2px}""")
        self.setContentsMargins(2, 2, 2, 2)

        # show noodle
        if is_selection_active:
            if not PortConnector.isSelectionActive():
                for port in selected_ports:
                    PortConnector.showNoodle(port)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._show_noodle = True
            self.close()

        QFrame.keyPressEvent(self, event)

    def closeEvent(self, event):
        katanaMainWindow().activateWindow()
        nodeutils.setGlowColor(self._node, None)
        QFrame.closeEvent(self, event)

    def leaveEvent(self, event):
        QFrame.leaveEvent(self, event)
        self.close()

    def showEvent(self, event):
        return_val = QFrame.showEvent(self, event)
        if self.width() < 200:
            self.setFixedWidth(200)

        return return_val


class MultiPortPopupMenu(ButtonInputWidgetContainer):
    """ Popup widget displayed when the user queries a node with multiple inputs

    This will show the user a list of all of the available ports to be selected.
    If no port is currently selected, this will activate a port selection, if one is
    currently selected, then this will connect the ports.

    Args:
        node (node): node
        ports (list): of ports
        port_type (PORT_TYPE): the type of ports that will be displayed to the user
        is_selection_active (bool): Determines if there are links currently selected
        selected_ports (port): port currently selected

    """
    def __init__(self, node, port_type=OUTPUT_PORT, is_selection_active=None, selected_ports=None, display_warning=True, is_recursive_selection=False, parent=None):
        super(MultiPortPopupMenu, self).__init__(parent, Qt.Vertical)

        # setup attrs
        self._node = node
        self._is_recursive_selection = is_recursive_selection
        self._port_type = port_type
        self._is_selection_active = is_selection_active
        self._selected_ports = selected_ports
        self._display_warning = display_warning
        self.setIsToggleable(False)

        for port in self.getDisplayPorts():
            self.addButton(port.getName(), port.getName(), self.portSelectedEvent)

        if port_type == INPUT_PORT:
            if node.getType() in nodegraphutils.dynamicInputPortNodes():
                self.addButton("< New >", "< New >", self.createNewPortEvent)

    """ PROPERTIES """
    def node(self):
        return self._node

    """ EVENTS """
    def portSelectedEvent(self, widget):
        """ Event run when the user selects a port"""
        port = self.getSelectedPort(widget.flag())
        # connect selected ports
        if self._is_selection_active:
            is_connected = portutils.isPortConnected(port)

            # port selected is connected, display display_warning
            if is_connected and self._display_warning:
                katanaMainWindow()._display_warning_widget = OverridePortWarningButtonPopupWidget(self._node, port, self._selected_ports, is_recursive_selection=self._is_recursive_selection)
                katanaMainWindow()._display_warning_widget.show()
                centerWidgetOnCursor(katanaMainWindow()._display_warning_widget, raise_=True)

            # port selected has no connections, connect port
            else:
                for selected_port in self._selected_ports:
                    selected_port.connect(port)
                PortConnector.hideNoodle()

                # recursive multi port selection
                if self._is_recursive_selection:
                    self.parent().hide()
                    QApplication.processEvents()
                    katanaMainWindow().activateWindow()
                    katanaMainWindow().setFocus()
                    PortConnector.actuateSelection(PortConnector.activeNodegraphWidget(), node=self.node(), port_type=self._selected_ports[0].getType())
                    return
                    # return

        # show noodle
        elif self._is_selection_active == OUTPUT_PORT:
            PortConnector.showNoodle(port)

        # self.parent()._show_noodle = False
        self.parent().close()

    def createNewPortEvent(self, widget):
        num_ports = len(self.node().getInputPorts())
        port = self.node().addInputPort(f"i{num_ports}")
        for selected_port in self._selected_ports:
            selected_port.connect(port)
        PortConnector.hideNoodle()
        self.parent().close()

    """ UTILS """
    def getDisplayPorts(self):
        if self._port_type == INPUT_PORT:
            ports = self._node.getInputPorts()
        elif self._port_type == OUTPUT_PORT:
            ports = self._node.getOutputPorts()

        return ports

    def getSelectedPort(self, port_name):
        """ Gets the port from the port name provided

        Args:
            port_name (str): """
        if self._port_type == INPUT_PORT:
            port = self._node.getInputPort(port_name)
        elif self._port_type == OUTPUT_PORT:
            port = self._node.getOutputPort(port_name)

        return port


class PortConnector():
    """ Main function for the port connector display """
    def __init__(self):
        PortConnector.active_port = None

    @staticmethod
    def actuateSelection(display_warning=True, is_recursive_selection=False, nodegraph_widget=None, node=None, port_type=None):
        """ Run when the user presses "~"

        This is the main switch that will determine what should be done.

        1.) This will detect the nearest node to the cursor when the hotkey is pressed.
        2a.) If no port is selected, select a port.  If there are multiple ports on the node,
            then show the user a GUI to select a port
        2b.) If a port is selected, then connect the port.  If multiple ports are available to be
            connected, then show the user a GUI to select a port.

        Args:
            display_warning (bool): determines if a display_warning should popup for users if the port is already
                connected.  This is only valid when doing a connection event.
            is_recursive_selection (bool):
            nodegraph_widget (NodgraphWiget):
            node (Node): Node to display port selection of
            port_type (PORT_TYPE): to be selected
        """
        if not nodegraph_widget:
            widget_under_cursor = getWidgetUnderCursor().__module__.split(".")[-1]
            if widget_under_cursor != "NodegraphWidget": return
            nodegraph_widget = getWidgetUnderCursor()

        is_selection_active = PortConnector.isSelectionActive()

        # CONNECT PORTS
        if is_selection_active:
            PortConnector.connectPortEvent(display_warning=display_warning, is_recursive_selection=is_recursive_selection)

        # SELECT PORT
        else:
            if not node:
                node = nodegraphutils.getClosestNode(has_output_ports=True)
                if not node: return
            PortConnector.setActiveNodegraphWidget(nodegraph_widget)
            PortConnector.selectPortEvent(node=node, port_type=port_type)

    @staticmethod
    def __connectOutputPorts(base_ports, display_warning, is_recursive_selection):
        exclude_nodes = [port.getNode() for port in base_ports]
        node = nodegraphutils.getClosestNode(has_input_ports=True, include_dynamic_port_nodes=True, exclude_nodes=exclude_nodes)
        if not node: return

        if len(node.getInputPorts()) == 0:
            connection_port = node.addInputPort("i0")
            for base_port in base_ports:
                connection_port.connect(base_port)
            PortConnector.hideNoodle()

        # SINGULAR INPUT PORT
        elif len(node.getInputPorts()) == 1:
            # MULTIPLE INPUT PORTS
            if node.getType() in nodegraphutils.dynamicInputPortNodes():
                katanaMainWindow()._port_popup_menu = MultiPortPopupMenuWidget(
                    node, port_type=INPUT_PORT, is_selection_active=True, selected_ports=base_ports, display_warning=display_warning,
                    is_recursive_selection=is_recursive_selection)
                katanaMainWindow()._port_popup_menu.show()
                centerWidgetOnCursor(katanaMainWindow()._port_popup_menu)

            # NORMAL NODE
            else:
                connection_port = node.getInputPortByIndex(0)
                is_connected = portutils.isPortConnected(connection_port)

                # prompt user to connect
                if display_warning and is_connected:
                    katanaMainWindow()._display_warning_widget = OverridePortWarningButtonPopupWidget(
                        node, connection_port, base_ports, is_recursive_selection=is_recursive_selection)
                    katanaMainWindow()._display_warning_widget.show()
                    centerWidgetOnCursor(katanaMainWindow()._display_warning_widget)

                # automagically connect
                else:
                    for base_port in base_ports:
                        connection_port.connect(base_port)
                    PortConnector.hideNoodle()

                    if is_recursive_selection:
                        PortConnector.actuateSelection(node=node, port_type=OUTPUT_PORT)

        # MULTIPLE INPUT PORTS
        elif 1 < len(node.getInputPorts()):
            katanaMainWindow()._port_popup_menu = MultiPortPopupMenuWidget(
                node, port_type=INPUT_PORT, is_selection_active=True, selected_ports=base_ports, display_warning=display_warning,
                is_recursive_selection=is_recursive_selection)
            katanaMainWindow()._port_popup_menu.show()
            centerWidgetOnCursor(katanaMainWindow()._port_popup_menu)

    @staticmethod
    def __connectInputPorts(base_ports, display_warning, is_recursive_selection):
        exclude_nodes = [port.getNode() for port in base_ports]
        node = nodegraphutils.getClosestNode(has_input_ports=True, include_dynamic_port_nodes=True, exclude_nodes=exclude_nodes)
        if not node: return

        if len(node.getOutputPorts()) == 0:
            connection_port = node.addOutputPort("i0")
            for base_port in base_ports:
                connection_port.connect(base_port)
            PortConnector.hideNoodle()

        # SINGULAR INPUT PORT
        elif len(node.getOutputPorts()) == 1:
            connection_port = node.getOutputPortByIndex(0)
            is_connected = portutils.isPortConnected(connection_port)

            # prompt user to connect
            if display_warning and is_connected:
                katanaMainWindow()._display_warning_widget = OverridePortWarningButtonPopupWidget(
                    node, connection_port, base_ports, is_recursive_selection=is_recursive_selection)
                katanaMainWindow()._display_warning_widget.show()
                centerWidgetOnCursor(katanaMainWindow()._display_warning_widget)

            # automagically connect
            else:
                for base_port in base_ports:
                    connection_port.connect(base_port)
                PortConnector.hideNoodle()

                if is_recursive_selection:
                    PortConnector.actuateSelection(node=node, port_type=INPUT_PORT)

        # MULTIPLE INPUT PORTS
        elif 1 < len(node.getOutputPorts()):
            katanaMainWindow()._port_popup_menu = MultiPortPopupMenuWidget(
                node, port_type=OUTPUT_PORT, is_selection_active=True, selected_ports=base_ports, display_warning=display_warning,
                is_recursive_selection=is_recursive_selection)
            katanaMainWindow()._port_popup_menu.show()
            centerWidgetOnCursor(katanaMainWindow()._port_popup_menu)

    @staticmethod
    def connectPortEvent(display_warning=True, is_recursive_selection=False):
        """ Run when the user has as port link selected, and is trying to connect a port"""
        link_connection_layer = PortConnector.getLinkConnectionLayer()
        if link_connection_layer:
            base_ports = link_connection_layer.getBasePorts()
            selection_type = PortConnector.selectionType()
            if selection_type == OUTPUT_PORT:
                PortConnector.__connectOutputPorts(base_ports, display_warning, is_recursive_selection)
            elif selection_type == INPUT_PORT:
                PortConnector.__connectInputPorts(base_ports, display_warning, is_recursive_selection)
                pass

    @staticmethod
    def selectPortEvent(node=None, port_type=None):
        """ Run when the user attempts to start a port connection event

        Args:
            node (Node): to display ports of
            port_type (PORTTYPE): The type of port to select
        """
        if not node:
            node = nodegraphutils.getClosestNode(has_output_ports=True)
            if not node: return

        # determine if cursor is above or below the closest node
        if port_type == None:
            mouse_pos = PortConnector.activeNodegraphWidget().getMousePos()
            world_pos = PortConnector.activeNodegraphWidget().mapFromQTLocalToWorld(mouse_pos.x(), mouse_pos.y())
            node_pos = NodegraphAPI.GetNodePosition(node)
            if world_pos[1] < node_pos[1]:
                port_type = OUTPUT_PORT
            if node_pos[1] < world_pos[1]:
                port_type = INPUT_PORT

        # GET OUTPUT PORTS
        if port_type == OUTPUT_PORT:
            # NO OUTPUT PORTS
            if 0 == len(node.getOutputPorts()):
                return

            # SINGULAR OUTPUT PORT
            if 1 == len(node.getOutputPorts()):
                PortConnector.active_port = node.getOutputPorts()[0]
                PortConnector.showNoodle(PortConnector.active_port)

            # MULTIPLE OUTPUT PORTS
            elif 1 < len(node.getOutputPorts()):
                katanaMainWindow()._port_popup_menu = MultiPortPopupMenuWidget(
                    node, is_selection_active=False, port_type=OUTPUT_PORT)
                katanaMainWindow()._port_popup_menu.show()
                centerWidgetOnCursor(katanaMainWindow()._port_popup_menu)
                katanaMainWindow()._port_popup_menu.activateWindow()
                katanaMainWindow()._port_popup_menu.setFocus()

        # GET INPUT PORTS
        if port_type == INPUT_PORT:
            if 0 == len(node.getInputPorts()):
                return
            # SINGULAR OUTPUT PORT
            if 1 == len(node.getOutputPorts()):
                PortConnector.active_port = node.getInputPorts()[0]
                PortConnector.showNoodle(PortConnector.active_port)

            # MULTIPLE OUTPUT PORTS
            elif 1 < len(node.getOutputPorts()):
                katanaMainWindow()._port_popup_menu = MultiPortPopupMenuWidget(
                    node, is_selection_active=False, port_type=INPUT_PORT)
                katanaMainWindow()._port_popup_menu.show()
                centerWidgetOnCursor(katanaMainWindow()._port_popup_menu)
                katanaMainWindow()._port_popup_menu.activateWindow()
                katanaMainWindow()._port_popup_menu.setFocus()

    @staticmethod
    def setActiveNodegraphWidget(nodegraph_widget=None):
        """ Sets the currently active nodegraph widget"""
        if not nodegraph_widget:
            nodegraph_widget = PortConnector.nodegraphWidget()
        katanaMainWindow()._active_nodegraph_widget = nodegraph_widget

    @staticmethod
    def activeNodegraphWidget():
        """ Returns the currently active nodegraph widget"""
        return katanaMainWindow()._active_nodegraph_widget

    @staticmethod
    def nodegraphWidget():
        """ Gets the nodegraph under the cursor"""
        # Todo update, as it hits the menu, instead of the nodegraph on release
        widget_under_cursor = getWidgetUnderCursor().__module__.split(".")[-1]
        if widget_under_cursor != "NodegraphWidget": return None

        return getWidgetUnderCursor()

    @staticmethod
    def getLinkConnectionLayer():
        """ Returns the link interaction layer.

        If it is not the last in the stack, this will return None"""
        nodegraph_widget = PortConnector.nodegraphWidget()
        last_layer = nodegraph_widget.getLayers()[-1]
        if isinstance(last_layer, LinkConnectionLayer):
            return last_layer

        return None

    @staticmethod
    def isSelectionActive():
        """ Determines if a port selection is active"""
        nodegraph_widget = PortConnector.nodegraphWidget()
        if not nodegraph_widget:
            nodegraph_widget = PortConnector.activeNodegraphWidget()
        graph_interaction = nodegraph_widget.getGraphInteraction()
        return not graph_interaction

    @staticmethod
    def selectionType():
        """ Returns the current selection type"""
        if not PortConnector.isSelectionActive(): return None
        link_connection_layer = PortConnector.getLinkConnectionLayer()
        base_ports = link_connection_layer.getBasePorts()
        if base_ports[0].getType() == OUTPUT_PORT:
            return OUTPUT_PORT
        if base_ports[0].getType() == INPUT_PORT:
            return INPUT_PORT

    @staticmethod
    def hideNoodle():
        """ Hides the noodle, or multiple noodles..."""
        nodegraph_widget = PortConnector.activeNodegraphWidget()
        last_layer = nodegraph_widget.getLayers()[-1]
        while isinstance(last_layer, LinkConnectionLayer):
            nodegraph_widget.idleUpdate()
            nodegraph_widget.removeLayer(last_layer)
            # nodegraph_widget = PortConnector.nodegraphWidget()
            last_layer = nodegraph_widget.getLayers()[-1]

        # remove glow color
        if hasattr(LinkConnectionLayer, "_highlighted_nodes"):
            # if closest_node == getattr(LinkConnectionLayer, "_highlighted_nodes"): return
            nodeutils.removeGlowColor(LinkConnectionLayer._highlighted_nodes)
            delattr(LinkConnectionLayer, "_highlighted_nodes")

        # remove last active node
        from .linkConnectionLayerOverrides import removeLastActiveNode
        removeLastActiveNode()
        # delattr(katanaMainWindow(), "_active_nodegraph_widget")

    @staticmethod
    def showNoodle(port):
        """ Shows the noodle from the port provided

        Args:
            port (Port): """

        nodegraph_widget = PortConnector.activeNodegraphWidget()
        port_layer = nodegraph_widget.getLayerByName("PortInteractions")

        ls = port_layer.layerStack()
        layer = LinkConnectionLayer([port], None, enabled=True)
        ls.appendLayer(layer, stealFocus=True)

# PortConnector()