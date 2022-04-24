from qtpy.QtCore import QTimer, Qt, QPoint

from Utils2 import nodeutils

from Katana import NodegraphAPI, Utils, DrawingModule, KatanaPrefs, PrefNames
from UI4.Tabs.NodeGraphTab.Layers.LinkConnectionLayer import LinkConnectionLayer

from .portConnector import PortConnector
from .gridLayer import GridUtils
from Utils2 import widgetutils, nodealignutils
from Utils2.nodealignutils import AlignUtils

# def createDotNode(self):
#     Utils.OpenGLTraceMarker.begin()
#     basePorts = self.getBasePorts()
#     if not basePorts:
#         Utils.OpenGLTraceMarker.end()
#         return False
#     if len(basePorts) != 1:
#         if basePorts[0].getType() == NodegraphAPI.Port.TYPE_PRODUCER:
#             Utils.OpenGLTraceMarker.end()
#             return False
#     else:
#         if NodegraphAPI.IsNodeLockedByParents(basePorts[0].getNode()):
#             Utils.OpenGLTraceMarker.end()
#             return False
#         mousePos = self.layerStack().getMousePos()
#         return mousePos or False
#     from qtpy.QtGui import QCursor
#     #mousePos = QCursor.pos()
#     mousePos = self.layerStack().mapFromQTLocalToWorld(mousePos.x(), mousePos.y())
#     rootview = self.layerStack().getCurrentNodeView()
#     rootviewscale = self.layerStack().getViewScale()[0]
#     parentNode = DrawingModule.nodeWorld_findGroupNodeOfClick(rootview, mousePos[0], mousePos[1], rootviewscale)
#     if parentNode is not None:
#         if parentNode.isContentLocked():
#             Utils.OpenGLTraceMarker.end()
#             return False
#     a, r, x, y = DrawingModule.nodeWorld_getGroupNodeRelativeAndAbsoluteChildScales(rootview, parentNode, rootviewscale, mousePos[0], mousePos[1])
#     Utils.UndoStack.OpenGroup('Create Dot Node')
#     try:
#         dot = NodegraphAPI.CreateNode('Dot', parentNode)
#         if KatanaPrefs[PrefNames.NODEGRAPH_GRIDSNAP]:
#             GRIDSIZEX = GridUtils.gridSizeX()
#             GRIDSIZEY = GridUtils.gridSizeY()
#             xmod = x % GRIDSIZEX
#             if xmod > GRIDSIZEX / 2.0:
#                 xmod = (GRIDSIZEX - xmod) * -1
#             ymod = y % GRIDSIZEY
#             if ymod > GRIDSIZEY / 2.0:
#                 ymod = (GRIDSIZEY - ymod) * -1
#             x -= xmod
#             y -= ymod
#         else:
#             NodegraphAPI.SetNodePosition(dot, (x, y))
#             if basePorts[0].getType() == NodegraphAPI.Port.TYPE_PRODUCER:
#                 basePorts[0].connect(dot.getInputPortByIndex(0))
#                 outputPort = dot.getOutputPortByIndex(0)
#                 self._LinkConnectionLayer__basePorts = [
#                  self._LinkConnectionLayer__getPortDescription(outputPort, False)]
#             else:
#                 for port in basePorts:
#                     port.connect(dot.getOutputPortByIndex(0))
#
#             inputPort = dot.getInputPortByIndex(0)
#             self._LinkConnectionLayer__basePorts = [
#              self._LinkConnectionLayer__getPortDescription(inputPort, False)]
#         return True
#     finally:
#         Utils.UndoStack.CloseGroup()
#
#     Utils.OpenGLTraceMarker.end()
def createDotNode(port):

    from MonkeyPatches.Nodegraph.portConnector import PortConnector

    """ Creates a dot node """
    nodegraph_widget = widgetutils.getActiveNodegraphWidget()
    # get cursor position
    cursor_pos = nodegraph_widget.getMousePos()
    group_node = nodegraph_widget.getGroupNodeUnderMouse()
    world_pos = nodegraph_widget.mapFromQTLocalToWorld(cursor_pos.x(), cursor_pos.y())
    cursor_pos = nodegraph_widget.getPointAdjustedToGroupNodeSpace(group_node, world_pos)
    if KatanaPrefs[PrefNames.NODEGRAPH_GRIDSNAP]:
        cursor_pos = AlignUtils().getNearestGridPoint(cursor_pos[0], cursor_pos[1])

    # create dot node
    dot_node = NodegraphAPI.CreateNode("Dot", group_node)
    NodegraphAPI.SetNodePosition(dot_node, [*cursor_pos])
    dot_node.getInputPortByIndex(0).connect(port)

    # update display
    PortConnector.hideNoodle()
    PortConnector.showNoodle(dot_node.getOutputPortByIndex(0))

    return dot_node


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
            exclude_nodes = [base_ports[0].getNode()]
            nodeutils.colorClosestNode(exclude_nodes=exclude_nodes, has_input_ports=True)

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
        if hasattr(LinkConnectionLayer, "_closest_node"):
            nodeutils.removeGlowColor(LinkConnectionLayer._closest_node)
            delattr(LinkConnectionLayer, "_closest_node")

        # toggle last active node flags
        widgetutils.katanaMainWindow()._is_link_creation_active = False
        if hasattr(LinkConnectionLayer, "_link_connection_active_node"):
            delattr(LinkConnectionLayer, "_link_connection_active_node")

        func(self, *args)
    return __exitLink


def installLinkConnectionLayerOverrides(**kwargs):
    """ Installs the overrides for the link connection layer"""

    # link interaction monkey patch
    LinkConnectionLayer._LinkConnectionLayer__processMouseMove = linkConnectionLayerMouseMove(LinkConnectionLayer._LinkConnectionLayer__processMouseMove)
    LinkConnectionLayer._LinkConnectionLayer__processKeyPress = linkConnectionLayerKeyPress(LinkConnectionLayer._LinkConnectionLayer__processKeyPress)

    LinkConnectionLayer._LinkConnectionLayer__connectLinks = exitLink(LinkConnectionLayer._LinkConnectionLayer__connectLinks)
    LinkConnectionLayer._LinkConnectionLayer__dropLinks = exitLink(LinkConnectionLayer._LinkConnectionLayer__dropLinks)
    LinkConnectionLayer._LinkConnectionLayer__exitNoChange = exitLink(LinkConnectionLayer._LinkConnectionLayer__exitNoChange)

    # LinkConnectionLayer._LinkConnectionLayer__create_dot_node = createDotNode
