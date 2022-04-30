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
from Utils2 import nodegraphutils, widgetutils
from Utils2.nodealignutils import AlignUtils

class LinkCuttingLayer(QT4GLLayerStack.Layer):
    """

    Attributes:
        cursor_trajectory (LinkCuttingLayer.DIRECTION): direction to position the nodes
        last_cursor_points (list): of QPoints that hold the last 5 cursor positions
            This is used for calculating the cursors trajectory
        _link_cutting_active (bool): determines if this event is active or not
        _link_cutting_finishing (bool): determines if the link cutting event is finishing
            This is useful to differentiate between a C+LMB and a C-Release event
    """

    def __init__(self, *args, **kwargs):
        (QT4GLLayerStack.Layer.__init__)(self, *args, **kwargs)
        self._cursor_trajectory = nodegraphutils.RIGHT
        self._last_cursor_points = []
        if not hasattr(widgetutils.katanaMainWindow(), "_link_cutting_finishing"):
            widgetutils.katanaMainWindow()._link_cutting_finishing = False

        if not hasattr(widgetutils.katanaMainWindow(), "_link_cutting_active"):
            widgetutils.katanaMainWindow()._link_cutting_active = False

    def addCursorPoint(self, point):
        self._last_cursor_points.append(point)

        if 5 < len(self._last_cursor_points):
            self._last_cursor_points = self._last_cursor_points[-5:]

    def getCursorPoints(self):
        return self._last_cursor_points

    def resetCursorPoints(self):
        self._last_cursor_points = []

    def getCursorTrajectory(self):
        """ Returns the direction that the cursor is currently travelling

        Returns (LinkCuttingLayer.DIRECTION)"""

        return self._cursor_trajectory

    def paintGL(self):
        if widgetutils.katanaMainWindow()._link_cutting_active:
            # create point on cursor
            mouse_pos = self.layerStack().getMousePos()
            # align nodes
            if mouse_pos:
                # get attrs
                window_pos = QPoint(mouse_pos.x(), self.layerStack().getWindowSize()[1] - mouse_pos.y())
                radius = 10
                glColor4f(0.75, 0.75, 1, 1)
                # glColor4f(1, 1, 0, 1)
                glPointSize(1)
                glLineWidth(2)

                # draw crosshair
                glBegin(GL_LINE_LOOP)
                glVertex2f(window_pos.x() - radius, window_pos.y())
                glVertex2f(window_pos.x(), window_pos.y() + radius)
                glVertex2f(window_pos.x() + radius, window_pos.y())
                glVertex2f(window_pos.x(), window_pos.y() - radius)
                glEnd()

                # get trajectory
                if 0 < len(self.getCursorPoints()):
                    glBegin(GL_LINE_STRIP)
                    for point in self.getCursorPoints():
                        glVertex2f(point.x(), self.layerStack().getWindowSize()[1] - point.y())
                    glEnd()

                # iron nodes
                if 0 < len(self.getCursorPoints()):
                    hit_points = nodegraphutils.interpolatePoints(self.getCursorPoints()[-1], mouse_pos, radius=radius, step_size=5)
                    link_hits = nodegraphutils.pointsHitTestNode(hit_points, self.layerStack(), hit_type=nodegraphutils.LINK)
                    for link in link_hits:
                        link[0].disconnect(link[1])

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
    if widgetutils.katanaMainWindow()._link_cutting_active:
        def deactivateLinkCutter():
            """ Need to run a delayed timer here, to ensure that when
            the user lifts up the A+LMB, that it doesn't accidently
            register a AlignMenu on release because they have slow fingers"""
            widgetutils.katanaMainWindow()._link_cutting_finishing = False
            delattr(self, "_timer")

        widgetutils.katanaMainWindow()._link_cutting_finishing = True

        # start deactivation timer
        self._timer = QTimer()
        self._timer.start(500)
        self._timer.timeout.connect(deactivateLinkCutter)

        # deactive link cutting
        self.layerStack().getLayerByName("Link Cutting Layer").resetCursorPoints()
        widgetutils.katanaMainWindow()._link_cutting_active = False
        QApplication.restoreOverrideCursor()

        self.layerStack().idleUpdate()

        # QApplication.processEvents()
        Utils.UndoStack.CloseGroup()

    # update view
    self.layerStack().idleUpdate()
    return False


def nodeInteractionMouseMoveEvent(self, event):
    # update node iron
    if widgetutils.katanaMainWindow()._link_cutting_active:
        self.layerStack().idleUpdate()

    return False


def nodeInteractionMousePressEvent(self, event):
    # start link cutting
    if (
        event.modifiers() == Qt.NoModifier
        and event.button() == Qt.LeftButton
        and nodegraphutils.getCurrentKeyPressed() == Qt.Key_C
    ):
        Utils.UndoStack.OpenGroup("Cut Links")
        # ensure that iron was deactivated (because I code bad)
        widgetutils.katanaMainWindow()._link_cutting_finishing = False
        self.layerStack().getLayerByName("Link Cutting Layer").resetCursorPoints()

        # activate iron
        widgetutils.katanaMainWindow()._link_cutting_active = True
        QApplication.setOverrideCursor(Qt.BlankCursor)

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


def showEvent(func):
    def __showEvent(self, event):
        # disable floating layer, as it for some reason inits as True...
        self.getLayerByName("Floating Nodes").setEnabled(False)

        # setup grid layer
        node_iron_layer = self.getLayerByName("Link Cutting Layer")
        if not node_iron_layer:
            self._link_cutting_layer = LinkCuttingLayer("Link Cutting Layer", enabled=True)
            self.appendLayer(self._link_cutting_layer)
        return func(self, event)

    return __showEvent


def installLinkCuttingLayer(**kwargs):
    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()
    nodegraph_widget.__class__.showEvent = showEvent(nodegraph_widget.__class__.showEvent)

    # install events
    node_interaction_layer = nodegraph_widget.getLayerByName("NodeInteractions")
    node_interaction_layer.__class__.processEvent = nodeInteractionEvent(node_interaction_layer.__class__.processEvent)
    node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress = nodeInteractionKeyPressEvent(
        node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress)