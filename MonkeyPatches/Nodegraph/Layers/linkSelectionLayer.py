""" The iron node layer allows users to "iron" their nodes

As the user swipes through nodes using CTRL+ALT+SHIFT+LMB, all
of the nodes hit will be aligned to the first node, based off
of the direction of the cursor as it passed through the second node.

"""

from qtpy.QtCore import Qt
from UI4.Tabs.NodeGraphTab.Layers.LinkConnectionLayer import LinkConnectionLayer

from Utils2 import nodegraphutils, widgetutils
from .AbstractGestureLayer import AbstractGestureLayer, insertLayerIntoNodegraph


OUTPUT_PORT = 0
INPUT_PORT = 1


class AbstractLinkSelectionLayer(AbstractGestureLayer):
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
        super(AbstractLinkSelectionLayer, self).__init__(*args, **kwargs)

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
                # draw crosshair
                self.drawCrosshair()
                self.drawTrajectory()

                # cut links
                if 0 < len(self.getCursorPoints()):
                    hit_points = nodegraphutils.interpolatePoints(self.getCursorPoints()[-1], mouse_pos, radius=self.crosshairRadius(), step_size=2)
                    link_hits = nodegraphutils.pointsHitTestNode(hit_points, self.layerStack(), hit_type=nodegraphutils.LINK)

                    for link in link_hits:
                        if link not in self.getHits():
                            self.addHit(link)

                self.addCursorPoint(mouse_pos)


class InputLinkSelectionLayer(AbstractLinkSelectionLayer):
    def __init__(self, *args, **kwargs):
        super(InputLinkSelectionLayer, self).__init__(*args, **kwargs)

    def mouseReleaseEvent(self, event):
        if self.isActive():
            ports = []
            for link in self.getHits():
                for port in link:
                    if port.getType() == OUTPUT_PORT:
                        ports.append(port)

            self.showNoodles(ports)
            widgetutils.katanaMainWindow()._active_nodegraph_widget = widgetutils.getActiveNodegraphWidget()
        return AbstractGestureLayer.mouseReleaseEvent(self, event)


class OutputLinkSelectionLayer(AbstractLinkSelectionLayer):
    def __init__(self, *args, **kwargs):
        super(OutputLinkSelectionLayer, self).__init__(*args, **kwargs)

    def mouseReleaseEvent(self, event):
        from MonkeyPatches.Nodegraph.portConnector import PortConnector
        if self.isActive():
            ports = []
            for link in self.getHits():
                for port in link:
                    if port.getType() == INPUT_PORT:
                        ports.append(port)

            self.showNoodles(ports)
            widgetutils.katanaMainWindow()._active_nodegraph_widget = widgetutils.getActiveNodegraphWidget()

        return AbstractGestureLayer.mouseReleaseEvent(self, event)


def installLinkSelectionLayer(**kwargs):
    insertLayerIntoNodegraph(InputLinkSelectionLayer, "_input_link_selection", Qt.Key_Q, "Select Links")
    insertLayerIntoNodegraph(OutputLinkSelectionLayer, "_output_link_selection", Qt.Key_W, "Select Links")