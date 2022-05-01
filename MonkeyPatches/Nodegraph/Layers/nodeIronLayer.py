""" The iron node layer allows users to "iron" their nodes

As the user swipes through nodes using CTRL+ALT+SHIFT+LMB, all
of the nodes hit will be aligned to the first node, based off
of the direction of the cursor as it passed through the second node.
"""
import math

from OpenGL.GL import (
    glBegin,
    glLineWidth,
    GL_LINE_STRIP,
    GL_LINE_LOOP,
    glColor4f,
    glEnd,
    glVertex2f,
    glPointSize,
)
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt, QPoint, QEvent, QTimer

# setup prefs
import QT4GLLayerStack
from Katana import NodegraphAPI, Utils, PrefNames, KatanaPrefs, UI4
from UI4.App import Tabs
from Utils2 import nodegraphutils, widgetutils, nodeutils
from Utils2.nodealignutils import AlignUtils
from .AbstractGestureLayer import (
    AbstractGestureLayer,
    insertLayerIntoNodegraph
)

LAYER_NAME = "Node Iron Layer"
ATTR_NAME = "_node_iron_layer"


class NodeIronLayer(AbstractGestureLayer):
    """

    Attributes:
        cursor_trajectory (NodeIronLayer.DIRECTION): direction to position the nodes
        last_cursor_points (list): of QPoints that hold the last 5 cursor positions
            This is used for calculating the cursors trajectory
        _node_iron_aligned_nodes (list): of nodes that have been aligned
        _node_iron_active (bool): determines if this event is active or not
        _node_iron_finishing (bool): determines if the link cutting event is finishing
            This is useful to differentiate between a A+LMB and a A-Release event
    """

    def __init__(self, *args, **kwargs):
        super(NodeIronLayer, self).__init__(*args, **kwargs)
        if not hasattr(widgetutils.katanaMainWindow(), "_node_iron_finishing"):
            widgetutils.katanaMainWindow()._node_iron_finishing = False

        if not hasattr(widgetutils.katanaMainWindow(), "_node_iron_aligned_nodes"):
            widgetutils.katanaMainWindow()._node_iron_aligned_nodes = []

        if not hasattr(widgetutils.katanaMainWindow(), "_node_iron_active"):
            widgetutils.katanaMainWindow()._node_iron_active = False

    def getAlignedNodes(self):
        return widgetutils.katanaMainWindow()._node_iron_aligned_nodes

    def getAlignXPos(self):
        return NodegraphAPI.GetNodePosition(self.getAlignedNodes()[-1])[0]

    def getAlignYPos(self):
        return NodegraphAPI.GetNodePosition(self.getAlignedNodes()[-1])[1]

    def paintGL(self):
        if widgetutils.katanaMainWindow()._node_iron_active:
            # create point on cursor
            mouse_pos = self.layerStack().getMousePos()
            # align nodes
            if mouse_pos:
                # set initial trajectory
                if len(self.getAlignedNodes()) == 0:
                    if 1 < len(self.getCursorPoints()):
                        self._cursor_trajectory = nodegraphutils.getCursorTrajectory(self.getCursorPoints()[0], self.getCursorPoints()[-1])

                # draw crosshair
                self.drawCrosshair()

                # draw trajectory
                self.drawTrajectory()

                # iron nodes
                if 0 < len(self.getCursorPoints()):
                    hit_points = nodegraphutils.interpolatePoints(self.getCursorPoints()[-1], mouse_pos, radius=self.crosshairRadius(), step_size=5)
                    node_hits = nodegraphutils.pointsHitTestNode(hit_points, self.layerStack(), hit_type=nodegraphutils.NODE)

                    for node in node_hits:
                        # first node
                        if node not in self.getAlignedNodes():
                            if len(self.getAlignedNodes()) == 0:
                                if KatanaPrefs[PrefNames.NODEGRAPH_GRIDSNAP]:
                                    from Utils2.nodealignutils import AlignUtils
                                    AlignUtils().snapNodeToGrid(node)

                            # set direction
                            if len(self.getAlignedNodes()) == 1:
                                self._cursor_trajectory = nodegraphutils.getCursorTrajectory(self.getCursorPoints()[0], self.getCursorPoints()[-1])

                            # iron node
                            if 0 < len(self.getAlignedNodes()):
                                from .gridLayer import (
                                    GRID_SIZE_X_PREF_NAME, GRID_SIZE_Y_PREF_NAME, ALIGN_X_OFFSET_PREF_NAME, ALIGN_Y_OFFSET_PREF_NAME)

                                offset_x = KatanaPrefs[GRID_SIZE_X_PREF_NAME] * KatanaPrefs[ALIGN_X_OFFSET_PREF_NAME]
                                offset_y = KatanaPrefs[GRID_SIZE_Y_PREF_NAME] * KatanaPrefs[ALIGN_Y_OFFSET_PREF_NAME]

                                if self.getCursorTrajectory() == nodegraphutils.RIGHT:
                                    xpos = self.getAlignXPos() + offset_x
                                    ypos = self.getAlignYPos()
                                if self.getCursorTrajectory() == nodegraphutils.LEFT:
                                    xpos = self.getAlignXPos() - offset_x
                                    ypos = self.getAlignYPos()
                                if self.getCursorTrajectory() == nodegraphutils.UP:
                                    xpos = self.getAlignXPos()
                                    ypos = self.getAlignYPos() + offset_y
                                if self.getCursorTrajectory() == nodegraphutils.DOWN:
                                    xpos = self.getAlignXPos()
                                    ypos = self.getAlignYPos() - offset_y

                                try:
                                    NodegraphAPI.SetNodePosition(node, (xpos, ypos))
                                except AttributeError:
                                    # node marked for deletion
                                    pass

                            self.getAlignedNodes().append(node)

                self.addCursorPoint(mouse_pos)

""" EVENTS"""
def nodeInteractionEvent(func):
    """ Each event type requires calling its own private methods
    Doing this will probably just obfuscate the shit out of the code...
    """
    def __nodeInteractionEvent(self, event):
        if event.type() == QEvent.MouseButtonPress:
            if nodeInteractionMousePressEvent(self, event): return True
        if event.type() == QEvent.MouseButtonRelease:
            if nodeInteractionMouseReleaseEvent(self, event): return True
        if event.type() == QEvent.MouseMove:
            if nodeInteractionMouseMoveEvent(self, event): return True

        return func(self, event)

    return __nodeInteractionEvent


def nodeInteractionMouseMoveEvent(self, event):
    # update node iron
    if widgetutils.katanaMainWindow()._node_iron_active:
        self.layerStack().idleUpdate()

    return False


def nodeInteractionMousePressEvent(self, event):
    # start iron
    if (
        event.modifiers() == Qt.NoModifier
        and event.button() == Qt.LeftButton
        and nodegraphutils.getCurrentKeyPressed() == Qt.Key_A
    ):
        Utils.UndoStack.OpenGroup("Align Nodes")
        # ensure that iron was deactivated (because I code bad)
        widgetutils.katanaMainWindow()._node_iron_finishing = False
        self.layerStack().getLayerByName("Node Iron Layer").resetCursorPoints()
        widgetutils.katanaMainWindow()._node_iron_aligned_nodes = []

        # activate iron
        widgetutils.katanaMainWindow()._node_iron_active = True
        QApplication.setOverrideCursor(Qt.BlankCursor)
        nodeutils.removeNodePreviewColors()

        return True

    return False


def nodeInteractionMouseReleaseEvent(self, event):
    # reset node iron attrs
    if widgetutils.katanaMainWindow()._node_iron_active:
        def deactiveNodeIron():
            """ Need to run a delayed timer here, to ensure that when
            the user lifts up the A+LMB, that it doesn't accidently
            register a AlignMenu on release because they have slow fingers"""
            widgetutils.katanaMainWindow()._node_iron_finishing = False
            delattr(self, "_timer")

        widgetutils.katanaMainWindow()._node_iron_finishing = True
        # if only one node is ironed, then automatically do an align upstream/downstream depending
        # on the direction of the swipe
        ironed_nodes = widgetutils.katanaMainWindow()._node_iron_aligned_nodes
        if len(ironed_nodes) == 1:
            nodegraphutils.selectNodes(ironed_nodes, True)
            iron_layer = self.layerStack().getLayerByName("Node Iron Layer")
            trajectory = iron_layer.getCursorTrajectory()
            if trajectory in [nodegraphutils.UP, nodegraphutils.RIGHT]:
                AlignUtils().alignUpstreamNodes()
            elif trajectory in [nodegraphutils.DOWN, nodegraphutils.LEFT]:
                AlignUtils().alignDownstreamNodes()

        # iron nodes
        if 1 < len(ironed_nodes):
            nodegraphutils.floatNodes(widgetutils.katanaMainWindow()._node_iron_aligned_nodes)

        self._timer = QTimer()
        self._timer.start(500)
        self._timer.timeout.connect(deactiveNodeIron)

        # deactive iron
        self.layerStack().getLayerByName("Node Iron Layer").resetCursorPoints()
        widgetutils.katanaMainWindow()._node_iron_active = False
        widgetutils.katanaMainWindow()._node_iron_aligned_nodes = []
        QApplication.restoreOverrideCursor()

        self.layerStack().idleUpdate()

        # QApplication.processEvents()
        Utils.UndoStack.CloseGroup()

    # update view
    self.layerStack().idleUpdate()
    return False


def nodeInteractionKeyPressEvent(func):
    def __nodeInteractionKeyPressEvent(self, event):
        if event.key() == Qt.Key_A and event.modifiers() == Qt.NoModifier:
            if event.isAutoRepeat(): return True
            nodegraphutils.setCurrentKeyPressed(event.key())
            return True

        return func(self, event)

    return __nodeInteractionKeyPressEvent


def installNodeIronLayer(**kwargs):
    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()
    insertLayerIntoNodegraph(NodeIronLayer, LAYER_NAME, ATTR_NAME)

    # install events
    node_interaction_layer = nodegraph_widget.getLayerByName("NodeInteractions")
    node_interaction_layer.__class__.processEvent = nodeInteractionEvent(node_interaction_layer.__class__.processEvent)
    node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress = nodeInteractionKeyPressEvent(
        node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress)