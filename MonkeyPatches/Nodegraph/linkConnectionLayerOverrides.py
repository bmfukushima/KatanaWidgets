""" Todo:
        Cleanup link connection attributes"""

from qtpy.QtCore import QTimer, Qt, QPoint

from Utils2 import nodeutils

from Katana import NodegraphAPI, Utils, DrawingModule, KatanaPrefs, PrefNames
from UI4.Tabs.NodeGraphTab.Layers.LinkConnectionLayer import LinkConnectionLayer
from UI4.App import Tabs

from .portConnector import PortConnector
from Utils2 import widgetutils, nodegraphutils


def createDotNode(port):
    """ Creates a dot node in the Link Connection Layer """
    from MonkeyPatches.Nodegraph.portConnector import PortConnector

    """ Creates a dot node """
    nodegraph_widget = widgetutils.getActiveNodegraphWidget()
    # get cursor position
    cursor_pos = nodegraph_widget.getMousePos()
    group_node = nodegraph_widget.getGroupNodeUnderMouse()
    world_pos = nodegraph_widget.mapFromQTLocalToWorld(cursor_pos.x(), cursor_pos.y())
    cursor_pos = QPoint(*nodegraph_widget.getPointAdjustedToGroupNodeSpace(group_node, world_pos))
    if KatanaPrefs[PrefNames.NODEGRAPH_GRIDSNAP]:
        cursor_pos = nodegraphutils.getNearestGridPoint(cursor_pos.x(), cursor_pos.y())

    # create dot node
    dot_node = NodegraphAPI.CreateNode("Dot", group_node)
    NodegraphAPI.SetNodePosition(dot_node, [cursor_pos.x(), cursor_pos.y()])
    dot_node.getInputPortByIndex(0).connect(port)

    # update display
    PortConnector.hideNoodle()
    PortConnector.showNoodle(dot_node.getOutputPortByIndex(0))

    return dot_node


def removeLastActiveNode():
    if hasattr(widgetutils.katanaMainWindow(), "_link_connection_active_node"):
        delattr(widgetutils.katanaMainWindow(), "_link_connection_active_node")


def lastActiveNode():
    return widgetutils.katanaMainWindow()._link_connection_active_node


def setLastActiveNode(node):
    widgetutils.katanaMainWindow()._link_connection_active_node = node


# link connection mouse move
def linkConnectionLayerMouseMove(func):
    """ Changes the color of the nearest node """
    def __linkConnectionLayerMouseMove(self, event):
        def colorNearestNode():
            base_ports = self.getBasePorts()
            if 0 < len(base_ports):
                exclude_nodes = [base_ports[0].getNode()]
                nodeutils.updateNodePreviewColors(exclude_nodes=exclude_nodes, has_input_ports=True)

        def unfreeze():
            self._is_frozen = False

        delay_amount = 100
        # setup frozen attr
        if not hasattr(self, "_is_frozen"):
            self._is_frozen = False

        # run events on timer
        if not self._is_frozen:
            # setup timer
            timer = QTimer()
            timer.start(delay_amount)
            timer.timeout.connect(unfreeze)
            colorNearestNode()

        return func(self, event)

    return __linkConnectionLayerMouseMove


def linkConnectionLayerKeyPress(func):
    def __linkConnectionLayerKeyPress(self, event):
        widgetutils.katanaMainWindow()._is_link_creation_active = True
        if not hasattr(widgetutils.katanaMainWindow(), "_link_connection_active_node"):
            if 0 < len(self.getBasePorts()):
                last_active_node = self.getBasePorts()[0].getNode()
                setLastActiveNode(last_active_node)

        if event.key() == Qt.Key_D:
            if not event.isAutoRepeat():
                dot_node = createDotNode(self.getBasePorts()[0])
                setLastActiveNode(dot_node)
                return True

        if event.key() == 96:
            """ Note: Recursive selection is handled through the ScriptManager, as for some reason
            ShiftModifier events are not recognized here"""
            # get warning status
            display_warning = True

            if (event.modifiers() & Qt.AltModifier) == Qt.AltModifier:
                display_warning = False

            # actuate
            PortConnector.actuateSelection(display_warning=display_warning, is_recursive_selection=False)

            return True

        if event.key() == Qt.Key_Tab:
            """ Connect last active node/port (dot, or first node selected) to first node created 
            
            # Todo hiding link here... because on exit doesnt work
            Might need to do something like this??
            self.layerStack().releaseMouse()"""
            # hide link
            nodegraph_widget = self.layerStack()
            for layer in reversed(nodegraph_widget.getLayers()):
                if isinstance(layer, LinkConnectionLayer):
                    nodegraph_widget.removeLayer(layer)
            nodegraph_widget.idleUpdate()

            # launch node menu
            interaction_layer = nodegraph_widget.getLayerByName("NodeInteractions")
            interaction_layer._NodeInteractionLayer__launchNodeCreationMenuLayer()
            return True

        func(self, event)
    return __linkConnectionLayerKeyPress


def exitLink(func):
    def __exitLink(self, *args):
        # remove glow color
        if hasattr(LinkConnectionLayer, "_highlighted_nodes"):
            nodeutils.removeGlowColor(LinkConnectionLayer._highlighted_nodes)
            delattr(LinkConnectionLayer, "_highlighted_nodes")

        # toggle last active node flags
        widgetutils.katanaMainWindow()._is_link_creation_active = False
        removeLastActiveNode()

        func(self, *args)
    return __exitLink


def placeNodeOverride(func):
    def __placeNodeOverride(node, shouldFloat=True, maskInputPreferred=False, autoPlaceAllowed=True):
        setLastActiveNode(None)
        return func(node, shouldFloat=shouldFloat, maskInputPreferred=maskInputPreferred, autoPlaceAllowed=autoPlaceAllowed)

    return __placeNodeOverride


def installLinkConnectionLayerOverrides(**kwargs):
    """ Installs the overrides for the link connection layer"""
    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()
    nodegraph_widget.placeNode = placeNodeOverride(nodegraph_widget.placeNode)

    # link interaction monkey patch
    LinkConnectionLayer._LinkConnectionLayer__processMouseMove = linkConnectionLayerMouseMove(LinkConnectionLayer._LinkConnectionLayer__processMouseMove)
    LinkConnectionLayer._LinkConnectionLayer__processKeyPress = linkConnectionLayerKeyPress(LinkConnectionLayer._LinkConnectionLayer__processKeyPress)

    LinkConnectionLayer._LinkConnectionLayer__connectLinks = exitLink(LinkConnectionLayer._LinkConnectionLayer__connectLinks)
    LinkConnectionLayer._LinkConnectionLayer__dropLinks = exitLink(LinkConnectionLayer._LinkConnectionLayer__dropLinks)
    LinkConnectionLayer._LinkConnectionLayer__exitNoChange = exitLink(LinkConnectionLayer._LinkConnectionLayer__exitNoChange)

