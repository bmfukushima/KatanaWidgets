""" The iron node layer allows users to "iron" their nodes

As the user swipes through nodes using CTRL+ALT+SHIFT+LMB, all
of the nodes hit will be aligned to the first node, based off
of the direction of the cursor as it passed through the second node.
"""
import os
import inspect

from qtpy.QtCore import Qt, QSize

from cgwidgets.widgets import PopupHotkeyMenu

# setup prefs
from Katana import NodegraphAPI, Utils, PrefNames, KatanaPrefs, UI4
from Utils2 import nodegraphutils, widgetutils, nodeutils
from Utils2.nodealignutils import AlignUtils
from .AbstractGestureLayer import (
    AbstractGestureLayer,
    insertLayerIntoNodegraph
)

ATTR_NAME = "_node_iron"


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
        self.setCrosshairRadius(QSize(10, 20))

    def getAlignXPos(self):
        return NodegraphAPI.GetNodePosition(self.getHits()[-1])[0]

    def getAlignYPos(self):
        return NodegraphAPI.GetNodePosition(self.getHits()[-1])[1]

    def getCursorTrajectory(self):
        """ Returns the direction that the cursor is currently travelling

        Returns (LinkCuttingLayer.DIRECTION)"""

        return self._cursor_trajectory

    def keyReleaseEvent(self, event):
        if event.modifiers() == Qt.NoModifier:
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
            file_path = f"{current_dir}/NodeAlignment/AlignNodes.json"
            popup_widget = PopupHotkeyMenu(parent=widgetutils.katanaMainWindow(), file_path=file_path)
            popup_widget.show()
            "/media/ssd02/dev/katana/KatanaWidgets/MonkeyPatches/Nodegraph/Layers/NodeAlignment/AlignNodes.json"
            # need to make sure this releases
            nodegraphutils.setCurrentKeyPressed(None)
        return AbstractGestureLayer.keyReleaseEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.isActive():
            ironed_nodes = self.getHits()
            if len(ironed_nodes) == 1:
                nodegraphutils.selectNodes(ironed_nodes, is_exclusive=True)
                trajectory = self.getCursorTrajectory()
                if trajectory in [nodegraphutils.UP, nodegraphutils.RIGHT]:
                    AlignUtils().alignUpstreamNodes()
                elif trajectory in [nodegraphutils.DOWN, nodegraphutils.LEFT]:
                    AlignUtils().alignDownstreamNodes()

            # iron nodes
            if 1 < len(ironed_nodes):
                nodegraphutils.floatNodes(ironed_nodes)

        return AbstractGestureLayer.mouseReleaseEvent(self, event)

    def paintGL(self):
        if self.isActive():
            # create point on cursor
            mouse_pos = self.layerStack().getMousePos()
            # align nodes
            if mouse_pos:
                # set initial trajectory
                if len(self.getHits()) == 0:
                    if 1 < len(self.getCursorPoints()):
                        self._cursor_trajectory = nodegraphutils.getCursorTrajectory(self.getCursorPoints()[0], self.getCursorPoints()[-1])

                # draw crosshair
                self.drawCrosshair()
                self.drawTrajectory()

                # iron nodes
                if 0 < len(self.getCursorPoints()):
                    hit_points = nodegraphutils.interpolatePoints(self.getCursorPoints()[-1], mouse_pos, radius=self.crosshairRadius(), step_size=5)
                    node_hits = nodegraphutils.pointsHitTestNode(hit_points, self.layerStack(), hit_type=nodegraphutils.NODE)

                    for node in node_hits:
                        # first node
                        if node not in self.getHits():
                            if len(self.getHits()) == 0:
                                if KatanaPrefs[PrefNames.NODEGRAPH_GRIDSNAP]:
                                    from Utils2.nodealignutils import AlignUtils
                                    AlignUtils().snapNodeToGrid(node)

                            # set direction
                            if len(self.getHits()) == 1:
                                self._cursor_trajectory = nodegraphutils.getCursorTrajectory(self.getCursorPoints()[0], self.getCursorPoints()[-1])

                            # iron node
                            if 0 < len(self.getHits()):
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

                            self.addHit(node)
                            nodeutils.addNodePreviewColor([node])

                self.addCursorPoint(mouse_pos)


""" EVENTS"""
def installNodeIronLayer(**kwargs):
    insertLayerIntoNodegraph(NodeIronLayer, ATTR_NAME, Qt.Key_A, "Align Nodes")