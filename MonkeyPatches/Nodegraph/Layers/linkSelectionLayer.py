""" The link selection layer allows the user to swipe through links to select them."""

from qtpy.QtCore import Qt, QEvent

from OpenGL.GL import glBegin, glEnd, GL_LINES, glVertex2f, glLineWidth, glColor4f

from Katana import Utils, DrawingModule
from UI4.Tabs.NodeGraphTab.Layers.LinkConnectionLayer import LinkConnectionLayer

from Utils2 import nodegraphutils, widgetutils
from .AbstractGestureLayer import AbstractGestureLayer, insertLayerIntoNodegraph


OUTPUT_PORT = 0
INPUT_PORT = 1
ATTR_NAME = "_link_selection"

class AbstractLinkSelectionLayer(AbstractGestureLayer):
    """
    Attributes:
        cursor_trajectory (LinkCuttingLayer.DIRECTION): direction to position the nodes
        last_cursor_points (list): of QPoints that hold the last 5 cursor positions
            This is used for calculating the cursors trajectory
        _link_cutting_active (bool): determines if this event is active or not
        _link_cutting_finishing (bool): determines if the link cutting event is finishing
            This is useful to differentiate between a C+LMB and a C-Release event
        selection_type (PORT_TYPE): the type of port that is currently being selected
            OUTPUT_PORT | INPUT_PORT
        selection_event_type (AbstractLinkSelectionLayer.TYPE): the type of event selected,
            if its a remove, or append event
    """
    REMOVE = 0
    APPEND = 1

    def __init__(self, *args, **kwargs):
        super(AbstractLinkSelectionLayer, self).__init__(*args, **kwargs)

        if not hasattr(widgetutils.katanaMainWindow(), "{ATTR_NAME}_current_selection".format(ATTR_NAME=ATTR_NAME)):
            setattr(widgetutils.katanaMainWindow(), "{ATTR_NAME}_current_selection".format(ATTR_NAME=ATTR_NAME), dict())

        self._selection_type = INPUT_PORT

    """ SELECTION ATTR"""
    @staticmethod
    def clearSelection():
        setattr(widgetutils.katanaMainWindow(), "{ATTR_NAME}_current_selection".format(ATTR_NAME=ATTR_NAME), dict())

    @staticmethod
    def currentSelection():
        return getattr(widgetutils.katanaMainWindow(), "{ATTR_NAME}_current_selection".format(ATTR_NAME=ATTR_NAME))

    @staticmethod
    def setCurrentSelection(selection):
        setattr(widgetutils.katanaMainWindow(), "{ATTR_NAME}_current_selection".format(ATTR_NAME=ATTR_NAME), selection)

    @staticmethod
    def appendSelection(selection):
        AbstractLinkSelectionLayer.currentSelection().update(selection)

    @staticmethod
    def removeSelection(selection):
        current_selection = AbstractLinkSelectionLayer.currentSelection()
        for item in selection:
            if item in current_selection:
                del current_selection[item]
                # current_selection.remove(item)
        AbstractLinkSelectionLayer.setCurrentSelection(current_selection)

    def updateSelection(self, ports):
        if self.selectionEventType() == AbstractLinkSelectionLayer.APPEND:
            AbstractLinkSelectionLayer.appendSelection(ports)
        elif self.selectionEventType() == AbstractLinkSelectionLayer.REMOVE:
            AbstractLinkSelectionLayer.removeSelection(ports)

    """ UTILS """
    def selectionEventType(self):
        return self._selection_event_type

    def setSelectionEventType(self, event_type):
        self._selection_event_type = event_type

    def selectionType(self):
        return self._selection_type

    def setSelectionType(self, selection_type):
        self._selection_type = selection_type

    """ VIRTUAL FUNCTIONS"""
    def activateGestureEvent(self, selection_event_type=APPEND, clear_data=True):
        self.setSelectionEventType(selection_event_type)
        AbstractGestureLayer.activateGestureEvent(self, clear_data=clear_data)

    def deactivateGestureEvent(self):
        # AbstractLinkSelectionLayer.clearSelection()
        AbstractGestureLayer.deactivateGestureEvent(self)

    def mousePressEvent(self, event):
        AbstractLinkSelectionLayer.clearSelection()
        return AbstractGestureLayer.mousePressEvent(self, event)

    def showNoodles(self, ports):
        nodegraph_widget = widgetutils.getActiveNodegraphWidget()
        layer = LinkConnectionLayer(ports, None, enabled=True)
        nodegraph_widget.appendLayer(layer, stealFocus=True)

    def paintGL(self):
        if self.isActive():
            # create point on cursor
            mouse_pos = self.layerStack().getMousePos()
            # align nodes
            if mouse_pos:
                # draw selected links
                glLineWidth(2)
                glColor4f(0.5, 0.5, 1, 1)
                link_points = []
                for port, link in AbstractLinkSelectionLayer.currentSelection().items():
                    end_points = DrawingModule.nodeWorld_getLinkEndPoints(
                        self.layerStack().getCurrentNodeView(),
                        link[0],
                        link[1],
                        self.layerStack().getViewScale()[0]
                    )

                    link_points.append(self.layerStack().mapFromWorldToWindow(end_points[0][0], end_points[0][1]))
                    link_points.append(self.layerStack().mapFromWorldToWindow(end_points[1][0], end_points[1][1]))

                glBegin(GL_LINES)
                for end_point in link_points:
                    glVertex2f(end_point[0], end_point[1])
                glEnd()

                # draw crosshair
                self.drawCrosshair()
                self.drawTrajectory()

                # get link hits
                # todo update port hits
                # todo no idea why, but something in here is moving the coordinate system... all drawing must be done before this
                # having issue selecting... I think this is something to do with appending ports
                if 0 < len(self.getCursorPoints()):
                    hit_points = nodegraphutils.interpolatePoints(self.getCursorPoints()[-1], mouse_pos, radius=self.crosshairRadius(), step_size=5)
                    link_hits = nodegraphutils.pointsHitTestNode(hit_points, self.layerStack(), hit_type=nodegraphutils.LINK)
                    ports = {}
                    for link in link_hits:
                        for port in link:
                            if port.getType() == self.selectionType():
                                if port not in ports:
                                    ports[port] = link
                    # for link in link_hits:
                    #     print(link)
                    #     # for port in link:
                    #     #     if port.getType() == self.selectionType():
                    #     #         self.updateSelection({port:link})
                    #             # if port not in ports:
                    #             #     ports[port] = link
                    # update port list
                    self.updateSelection(ports)

                self.addCursorPoint(mouse_pos)

class InputLinkSelectionLayer(AbstractLinkSelectionLayer):
    def __init__(self, *args, **kwargs):
        super(InputLinkSelectionLayer, self).__init__(*args, **kwargs)
        self.setSelectionType(INPUT_PORT)

    def mouseReleaseEvent(self, event):
        if self.isActive():
            # show selection
            self.showNoodles(list(AbstractLinkSelectionLayer.currentSelection().keys()))
            widgetutils.katanaMainWindow()._active_nodegraph_widget = widgetutils.getActiveNodegraphWidget()
        return AbstractGestureLayer.mouseReleaseEvent(self, event)


class OutputLinkSelectionLayer(AbstractLinkSelectionLayer):
    def __init__(self, *args, **kwargs):
        super(OutputLinkSelectionLayer, self).__init__(*args, **kwargs)
        self.setSelectionType(OUTPUT_PORT)

    def mouseReleaseEvent(self, event):
        if self.isActive():
            # todo fix sort algo
            # sort ports
            # sorted_ports = []
            # ports = AbstractLinkSelectionLayer.currentSelection()
            # for port in ports:
            #     node = port.getNode()
            #     for output_port in node.getOutputPorts():
            #         if output_port in ports:
            #             sorted_ports.append(output_port)
            #             ports.remove(output_port)

            # show noodles
            self.showNoodles(list(AbstractLinkSelectionLayer.currentSelection().keys()))
            widgetutils.katanaMainWindow()._active_nodegraph_widget = widgetutils.getActiveNodegraphWidget()

        return AbstractGestureLayer.mouseReleaseEvent(self, event)


def linkConnectionEvent(func):
    def __linkConnectionEvent(self, event):
        if event.type() == QEvent.MouseButtonPress:
            if linkConnectionMousePressEvent(self, event): return True

        return func(self, event)

    return __linkConnectionEvent


def linkConnectionMousePressEvent(self, event):
    """ Mouse press event that is activate when the user clicks while having a selection active """
    # append to link selection
    if event.modifiers() in [Qt.ShiftModifier, Qt.ControlModifier]:
        from MonkeyPatches.Nodegraph.portConnector import PortConnector
        link_connection_layer = PortConnector.getLinkConnectionLayer()

        if link_connection_layer:
            # base_ports = link_connection_layer.getBasePorts()
            # AbstractLinkSelectionLayer.setCurrentSelection(base_ports)

            selection_type = PortConnector.selectionType()
            if selection_type == INPUT_PORT:
                layer = self.layerStack().getLayerByName("_input_link_selection")
            elif selection_type == OUTPUT_PORT:
                layer = self.layerStack().getLayerByName("_output_link_selection")

            # hide noodle and activate gesture
            PortConnector.hideNoodle()
            if event.modifiers() == Qt.ShiftModifier:
                layer.activateGestureEvent(selection_event_type=AbstractLinkSelectionLayer.APPEND)
            if event.modifiers() == Qt.ControlModifier:
                layer.activateGestureEvent(selection_event_type=AbstractLinkSelectionLayer.REMOVE)

            """ Need to open a group here, as the AbstractGestureLayer closes on mouse release"""
            Utils.UndoStack.OpenGroup("Link Selection")
            return True

    return False


def linkConnectionMouseMove(self, event):

    return False


def installLinkSelectionLayer(**kwargs):
    insertLayerIntoNodegraph(InputLinkSelectionLayer, "_input_link_selection", Qt.Key_Q, "Select Links")
    insertLayerIntoNodegraph(OutputLinkSelectionLayer, "_output_link_selection", Qt.Key_W, "Select Links")
    LinkConnectionLayer.processEvent = linkConnectionEvent(LinkConnectionLayer.processEvent)