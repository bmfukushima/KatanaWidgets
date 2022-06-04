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
    *   Network Material Create / Shading Nodes
"""
from qtpy.QtWidgets import QFrame, QVBoxLayout, QLabel, QApplication
from qtpy.QtCore import Qt

from Katana import Utils, QT4Widgets, QT4GLLayerStack, NodegraphAPI, DrawingModule, ResourceFiles, KatanaPrefs, logging, PrefNames, UI4
from UI4.Tabs.NodeGraphTab.Layers.LinkConnectionLayer import LinkConnectionLayer

from cgwidgets.widgets import ButtonInputWidgetContainer, ButtonInputWidget, FrameInputWidgetContainer
from cgwidgets.utils import centerWidgetOnCursor, setAsBorderless, setAsTransparent, getWidgetUnderCursor, isCursorOverWidget, getWidgetAncestor
from Utils2 import nodeutils, portutils, getFontSize, nodegraphutils
from Utils2.widgetutils import katanaMainWindow, getActiveNodegraphWidget


OUTPUT_PORT = 0
INPUT_PORT = 1


class OverridePortWarningButtonPopupWidget(QFrame):
    def __init__(self, node, connection_port, active_ports, is_recursive_selection=False, parent=None):
        super(OverridePortWarningButtonPopupWidget, self).__init__(parent)
        # setup attrs

        self._active_ports = active_ports

        # setup layout
        QVBoxLayout(self)
        self._button_widget = OverridePortWarningButtonWidget(node, connection_port, active_ports, is_recursive_selection=is_recursive_selection)
        self.layout().addWidget(self._button_widget)

        # setup display
        setAsBorderless(self)
        # self.setContentsMargins(10, 10, 10, 10)
        self.setStyleSheet("""QFrame{border: 1px solid rgba(128,128,255,255); margin: 2px}""")
        if not PortConnector.isSelectionActive():
            PortConnector.showNoodle(active_ports)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
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
        active_ports (port):

    Attributes:
        show_noodle (bool): determines if the noodle should be shown on exit
        input_port (port):
        output_port (port)
    """
    def __init__(self, node, connection_port, active_ports, is_recursive_selection=False, parent=None):
        super(OverridePortWarningButtonWidget, self).__init__(parent=parent)

        # setup attrs
        self._is_recursive_selection = is_recursive_selection
        self._connection_port = connection_port
        self._active_ports = active_ports
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
        Utils.UndoStack.OpenGroup("Connect Nodes")
        try:
            for selected_port in self._active_ports:
                self._connection_port.connect(selected_port)
            PortConnector.hideNoodle()

            if self._is_recursive_selection:
                self.parent().hide()
                QApplication.processEvents()
                katanaMainWindow().activateWindow()
                katanaMainWindow().setFocus()
                PortConnector.actuateSelection(
                    PortConnector.activeNodegraphWidget(), node=self.node(), port_type=self._active_ports[0].getType())
            parent = getWidgetAncestor(self, OverridePortWarningButtonPopupWidget)
            parent.close()
        finally:
            Utils.UndoStack.CloseGroup()
        # self.parent().close()


class MultiPortPopupMenuWidget(FrameInputWidgetContainer):
    def __init__(self, node, port_list=None, port_type=OUTPUT_PORT, active_ports=None, display_warning=True, is_selection_active=None, is_recursive_selection=False, parent=None):
        super(MultiPortPopupMenuWidget, self).__init__(parent)
        # setup attrs
        self._node = node
        self._is_selection_active = is_selection_active
        self._active_ports = active_ports
        self.setTitle(node.getName())
        self.setIsHeaderEditable(False)
        self.setDirection(Qt.Vertical)

        # create widgets
        self._title_widget = QLabel(node.getName())
        self._title_widget.setAlignment(Qt.AlignCenter)
        self._ports_widget = MultiPortPopupMenu(
            node,
            port_type=port_type,
            active_ports=active_ports,
            display_warning=display_warning,
            is_selection_active=is_selection_active,
            is_recursive_selection=is_recursive_selection,
            port_list=port_list,
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
                PortConnector.showNoodle(active_ports)

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
        flags = self._ports_widget.flags()
        if 0 < len(flags):
            if self._is_selection_active:
                self._ports_widget.connectPorts()
            else:
                self._ports_widget.showNoodleForMultiplePorts()
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
        flags (list): of strings that show all of the ports currently selected by the user in this GUI
        is_selection_active (bool): Determines if there are links currently selected
        node (node): closest node of selection.  This is the node containing the connected ports.
        port_list (list): of ports
            This is only used when connecting multiple output ports to a single input port.  This list of
            ports will popup and be shown to the user for connection.
        port_type (PORT_TYPE): the type of ports that will be displayed to the user
        active_ports (list): of ports currently selected
            Note: these are not the ports selected by the user in this GUI

    """
    def __init__(self, node, port_list=None, port_type=OUTPUT_PORT, is_selection_active=None, active_ports=None, display_warning=True, is_recursive_selection=False, parent=None):
        super(MultiPortPopupMenu, self).__init__(parent, Qt.Vertical)

        # setup attrs
        self._node = node
        self._is_recursive_selection = is_recursive_selection
        self._port_type = port_type
        self._is_selection_active = is_selection_active
        self._active_ports = active_ports
        self._display_warning = display_warning
        self.setIsToggleable(False)

        # populate ports
        if port_list:
            for port in port_list:
                self.addButton(port.getName(), port.getName(), self.connectMultipleOutputsToSingleInput)
        else:
            for port in self.getDisplayPorts():
                self.addButton(port.getName(), port.getName(), self.portSelectedEvent)

            if is_selection_active:
                if node.getType() in nodegraphutils.dynamicInputPortNodes():
                    self.addButton("< New >", "< New >", self.createNewPortEvent)
            else:
                self.addButton("< All >", "< All >", self.selectAllNoodlesEvent)

    """ PROPERTIES """
    def node(self):
        return self._node

    """ EVENTS """
    def selectAllNoodlesEvent(self, widget):
        """ When the user selects the "Select All Noodles" options. This runs and closes the parent."""
        self.closeParent()

    def portSelectedEvent(self, widget):
        """ Event run when the user selects a port"""
        port = self.getPortFromName(widget.flag())
        if QApplication.keyboardModifiers() in [
            Qt.ShiftModifier,
            Qt.ControlModifier,
            (Qt.ShiftModifier | Qt.ControlModifier)
        ]:
            # by pass if modifiers are pressed
            pass

        else:
            # connect selected ports
            if self._is_selection_active:
                is_connected = portutils.isPortConnected(port)

                # port selected is connected, display display_warning
                if is_connected and self._display_warning and len(self._active_ports) == 1:
                    katanaMainWindow()._display_warning_widget = OverridePortWarningButtonPopupWidget(self._node, port, self._active_ports, is_recursive_selection=self._is_recursive_selection)
                    katanaMainWindow()._display_warning_widget.show()
                    centerWidgetOnCursor(katanaMainWindow()._display_warning_widget, raise_=True)

                # port selected has no connections, connect port
                else:
                    # recursive multi port selection
                    if self._is_recursive_selection:
                        self.parent().hide()
                        QApplication.processEvents()
                        katanaMainWindow().activateWindow()
                        katanaMainWindow().setFocus()
                        PortConnector.actuateSelection(PortConnector.activeNodegraphWidget(), node=self.node(), port_type=self._active_ports[0].getType())
                        return
                        # return

            # show noodle
            else:
                PortConnector.showNoodle([port])

            self.closeParent()

    def createNewPortEvent(self, widget):
        """ During port connection, when the user presses "< New >" this will be run"""
        Utils.UndoStack.OpenGroup("Connect Ports")

        selected_ports = self.getAllSelectedPorts()
        # connect all user defined ports first
        for x in range(len(selected_ports)):
            try:
                self._active_ports.pop(0).connect(selected_ports.pop(0))
                # del selected_ports[0]
            except IndexError:
                return

        # create new ports for the excess
        for active_port in self._active_ports:
            num_ports = len(self.node().getInputPorts())
            port = self.node().addInputPort(f"i{num_ports}")
            active_port.connect(port)

        Utils.UndoStack.CloseGroup()
        PortConnector.hideNoodle()
        self.closeParent()

    def keyPressEvent(self, event):
        if event.key() in [96, Qt.Key_Return, Qt.Key_Enter]:
            if self._is_selection_active:
                pass
            else:
                self.showNoodleForMultiplePorts()
            self.closeParent()
            return

        return ButtonInputWidgetContainer.keyPressEvent(self, event)

    """ UTILS """
    def closeParent(self):
        parent = getWidgetAncestor(self, MultiPortPopupMenuWidget)
        parent.close()

    def connectPorts(self):
        Utils.UndoStack.OpenGroup("Connect Ports")
        # special condition to connect all ports to a single source
        if len(self.flags()) == 1 and self._port_type == OUTPUT_PORT:
            connection_port = self.getPortFromName(self.flags()[0])
            for port in self._active_ports:
                port.connect(connection_port)
            PortConnector.hideNoodle()

        # connect ports
        else:
            self.connectNoodleForMultiplePorts()

        Utils.UndoStack.CloseGroup()

    def connectMultipleOutputsToSingleInput(self, widget):
        """ Special handler for connecting multiple output ports to a single input port """
        port = self.getPortFromName(widget.flag())
        self._active_ports[0].connect(port)
        PortConnector.hideNoodle()
        self.closeParent()

    def connectNoodleForMultiplePorts(self, auto_organize=False):
        """ When multiple noodles are selected, this will connect them to a node"""
        # todo how to handle auto organize here, and still allow user selection to parse through?
        # probably just say screw it and not allow user selection, because whose actually going to select
        # ports in reverse order and then hope it wires in... hopefully...
        # if auto_organize:
        #     active_ports = PortConnector.organizePortsByPosition(self._active_ports)
        # else:
        #     active_ports = self._active_ports

        active_ports = PortConnector.organizePortsByPosition(self._active_ports)
        # build ports to connect to
        connected_ports = self.getAllSelectedPorts()

        if "< New >" in self.flags():
            # note: this is handled in createNewPortEvent()
            pass
        else:
            # find all empty ports
            last_port_index = connected_ports[-1].getIndex()
            if self._port_type == OUTPUT_PORT:
                _end_ports = self.node().getOutputPorts()[last_port_index:]
            if self._port_type == INPUT_PORT:
                _end_ports = self.node().getInputPorts()[last_port_index:]
            for port in _end_ports:
                if len(port.getConnectedPorts()) == 0:
                    if port not in connected_ports:
                        connected_ports.append(port)

            # add additional ports
            if len(connected_ports) < len(active_ports):
                num_ports_to_add = len(active_ports) - len(connected_ports)
                for x in range(num_ports_to_add):
                    port_num = len(connected_ports)
                    if self._port_type == OUTPUT_PORT:
                        connected_ports.append(self.node().addOutputPort(f"o{port_num}"))
                    if self._port_type == INPUT_PORT:
                        connected_ports.append(self.node().addInputPort(f"i{port_num}"))

            # connect ports
            for i, port in enumerate(active_ports):
                port.connect(connected_ports[i])

        PortConnector.hideNoodle()

    def isTagValid(self, tags, valid_tags):
        """ Determines if a port tag is valid

        Args:
            tags (list): of port tags (strings)
            valid_tags (set): of port tags (strings)
            """
        # return valid if there are no tags to ensure all ports are visible
        if len(valid_tags) == 0 or len(tags) == 0:
            return True

        # check tags
        for tag in tags:
            if tag in valid_tags:
                return True

        return False

    def showNoodleForMultiplePorts(self):
        """ Shows the noodle for all of the currently selected ports"""
        # show all noodles
        if "< All >" in self.flags():
            PortConnector.showNoodle(self.getDisplayPorts())
            self.parent().close()

        # show selected noodles
        else:
            ports = []
            for port_name in self.flags():
                ports.append(self.getPortFromName(port_name))
            PortConnector.showNoodle(ports)

    def getDisplayPorts(self):
        """ Return a list of ports to be displayed to the user """

        # get valid tags
        valid_tags = set()
        if self._active_ports:
            for port in self._active_ports:
                tags = port.getTags()
                if tags:
                    for tag in tags:
                        valid_tags.add(tag)

        # get all ports
        if self._port_type == INPUT_PORT:
            ports = [port for port in self.node().getInputPorts() if self.isTagValid(port.getTags(), valid_tags)]
        elif self._port_type == OUTPUT_PORT:
            ports = [port for port in self.node().getOutputPorts() if self.isTagValid(port.getTags(), valid_tags)]



        return ports

    def getAllSelectedPorts(self):
        """ Returns a list of all of the ports the user has selected in this GUI

        Returns (list): of PORTS"""
        connection_port_names = self.flags()
        connected_ports = []
        for port_name in connection_port_names:
            port = self.getPortFromName(port_name)
            if port:
                connected_ports.append(port)

        return connected_ports

    def getPortFromName(self, port_name):
        """ Gets the port from the port name provided

        Args:
            port_name (str): """
        if self._port_type == INPUT_PORT:
            port = self._node.getInputPort(port_name)
        elif self._port_type == OUTPUT_PORT:
            port = self._node.getOutputPort(port_name)

        return port


class PortConnector():
    """ Main function for the port connector display

    Attributes:
        _link_selection_last_active_ports (list): of ports that were last active during link selection
            This is used when the user creates a node during link connection
        _active_nodegraph_widget (NodeGraphWidget): Node Graph widget the user is currently using
            This is required as getting the node graph requires a node graph to be directly under the cursor,
            so the popup widgets will fail.

        """

    def __init__(self):
        PortConnector.active_port = None

    """ UTILS """
    @staticmethod
    def getPortPosition(port):
        view_scale = PortConnector.activeNodegraphWidget().getViewScale()[0]
        pos = DrawingModule.nodeWorld_getPortPosition(port, view_scale)
        return pos

    @staticmethod
    def organizePortsByPosition(ports):
        """ Organizes the ports in a list based off of their world coordinates from upper left
        to bottom right.

        This is done by calculating the ports YPos first, and seeing if it fits into a chunk
        specific chunk size.  After all ports in that ypos chunksize are arranged, they are
        then arranged by their xpos.  So this in theory should read top left, to bottom right.

        Args:
            ports (dict): of ports to be organized
                {y_block: list(ports)}
                Note: This list will need to be sorted in reverse order in order to retrieve it
                    as a top to bottom list.
        """
        chunk_size = 100

        # sort ports
        # {y_block: list(ports)}
        """ This sorting algo works by
        1.) Checking to see if there are ports, if there are not ports, then initialize and add the first port
        2.) Checking to see if this port should be the last port
        3.) Checking to see if this port sits somewhere in the middle """
        port_map = {}

        for active_port in ports:
            active_pos = PortConnector.getPortPosition(active_port)
            # Initalize list of ports
            y_block = int(active_pos[1] // chunk_size)
            if y_block not in port_map:
                # is not yet initialize
                port_map[y_block] = [active_port]

            # Port should be last entry in the list
            elif PortConnector.getPortPosition(port_map[y_block][-1])[0] < active_pos[0]:
                port_map[y_block].append(active_port)
                pass

            # Port sits somewhere in the middle
            else:
                for i, _port in enumerate(port_map[y_block]):
                    _port_pos = PortConnector.getPortPosition(_port)
                    if active_pos[0] < _port_pos[0]:
                        port_map[y_block].insert(i, active_port)
                        break

        # compile list
        port_list = []
        for y_block in reversed(sorted(port_map)):
            port_chunk = port_map[y_block]
            for port in port_chunk:
                port_list.append(port)

        return port_list
        # sort by xpos

    """ PROPERTIES """
    @staticmethod
    def activeNodegraphWidget():
        """ Returns the currently active nodegraph widget"""
        return katanaMainWindow()._active_nodegraph_widget

    @staticmethod
    def setActiveNodegraphWidget(nodegraph_widget=None):
        """ Sets the currently active nodegraph widget"""
        if not nodegraph_widget:
            nodegraph_widget = getActiveNodegraphWidget()
        katanaMainWindow()._active_nodegraph_widget = nodegraph_widget

    @staticmethod
    def getLastActiveLinkSelectionPorts(organize_ports=False):
        """ Returns the last actively selected ports.

        This is attribute is set when the user selects ports and is only used when the user
        is attempting to create a node with an active link selection """
        if hasattr(katanaMainWindow(), "_link_selection_last_active_ports"):
            ports = getattr(katanaMainWindow(), "_link_selection_last_active_ports")
            if organize_ports:
                ports = PortConnector.organizePortsByPosition(ports)
            return ports
        else:
            return list()

    @staticmethod
    def setLastActiveLinkSelectionPorts(ports):
        setattr(katanaMainWindow(), "_link_selection_last_active_ports", ports)

    @staticmethod
    def getLinkConnectionLayer():
        """ Returns the link interaction layer.

        If it is not the last in the stack, this will return None"""
        nodegraph_widget = getActiveNodegraphWidget()
        for layer in reversed(nodegraph_widget.getLayers()):
            if isinstance(layer, LinkConnectionLayer):
                return layer

        return None

    @staticmethod
    def isSelectionActive():
        """ Determines if a port selection is active"""
        nodegraph_widget = getActiveNodegraphWidget()
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

    """ EVENTS """
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

    # todo abstract this to function
    @staticmethod
    def __connectOutputPorts(base_ports, display_warning, is_recursive_selection):
        exclude_nodes = [port.getNode() for port in base_ports]
        node = nodegraphutils.getClosestNode(has_input_ports=True, include_dynamic_port_nodes=True, exclude_nodes=exclude_nodes)
        if not node: return

        if len(node.getInputPorts()) == 0:
            if node.getType() in nodegraphutils.dynamicInputPortNodes():
                for i, base_port in enumerate(base_ports):
                    connection_port = node.addInputPort(f"i{i}")
                    connection_port.connect(base_port)
            else:
                connection_port = node.addInputPort("i0")
                connection_port.connect(base_ports[0])
            PortConnector.hideNoodle()

        # SINGULAR INPUT PORT
        elif len(node.getInputPorts()) == 1:
            # MULTIPLE INPUT PORTS
            if node.getType() in nodegraphutils.dynamicInputPortNodes():
                katanaMainWindow()._port_popup_menu = MultiPortPopupMenuWidget(
                    node, port_type=INPUT_PORT, is_selection_active=True, active_ports=base_ports, display_warning=display_warning,
                    is_recursive_selection=is_recursive_selection)
                katanaMainWindow()._port_popup_menu.show()
                centerWidgetOnCursor(katanaMainWindow()._port_popup_menu)
            elif 1 < len(base_ports):
                # This is a special case for the MultiPortPopupMenuWidget
                """ This essentially hacks together the popup to show the user the port to connect from their 
                currently active selection """
                katanaMainWindow()._port_popup_menu = MultiPortPopupMenuWidget(
                    base_ports[0].getNode(), port_list=base_ports, port_type=OUTPUT_PORT, is_selection_active=True, active_ports=[node.getInputPortByIndex(0)], display_warning=display_warning,
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

                    PortConnector.setLastActiveLinkSelectionPorts([])

                    if is_recursive_selection:
                        PortConnector.actuateSelection(node=node, port_type=OUTPUT_PORT)

        # MULTIPLE INPUT PORTS
        elif 1 < len(node.getInputPorts()):
            katanaMainWindow()._port_popup_menu = MultiPortPopupMenuWidget(
                node, port_type=INPUT_PORT, is_selection_active=True, active_ports=base_ports, display_warning=display_warning,
                is_recursive_selection=is_recursive_selection)
            katanaMainWindow()._port_popup_menu.show()
            centerWidgetOnCursor(katanaMainWindow()._port_popup_menu)

    # todo abstract this to function
    @staticmethod
    def __connectInputPorts(base_ports, display_warning, is_recursive_selection):
        exclude_nodes = [port.getNode() for port in base_ports]
        node = nodegraphutils.getClosestNode(has_output_ports=True, include_dynamic_port_nodes=True, exclude_nodes=exclude_nodes)
        if not node: return

        if len(node.getOutputPorts()) == 0:
            connection_port = node.addOutputPort("i0")
            for base_port in base_ports:
                connection_port.connect(base_port)
            PortConnector.hideNoodle()

        # SINGULAR OUTPUT PORT
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

                PortConnector.setLastActiveLinkSelectionPorts([])

                if is_recursive_selection:
                    PortConnector.actuateSelection(node=node, port_type=INPUT_PORT)

        # MULTIPLE OUTPUT PORTS
        elif 1 < len(node.getOutputPorts()):
            katanaMainWindow()._port_popup_menu = MultiPortPopupMenuWidget(
                node, port_type=OUTPUT_PORT, is_selection_active=True, active_ports=base_ports, display_warning=display_warning,
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
            Utils.UndoStack.OpenGroup("Connect Ports")
            if selection_type == OUTPUT_PORT:
                PortConnector.__connectOutputPorts(base_ports, display_warning, is_recursive_selection)
            elif selection_type == INPUT_PORT:
                PortConnector.__connectInputPorts(base_ports, display_warning, is_recursive_selection)
            Utils.UndoStack.CloseGroup()

    @staticmethod
    def selectPortEvent(node=None, port_type=None):
        """ Run when the user attempts to start a port connection event

        Args:
            node (Node): to display ports of
            port_type (PORTTYPE): The type of port to select
        """
        # special condition to select all output ports if multiple nodes are selected
        """ This condition is only triggered if there are multiple nodes selected with 1 or more output ports """
        selected_nodes = [node for node in NodegraphAPI.GetAllSelectedNodes() if 0 < len(node.getOutputPorts())]
        if 1 < len(selected_nodes):
            ports = [port.getOutputPortByIndex(0) for port in selected_nodes]
            PortConnector.showNoodle(ports)
            return

        # normal connection
        if not node:
            node = nodegraphutils.getClosestNode(has_output_ports=True)
            if not node: return

        # determine port connection type to query, if none provided
        """ For normal nodes, this will check to see if the cursor is above/below the current
        node, for shading nodes, this will check the left/right orientation
        
        Note: The "port_type is None" here is required as the "port_type" provided might be 0"""
        if port_type is None:
            mouse_pos = PortConnector.activeNodegraphWidget().getMousePos()
            world_pos = PortConnector.activeNodegraphWidget().mapFromQTLocalToWorld(mouse_pos.x(), mouse_pos.y())
            node_pos = NodegraphAPI.GetNodePosition(node)
            if nodeutils.isShadingNode(node):
                if world_pos[0] < node_pos[0]:
                    port_type = INPUT_PORT
                if node_pos[0] < world_pos[0]:
                    port_type = OUTPUT_PORT
            else:
                if world_pos[1] < node_pos[1]:
                    port_type = OUTPUT_PORT
                if node_pos[1] < world_pos[1]:
                    port_type = INPUT_PORT

        # GET PORTS
        ports = None
        if port_type == OUTPUT_PORT:
            ports = node.getOutputPorts()
            port_type = OUTPUT_PORT
        if port_type == INPUT_PORT:
            ports = node.getInputPorts()
            port_type = INPUT_PORT

        # Show noodle
        if ports:
            # NO OUTPUT PORTS
            if 0 == len(ports):
                return

            # SINGULAR OUTPUT PORT
            if 1 == len(ports):
                PortConnector.active_port = ports[0]
                PortConnector.showNoodle([PortConnector.active_port])

            # MULTIPLE OUTPUT PORTS
            elif 1 < len(ports):
                katanaMainWindow()._port_popup_menu = MultiPortPopupMenuWidget(
                    node, is_selection_active=False, port_type=port_type)
                katanaMainWindow()._port_popup_menu.show()
                centerWidgetOnCursor(katanaMainWindow()._port_popup_menu)
                katanaMainWindow()._port_popup_menu.activateWindow()
                katanaMainWindow()._port_popup_menu.setFocus()

    @staticmethod
    def hideNoodle():
        """ Hides the noodle, or multiple noodles..."""
        # hide noodle
        nodegraph_widget = PortConnector.activeNodegraphWidget()
        for layer in reversed(nodegraph_widget.getLayers()):
            if isinstance(layer, LinkConnectionLayer):
                nodegraph_widget.idleUpdate()
                nodegraph_widget.removeLayer(layer)

        # remove glow color
        if hasattr(LinkConnectionLayer, "_highlighted_nodes"):
            nodeutils.removeGlowColor(LinkConnectionLayer._highlighted_nodes)
            delattr(LinkConnectionLayer, "_highlighted_nodes")

    @staticmethod
    def showNoodle(ports, nodegraph=None):
        """ Shows the noodle from the port provided

        Args:
            ports (list): of ports to show
            nodegraph (NodeGraph): Instance of nodegraph to work on"""

        if not nodegraph:
            nodegraph_widget = PortConnector.activeNodegraphWidget()

        layer = LinkConnectionLayer(ports, None, enabled=True)
        nodegraph_widget.appendLayer(layer, stealFocus=True)

        # update port last active port selection
        base_ports = []
        for layer in reversed(nodegraph_widget.getLayers()):
            if isinstance(layer, LinkConnectionLayer):
                base_ports += layer.getBasePorts()
        PortConnector.setLastActiveLinkSelectionPorts(base_ports)
