"""
TODO
    *   Connect to single port
            - show prompt if connected
"""
from qtpy.QtWidgets import QFrame, QVBoxLayout, QLabel
from qtpy.QtCore import Qt

from Katana import Utils, QT4Widgets, QT4GLLayerStack, NodegraphAPI, DrawingModule, ResourceFiles, KatanaPrefs, logging, PrefNames, UI4
from UI4.Tabs.NodeGraphTab.Layers.LinkConnectionLayer import LinkConnectionLayer

from cgwidgets.widgets import ButtonInputWidgetContainer
from cgwidgets.utils import centerWidgetOnCursor, setAsTransparent
from Utils2 import nodeutils

main_window = UI4.App.MainWindow.CurrentMainWindow()

INPUT_PORT = 0
OUTPUT_PORT = 1

class MultiPortPopupMenuWidget(QFrame):
    def __init__(self, node, port_type=OUTPUT_PORT, selected_port=None,  parent=None):
        super(MultiPortPopupMenuWidget, self).__init__(parent)
        # setup attrs
        self._node = node

        # create widgets
        self._title_widget = QLabel(node.getName())
        self._title_widget.setAlignment(Qt.AlignCenter)
        self._ports_widget = MultiPortPopupMenu(node, port_type=port_type, selected_port=selected_port,  parent=self)

        # setup layout
        QVBoxLayout(self)
        self.layout().setSpacing(0)
        self.layout().addWidget(self._title_widget)
        self.layout().addWidget(self._ports_widget)

        # setup display
        setAsTransparent(self)
        nodeutils.setGlowColor(node, (0.5, 0.5, 1))
        self.setStyleSheet("border: 1px solid rgba(128,128,255,255); margin: 2px")
        self.setContentsMargins(10, 10, 10, 10)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

        QFrame.keyPressEvent(self, event)

    def closeEvent(self, event):
        main_window.activateWindow()
        nodeutils.setGlowColor(self._node, None)
        QFrame.closeEvent(self, event)

    def leaveEvent(self, event):
        self.close()
        QFrame.leaveEvent(self, event)

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
        selected_port (port): port currently selected

    """
    def __init__(self, node, port_type=OUTPUT_PORT, selected_port=None,  parent=None):
        super(MultiPortPopupMenu, self).__init__(parent, Qt.Vertical)

        # setup attrs
        self._selected_port = selected_port
        self._node = node
        self._port_type = port_type
        self.setIsToggleable(False)

        for port in self.getDisplayPorts():
            self.addButton(port.getName(), port.getName(), self.portSelectedEvent)

    """ EVENTS """
    def portSelectedEvent(self, widget):
        """ Event run when the user selects a port"""
        port = self.getSelectedPort(widget.flag())

        # connect selected ports
        if self._port_type == INPUT_PORT:
            self._selected_port.connect(port)

        # show noodle
        elif self._port_type == OUTPUT_PORT:
            NodeConnector.showNoodle(port)

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


class NodeConnector():
    def __init__(self):
        self.output_port = None
        self.main()

    def main(self):
        """ Run when the node is initialized.

        This is the main switch that will determine what should be done.

        1.) This will detect the nearest node to the cursor when the hotkey is pressed.
        2a.) If no port is selected, select a port.  If there are multiple ports on the node,
            then show the user a GUI to select a port
        2b.) If a port is selected, then connect the port.  If multiple ports are available to be
            connected, then show the user a GUI to select a port.
        """
        nodegraph_tab = UI4.App.Tabs.FindTopTab('Node Graph')
        nodegraph_widget = nodegraph_tab.getNodeGraphWidget()
        node = nodeutils.getClosestNode()
        graph_interaction = nodegraph_widget.getGraphInteraction()

        # has not selected a port yet
        if graph_interaction is True:
            # no port selected yet...
            if len(node.getOutputPorts()) == 1:
                self.output_port = node.getOutputPorts()[0]
                self.showNoodle(self.output_port)
            elif len(node.getOutputPorts()) > 1:
                main_window._port_popup_menu = MultiPortPopupMenuWidget(node)
                main_window._port_popup_menu.show()
                centerWidgetOnCursor(main_window._port_popup_menu)

        elif graph_interaction is False:
            link_connection_layer = nodegraph_widget.getLayers()[-1]
            if isinstance(link_connection_layer, LinkConnectionLayer):
                base_ports = link_connection_layer.getBasePorts()

                if len(node.getInputPorts()) == 1:
                    for base_port in base_ports:
                        node.getInputPortByIndex(0).connect(base_port)

                elif len(node.getInputPorts()) > 1:
                    main_window._port_popup_menu = MultiPortPopupMenuWidget(node, port_type=INPUT_PORT, selected_port=base_ports[0])
                    main_window._port_popup_menu.show()
                    centerWidgetOnCursor(main_window._port_popup_menu)

                nodegraph_widget.idleUpdate()
                nodegraph_widget.removeLayer(link_connection_layer)
            # port is selected... so do this

    @staticmethod
    def showNoodle(port):
        """ Shows the noodle from the port provided

        Args:
            port (Port): """
        nodegraph_tab = UI4.App.Tabs.FindTopTab('Node Graph')
        nodegraph_widget = nodegraph_tab.getNodeGraphWidget()
        port_layer = nodegraph_widget.getLayerByName("PortInteractions")

        ls = port_layer.layerStack()
        layer = LinkConnectionLayer([port], None, enabled=True)
        ls.appendLayer(layer, stealFocus=True)


nc = NodeConnector()