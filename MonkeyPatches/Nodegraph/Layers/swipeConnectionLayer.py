""" The iron node layer allows users to "iron" their nodes

As the user swipes through nodes using CTRL+ALT+SHIFT+LMB, all
of the nodes hit will be aligned to the first node, based off
of the direction of the cursor as it passed through the second node.

"""
import math

from OpenGL.GL import (
    glBegin,
    glLineWidth,
    GL_POINTS,
    GL_LINES,
    glRotatef,
    GL_LINE_LOOP,
    GL_LINE_STRIP,
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
from .AbstractGestureLayer import (
    AbstractGestureLayer,
    insertLayerIntoNodegraph)


LAYER_NAME = "Swipe Connection Layer"
ATTR_NAME = "_swipe_connection_layer"

class SwipeConnectionLayer(AbstractGestureLayer):
    """

    Attributes:
        cursor_trajectory (SwipeConnectionLayer.DIRECTION): direction to position the nodes
        last_cursor_points (list): of QPoints that hold the last 5 cursor positions
            This is used for calculating the cursors trajectory
        _swipe_connection_active (bool): determines if this event is active or not
        _swipe_connection_finishing (bool): determines if the link cutting event is finishing
            This is useful to differentiate between a C+LMB and a C-Release event
    """

    def __init__(self, *args, **kwargs):
        super(SwipeConnectionLayer, self).__init__(*args, **kwargs)
        if not hasattr(widgetutils.katanaMainWindow(), "_swipe_connection_finishing"):
            widgetutils.katanaMainWindow()._swipe_connection_finishing = False
        if not hasattr(widgetutils.katanaMainWindow(), "_swipe_connection_active"):
            widgetutils.katanaMainWindow()._swipe_connection_active = False
        if not hasattr(widgetutils.katanaMainWindow(), "_swipe_connection_nodes"):
            widgetutils.katanaMainWindow()._swipe_connection_nodes = []

    def getConnectedNodes(self):
        return widgetutils.katanaMainWindow()._swipe_connection_nodes

    def addConnectedNode(self, node):
        self.getConnectedNodes().append(node)

    def resetConnectedNodes(self):
        widgetutils.katanaMainWindow()._swipe_connection_nodes = []

    def paintGL(self):
        if widgetutils.katanaMainWindow()._swipe_connection_active:
            # create point on cursor
            mouse_pos = self.layerStack().getMousePos()
            # align nodes
            if mouse_pos:
                self.drawCrosshair()
                self.drawTrajectory()

                # connect nodes
                if 0 < len(self.getCursorPoints()):
                    hit_points = nodegraphutils.interpolatePoints(self.getCursorPoints()[-1], mouse_pos, radius=self.crosshairRadius(), step_size=5)
                    node_hits = nodegraphutils.pointsHitTestNode(hit_points, self.layerStack(), hit_type=nodegraphutils.NODE)
                    for node in node_hits:
                        if len(self.getConnectedNodes()) == 0:
                            self.addConnectedNode(node)
                        elif node not in self.getConnectedNodes():
                            input_port = nodeutils.getFirstEmptyPort(node, force_create=True)
                            if input_port:
                                input_port.connect(self.getConnectedNodes()[-1].getOutputPortByIndex(0))
                            else:
                                self.getConnectedNodes()[-1].getOutputPortByIndex(0).connect(node.getInputPortByIndex(0))
                            self.addConnectedNode(node)

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


def nodeInteractionMouseReleaseEvent(self, event):
    # reset node iron attrs
    if widgetutils.katanaMainWindow()._swipe_connection_active:
        def deactivateSwipeConnector():
            """ Need to run a delayed timer here, to ensure that when
            the user lifts up the A+LMB, that it doesn't accidently
            register a AlignMenu on release because they have slow fingers"""
            widgetutils.katanaMainWindow()._swipe_connection_finishing = False
            delattr(self, "_timer")

        widgetutils.katanaMainWindow()._swipe_connection_finishing = True

        # start deactivation timer
        self._timer = QTimer()
        self._timer.start(500)
        self._timer.timeout.connect(deactivateSwipeConnector)

        # deactive link cutting
        self.layerStack().getLayerByName("Swipe Connection Layer").resetCursorPoints()
        widgetutils.katanaMainWindow()._swipe_connection_active = False
        widgetutils.katanaMainWindow()._swipe_connection_nodes = []
        QApplication.restoreOverrideCursor()

        self.layerStack().idleUpdate()

        # QApplication.processEvents()
        Utils.UndoStack.CloseGroup()

    # update view
    self.layerStack().idleUpdate()
    return False


def nodeInteractionMouseMoveEvent(self, event):
    # update node iron
    if widgetutils.katanaMainWindow()._swipe_connection_active:
        self.layerStack().idleUpdate()

    return False


def nodeInteractionMousePressEvent(self, event):
    # start link cutting
    if (
        event.modifiers() == Qt.NoModifier
        and event.button() == Qt.LeftButton
        and nodegraphutils.getCurrentKeyPressed() == Qt.Key_C
    ):
        Utils.UndoStack.OpenGroup("Connect Nodes")
        # ensure that iron was deactivated (because I code bad)
        widgetutils.katanaMainWindow()._swipe_connection_finishing = False
        self.layerStack().getLayerByName("Swipe Connection Layer").resetCursorPoints()

        # activate iron
        widgetutils.katanaMainWindow()._swipe_connection_active = True
        QApplication.setOverrideCursor(Qt.BlankCursor)
        nodeutils.removeNodePreviewColors()

        return True

    return False


def nodeInteractionKeyPressEvent(func):
    def __nodeInteractionKeyPressEvent(self, event):
        if event.key() == Qt.Key_C and event.modifiers() == Qt.NoModifier:
            if event.isAutoRepeat(): return True
            nodegraphutils.setCurrentKeyPressed(event.key())
            return True

        return func(self, event)

    return __nodeInteractionKeyPressEvent


def installSwipeConnectionLayer(**kwargs):
    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()
    insertLayerIntoNodegraph(SwipeConnectionLayer, LAYER_NAME, ATTR_NAME)
    # install events
    node_interaction_layer = nodegraph_widget.getLayerByName("NodeInteractions")
    node_interaction_layer.__class__.processEvent = nodeInteractionEvent(node_interaction_layer.__class__.processEvent)
    node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress = nodeInteractionKeyPressEvent(
        node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress)