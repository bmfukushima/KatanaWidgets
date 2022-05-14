""" Todo:
        - Extract paintGL layer into API
            Provide a list of hits for gesture connection layers to use
        - Move this into one layer, which is called and updated, rather than the multiple layers

"""

from OpenGL.GL import (
    glBegin,
    glLineWidth,
    GL_LINE_LOOP,
    GL_LINE_STRIP,
    glColor4f,
    glEnd,
    glVertex2f,
)
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt, QPoint, QEvent, QTimer, QSize

from Katana import Utils
import QT4GLLayerStack
from UI4.App import Tabs

from Utils2 import nodegraphutils, widgetutils, nodeutils


class AbstractGestureLayer(QT4GLLayerStack.Layer):
    """

    Attributes:
        actuation_key (Qt.KEY): key pressed to start the swipe event
        name (str): name of attribute stored on katana main window
            All additional attrs will be stored under <name>_<someattr>
        color (RGBA0-1) Tuple of rgba 0-1 values
        crosshair_radius (QSize): X/Y radius of crosshair
        cursor_trajectory (LinkCuttingLayer.DIRECTION): direction to position the nodes
        last_cursor_points (list): of QPoints that hold the last 5 cursor positions
            This is used for calculating the cursors trajectory
        <name>_active (bool): determines if this event is active or not
        <name>_finishing (bool): determines if the link cutting event is finishing
            This is useful to differentiate between a C+LMB and a C-Release event
        <name>_hits (list): of objects that are hit.  This list is usually populate
            during the paintGL event, when a cursor comes into contact with an object
        _nodegraph_gesture_layers (set): of strings of gesture <name>
        undo_name (str): Name to be put into the undo stack
    """

    def __init__(self, *args, name="_abstract_gesture", actuation_key=None, undo_name="Nodegraph Swipe Gesture", **kwargs):
        (QT4GLLayerStack.Layer.__init__)(self, *args, **kwargs)

        # setup default attrs
        self._actuation_key = actuation_key
        self._color = (0.75, 0.75, 1, 1)
        self._crosshair_radius = QSize(10, 10)
        self._cursor_trajectory = nodegraphutils.RIGHT
        self._last_cursor_points = []
        self._undo_name = undo_name

        katana_main_widget = widgetutils.katanaMainWindow()
        self._name = name
        if not hasattr(katana_main_widget, f"{name}_finishing"):
            setattr(katana_main_widget, f"{name}_finishing", False)
        if not hasattr(katana_main_widget, f"{name}_active"):
            setattr(katana_main_widget, f"{name}_active", False)
        if not hasattr(katana_main_widget, f"{name}_hits"):
            setattr(katana_main_widget, f"{name}_hits", [])
        if not hasattr(katana_main_widget, "_nodegraph_gesture_layers"):
            setattr(katana_main_widget, "_nodegraph_gesture_layers", set())

        AbstractGestureLayer.addGestureLayer(name)

    """ PROPERTIES """
    def actuationKey(self):
        return self._actuation_key

    def name(self):
        return self._name

    def isActive(self):
        return getattr(widgetutils.katanaMainWindow(), self.name() + "_active")

    def setIsActive(self, is_active):
        return setattr(widgetutils.katanaMainWindow(), self.name() + "_active", is_active)

    def isFinishing(self):
        return getattr(widgetutils.katanaMainWindow(), self.name() + "_finishing")

    def setIsFinishing(self, is_finishing):
        setattr(widgetutils.katanaMainWindow(), self.name() + "_finishing", is_finishing)
        if is_finishing:
            self._timer = QTimer()
            self._timer.start(500)
            self._timer.timeout.connect(self.deactivateGestureEvent)
        else:
            if hasattr(self, "_timer"):
                delattr(self, "_timer")

    def addCursorPoint(self, point):
        self._last_cursor_points.append(point)

        if 5 < len(self._last_cursor_points):
            self._last_cursor_points = self._last_cursor_points[-5:]

    def getCursorPoints(self):
        return self._last_cursor_points

    def resetCursorPoints(self):
        self._last_cursor_points = []

    def getHits(self):
        return getattr(widgetutils.katanaMainWindow(), self.name() + "_hits")

    def addHit(self, hit):
        self.getHits().append(hit)

    def resetHits(self):
        setattr(widgetutils.katanaMainWindow(), self.name() + "_hits", [])

    def color(self):
        return self._color

    def setColor(self, color):
        self._color = color

    def crosshairRadius(self):
        return self._crosshair_radius

    def setCrosshairRadius(self, crosshair_radius):
        self._crosshair_radius = crosshair_radius

    def undoName(self):
        return self._undo_name

    """ UTILS"""
    @staticmethod
    def addGestureLayer(name):
        """ Adds a gesture layer to the registry.

        These are stored as strings of the name"""
        gesture_layers = getattr(widgetutils.katanaMainWindow(), "_nodegraph_gesture_layers")
        gesture_layers.add(name)

    @staticmethod
    def isGestureLayerActive():
        """ Determines if a gesture layer is currently active

        Returns (bool)"""
        gesture_layers = getattr(widgetutils.katanaMainWindow(), "_nodegraph_gesture_layers")
        for layer_name in gesture_layers:
            if getattr(widgetutils.katanaMainWindow(), f"{layer_name}_active"): return True
        return False

    def drawCrosshair(self):
        """ Draws the crosshair at the current position on the screen"""
        glColor4f(*self.color())
        glLineWidth(2)

        mouse_pos = self.layerStack().getMousePos()
        window_pos = QPoint(mouse_pos.x(), self.layerStack().getWindowSize()[1] - mouse_pos.y())
        glBegin(GL_LINE_LOOP)
        glVertex2f(window_pos.x() - self.crosshairRadius().width(), window_pos.y())
        glVertex2f(window_pos.x(), window_pos.y() + self.crosshairRadius().height())
        glVertex2f(window_pos.x() + self.crosshairRadius().width(), window_pos.y())
        glVertex2f(window_pos.x(), window_pos.y() - self.crosshairRadius().height())
        glEnd()

    def drawTrajectory(self):
        """ Draws the trail behind the cross hair"""
        glColor4f(*self.color())
        glLineWidth(2)

        # get trajectory
        if 0 < len(self.getCursorPoints()):
            glBegin(GL_LINE_STRIP)
            for point in self.getCursorPoints():
                glVertex2f(point.x(), self.layerStack().getWindowSize()[1] - point.y())
            glEnd()

    def resetAttrs(self):
        self.setIsFinishing(True)

        # deactivate gesture
        self.resetCursorPoints()
        self.setIsActive(False)
        self.resetHits()
        nodegraphutils.setCurrentKeyPressed(None)

    """ EVENTS """
    def deactivateGestureEvent(self):
        """ Need to run a delayed timer here, to ensure that when
        the user lifts up the A+LMB, that it doesn't accidently
        register a AlignMenu on release because they have slow fingers"""
        self.setIsFinishing(False)

    def processEvent(self, event):
        if event.type() == QEvent.MouseMove:
            self.mouseMoveEvent(event)
        if event.type() == QEvent.MouseButtonPress:
            if self.mousePressEvent(event): return True
        if event.type() == QEvent.MouseButtonRelease:
            if self.mouseReleaseEvent(event): return True
        if event.type() == QEvent.KeyRelease:
            if self.shouldProcessKeyReleaseEvent(event):
                if self.keyReleaseEvent(event): return True
        return QT4GLLayerStack.Layer.processEvent(self, event)

    def keyReleaseEvent(self, event):
        return False

    def shouldProcessKeyReleaseEvent(self, event):
        """ Determines if a key release event should be processed or not.

        This is necessary as events are triggered on release, as press may behave
        differently"""
        if event.isAutoRepeat(): return False
        if event.key() == self.actuationKey() and event.modifiers() == Qt.NoModifier:
            if not getattr(widgetutils.katanaMainWindow(), self.name() + "_finishing"):
                return True
        if event.key() in [Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Control]:
            self.setIsFinishing(True)
        return False

    def mouseMoveEvent(self, event):
        # update cursor display
        if self.isActive():
            self.layerStack().idleUpdate()

        return False

    def mousePressEvent(self, event):
        """ Activates the gestural event"""
        if self.isActive(): return True
        if not self.actuationKey(): return False
        if (
                event.modifiers() == Qt.NoModifier
                and event.button() == Qt.LeftButton
                and nodegraphutils.getCurrentKeyPressed() == self.actuationKey()
        ):
            # todo setup activation handler
            Utils.UndoStack.OpenGroup(self.undoName())
            # ensure that everything was turned off... because sometimes I do stuff bad
            self.setIsFinishing(False)
            self.resetCursorPoints()
            self.resetHits()

            # activate swipe gesture
            self.setIsActive(True)
            QApplication.setOverrideCursor(Qt.BlankCursor)
            nodeutils.clearNodePreviewColors()
            return True

        return False

    def mouseReleaseEvent(self, event):
        # reset layer attrs
        if self.isActive():
            self.resetAttrs()

            QApplication.restoreOverrideCursor()

            self.layerStack().idleUpdate()

            nodeutils.clearNodePreviewColors()
            # todo setup deactivation handler

            Utils.UndoStack.CloseGroup()

        # update view
        self.layerStack().idleUpdate()

        return False


def insertLayerIntoNodegraph(layer_type, name, actuation_key, undo_name):
    """ Returns a function that can be used to override the NodegraphWidgets show function
    automatically insert the layer provided into the NodegraphTab

    Args:
        actuation_key (Qt.KEY): key pressed to start the event
        layer_type (AbstractGestureLayer): class of layer to be inserted
        name (str): name of attr to store the layer as on the NodegraphWidget
        """
    def showEvent(func):
        def __showEvent(self, event):
            # disable floating layer, as it for some reason inits as True...
            self.getLayerByName("Floating Nodes").setEnabled(False)
            # name = "_abstract_gesture_layer",
            # actuation_key = None,
            # undo_name = "Abstract Gesture Event",
            # setup grid layer
            gesture_layer = self.getLayerByName(name)
            if not gesture_layer:
                gesture_layer = layer_type(
                    name, actuation_key=actuation_key, name=name, enabled=True, undo_name=undo_name)
                setattr(self, name + "_layer", gesture_layer)
                self.appendLayer(gesture_layer)

                # todo NMC gesture layer (events)
                def processEvent(func):
                    def __processEvent(self, event):
                        # if event.type() == QEvent.MouseMove:
                        #     gesture_layer.mouseMoveEvent(event)
                        # if event.type() == QEvent.MouseButtonPress:
                        #     if gesture_layer.mousePressEvent(event): return True
                        # if event.type() == QEvent.MouseButtonRelease:
                        #     if gesture_layer.mouseReleaseEvent(event): return True
                        if event.type() == QEvent.KeyRelease:
                            if gesture_layer.shouldProcessKeyReleaseEvent(event):
                                if gesture_layer.keyReleaseEvent(event): return True
                        return func(self, event)

                    return __processEvent
                #
                nodegraph_view_interaction_layer = nodegraph_widget.getLayerByName("NodeGraphViewInteraction")
                nodegraph_view_interaction_layer.__class__.processEvent = processEvent(nodegraph_view_interaction_layer.__class__.processEvent)

            return func(self, event)

        return __showEvent

    def nodeInteractionKeyPressEvent(func):
        def __nodeInteractionKeyPressEvent(self, event):
            if event.key() == actuation_key and event.modifiers() == Qt.NoModifier:
                if event.isAutoRepeat(): return True
                nodegraphutils.setCurrentKeyPressed(event.key())
                return True

            return func(self, event)

        return __nodeInteractionKeyPressEvent

    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()
    nodegraph_widget.__class__.showEvent = showEvent(nodegraph_widget.__class__.showEvent)

    node_interaction_layer = nodegraph_widget.getLayerByName("NodeInteractions")
    node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress = nodeInteractionKeyPressEvent(
        node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress)

    nodegraph_view_interaction_layer = nodegraph_widget.getLayerByName("NodeGraphViewInteraction")
    nodegraph_view_interaction_layer.__class__._NodeGraphViewInteractionLayer__processKeyPress = nodeInteractionKeyPressEvent(
        nodegraph_view_interaction_layer.__class__._NodeGraphViewInteractionLayer__processKeyPress)
    return showEvent
