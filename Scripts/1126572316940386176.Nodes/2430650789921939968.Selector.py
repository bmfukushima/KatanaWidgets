"""
TODO
    *   Connect to single port
            - show prompt if connected
    *   Node Colors
            - Change node glow color
    *   Node Name
            Add node name to top of selection



"""
from qtpy.QtCore import Qt, QPoint
from qtpy.QtGui import QCursor

from Katana import Utils, QT4Widgets, QT4GLLayerStack, NodegraphAPI, DrawingModule, ResourceFiles, KatanaPrefs, logging, PrefNames, UI4
from UI4.Tabs.NodeGraphTab.Layers.LinkConnectionLayer import LinkConnectionLayer

from cgwidgets.widgets import ButtonInputWidgetContainer
from cgwidgets.utils import centerWidgetOnCursor, setAsTransparent
from Utils2 import nodeutils

main_window = UI4.App.MainWindow.CurrentMainWindow()

INPUT_PORT = 0
OUTPUT_PORT = 1


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

        setAsTransparent(self)

        nodeutils.setGlowColor(node, (0.5, 0.5, 1))

    """ EVENTS """
    def closeEvent(self, event):
        main_window.activateWindow()
        nodeutils.setGlowColor(self._node, None)
        ButtonInputWidgetContainer.closeEvent(self, event)

    def leaveEvent(self, event):
        self.close()
        ButtonInputWidgetContainer.leaveEvent(self, event)

    def showEvent(self, event):
        return_val = ButtonInputWidgetContainer.showEvent(self, event)
        if self.width() < 100:
            self.setFixedWidth(100)

        return return_val

    def portSelectedEvent(self, widget):
        """ Event run when the user selects a port"""
        port = self.getSelectedPort(widget.flag())

        # connect selected ports
        if self._port_type == INPUT_PORT:
            self._selected_port.connect(port)

        # show noodle
        elif self._port_type == OUTPUT_PORT:
            NodeConnector.showNoodle(port)

        self.close()

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
                main_window._port_popup_menu = MultiPortPopupMenu(node)
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
                    main_window._port_popup_menu = MultiPortPopupMenu(node, port_type=INPUT_PORT, selected_port=base_ports[0])
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