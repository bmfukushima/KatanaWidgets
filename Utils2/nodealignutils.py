"""
- Align All
    Issue with recursion...
        - Can't seem to find nodes... when it recurses back up, then back down...
        for some reason it doesn't fine some down stream nodes...
            - tried moving the recursive loop... just stalled out lol
    Root node not being aligned
    Potentially store node dictionary with offsets...
        check against dictionary
        if it is overlapping... 
            offset and recurse up/down?

- Arrow key walk nodes
    Up/Down go up/down...
    Left/Right 
        Check above and below... to see if multiple ports
            if multiple ports... go to the next index
Iron Trajectory is set by direction when you pass through first node...

"""
import sys
import platform
import time
import math


from qtpy import QtWidgets, QtGui, QtCore
from Katana import UI4, NodegraphAPI, DrawingModule, NodeGraphView, Utils


class MainWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MainWidget, self).__init__(parent)
        # Setting Display Attrs
        if platform.system() == 'Linux':
            self.setWindowFlags(
                QtCore.Qt.Tool
                | QtCore.Qt.NoDropShadowWindowHint
                | QtCore.Qt.FramelessWindowHint
                | QtCore.Qt.WindowStaysOnTopHint
            )

        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.view = View()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        layout.addWidget(self.view)


class View(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super(View, self).__init__(parent)
        if platform.system() == 'Linux':
            self.setWindowFlags(
                QtCore.Qt.Tool
                | QtCore.Qt.NoDropShadowWindowHint
                | QtCore.Qt.FramelessWindowHint
                | QtCore.Qt.WindowStaysOnTopHint
            )

        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        """
        self.setViewportUpdateMode(
            QtWidgets.QGraphicsView.FullViewportUpdate
        )
        """
        # Setup Scene/Viewport
        viewport = QtWidgets.QOpenGLWidget()
        self.setViewport(viewport)

        scene = Scene()
        self.setScene(scene)

        # Nodegraph
        self.nodegraph = UI4.App.Tabs.FindTopTab('Node Graph')
        self.nodegraph_widget = self.nodegraph.getNodeGraphWidget()
        self.katana_main = UI4.App.MainWindow.GetMainWindow()
        self.x_space = 6
        self.y_space = 6
        self.x_grid = 32
        self.y_grid = 16
        self.x_offset = self.x_grid * self.x_space
        self.y_offset = (self.y_grid * self.y_space) * -1
        self.x = 0
        self.upstream_x = 0

        self.modifer_pressed = False
        self.modifier_key = QtCore.Qt.Key_Alt

    """  EVENTS """

    def eventFilter(self, obj, event, *args, **kwargs):
        # self.nodegraph_widget = self.nodegraph.getNodeGraphWidget()
        # modfier_key = QtCore.Qt.Key_Alt
        # alt_key = QtCore.Qt.Key_Alt

        # =======================================================================
        # # KEYBOARD EVENTS
        # =======================================================================
        # Key Press
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == self.modifier_key:
                if not hasattr(self, 'iron'):
                    self.goIron()

                # set cursor /home/brian/Downloads/iron_selected.png
                pixmap = QtGui.QPixmap('/home/brian/Downloads/iron_selected.png')
                pixmap = pixmap.scaled(
                    50,
                    50,
                    QtCore.Qt.KeepAspectRatio,
                    transformMode=QtCore.Qt.SmoothTransformation
                )
                cursor = QtGui.QCursor(pixmap)
                self.nodegraph_widget.setCursor(cursor)
                # Set Ironing On
                # if shift is pressed, it will maintain the old list
                if event.modifiers() != QtCore.Qt.ShiftModifier:
                    self.iron.setNodeList([])
                self.iron.resetTrajectory()
                self.modifer_pressed = True
            elif event.key() == QtCore.Qt.Key_Escape:
                self.close()

        if event.type() == QtCore.QEvent.KeyRelease:
            if event.key() == self.modifier_key:
                if hasattr(self, 'iron'):
                    self.iron.setNodeList([])
                    self.modifer_pressed = False
                    self.nodegraph_widget.unsetCursor()
        # =======================================================================
        # MOUSE EVENTS
        # =======================================================================
        # Move Event
        if event.type() == QtCore.QEvent.MouseMove:
            if hasattr(self, 'iron'):
                if self.modifer_pressed is True:
                    pos = self.mapFromGlobal(QtGui.QCursor.pos())
                    width = self.iron.rect().width() * .5
                    height = self.iron.rect().height() * .5
                    self.iron.setPos(pos.x() - width, pos.y() - height)
                else:
                    self.nodegraph_widget.unsetCursor()

        return QtWidgets.QGraphicsView.eventFilter(self, obj, event, *args, **kwargs)

    def keyPressEvent(self, event, *args, **kwargs):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        return QtWidgets.QGraphicsView.keyPressEvent(self, event, *args, **kwargs)

    def keyReleaseEvent(self, event, *args, **kwargs):
        if event.key() == self.modifier_key:
            if hasattr(self, 'iron'):
                self.hide()
                self.iron.setNodeList([])
                self.modifer_pressed = False
                self.nodegraph_widget.unsetCursor()
        return QtWidgets.QGraphicsView.keyReleaseEvent(self, event, *args, **kwargs)

    def closeEvent(self, *args, **kwargs):
        self.nodegraph_widget.removeEventFilter(self)
        self.nodegraph_widget.unsetCursor()
        return QtWidgets.QGraphicsView.closeEvent(self, *args, **kwargs)

    """ HELPER STUFFS"""
    def mapToNodegraph(self, pos):
        """
        maps a screen space position to the Nodegraphs position
        @pos <QPoint> in screen space
        """
        local = self.nodegraph_widget.mapFromGlobal(pos)
        scene_pos = self.nodegraph_widget.mapFromQTLocalToWorld(local.x(), local.y())
        return scene_pos

    def setupMask(self):
        region = QtGui.QRegion(self.frameGeometry())
        region -= QtGui.QRegion(self.geometry())
        if hasattr(self, 'bumper'):
            bumper = self.bumper.rect()
            width = bumper.toAlignedRect().width()
            height = bumper.toAlignedRect().height()
            bumper_pos = self.bumper.pos()
            if bumper_pos.isNull() is True:
                bumper_pos = QtCore.QPoint(1, 1)
            scene_pos = self.mapFromScene(bumper_pos)
            region += QtGui.QRegion(
                scene_pos.x() + 1, scene_pos.y() + 1, width, height
            )
        if hasattr(self, 'iron'):
            iron = self.iron.rect()
            width = iron.toAlignedRect().width()
            height = iron.toAlignedRect().height()
            iron_pos = self.iron.pos()
            if iron_pos.isNull() is True:
                iron_pos = QtCore.QPoint(1, 1)
            scene_pos = self.mapFromScene(iron_pos)
            # region += QtGui.QRegion(blah.x()+1, blah.y()+1, width, height, QtGui.QRegion.Ellipse)
            region += QtGui.QRegion(
                scene_pos.x() + 1, scene_pos.y() + 1, width, height
            )

        self.setMask(region)

    def setTransparent(self):
        region = QtGui.QRegion(self.frameGeometry())
        region -= QtGui.QRegion(self.geometry())
        self.setMask(region)

    def getCollidingNodes(
            self,
            left=None,
            top=None,
            right=None,
            bottom=None
    ):
        """
        returns a list of all nodes that are within a specific rectangle
        defined as
        left, top, right, bottom
        """
        all_nodes = NodegraphAPI.GetAllNodes()
        node_list = []
        # get bumper positions
        # bump_l, bump_t, bump_r, bump_b = self.getBumperPosition()

        # run through all nodes and test if they are inside of the bumper
        for node in all_nodes:
            if node.getParent() == self.nodegraph_widget.getCurrentNodeView():
                fit_x = False
                fit_y = False
                # left bot right top
                # weird... normally its left top right bot in Qt... :ok_hand:
                node_bounds = DrawingModule.nodeWorld_getBounds(node)
                node_l = node_bounds[0]
                node_b = node_bounds[1]
                node_r = node_bounds[2]
                node_t = node_bounds[3]

                # ===========================================================
                # CHECK INTERSECTIONS
                # ===========================================================
                # check right
                if (
                        (node_r > left and node_r < right)
                        or (right > node_l and right < node_r)
                ):
                    fit_x = True

                # check left
                if (
                        (node_l < right and node_l > left)
                        or (left < node_r and left > node_l)
                ):
                    fit_x = True

                # check bot
                if (
                        (node_b < top and node_b > bottom)
                        or (bottom > node_t and bottom < node_b)
                ):
                    fit_y = True

                # check top
                if (
                        (node_t > bottom and node_t < top)
                        or (top < node_b and top > node_t)
                ):
                    fit_y = True

                if fit_x is True and fit_y is True:
                    node_list.append(node)

        return node_list

    def smackNodes(self, node_list):
        """
        literally smacks the node based off of the trajectory
        of the bumper
        @node_list <list> of <nodes>
        """
        trajectory_list = self.bumper.getTrajectory()
        p0 = trajectory_list[0]['pos']
        p1 = trajectory_list[-1]['pos']
        new_x = (p0.x() - p1.x())
        new_y = (p0.y() - p1.y())
        magnitude = math.sqrt(
            math.pow(new_x, 2)
            + math.pow(new_y, 2)
        )

        magnitude *= .01
        for node in node_list:
            node_pos = NodegraphAPI.GetNodePosition(node)
            new_pos = (
                node_pos[0] - new_x * magnitude,
                node_pos[1] + new_y * magnitude
            )
            NodegraphAPI.SetNodePosition(node, new_pos)

    """ FUNCTIONS """

    def goBumper(self):
        # Bumper
        self.bumper = Bumper()
        self.bumper.setRect(0, 0, 100, 100)
        self.scene().addItem(self.bumper)

        # tab = UI4.App.Tabs.FindTopTab('Node Graph')._NodegraphPanel__nodegraphWidget
        rect = self.nodegraph_widget.rect()
        left = self.nodegraph_widget.mapToGlobal(rect.topLeft()).x()
        top = self.nodegraph_widget.mapToGlobal(rect.topLeft()).y()
        width = self.nodegraph_widget.geometry().getRect()[2]
        height = self.nodegraph_widget.geometry().getRect()[3]
        self.setGeometry(left, top, width, height)
        self.show()
        self.setupMask()

    def goIron(self):
        """
        Starts the ironing tool
        """
        # Bumper
        self.iron = IronTool()
        # get mouse pos...
        # need to get mouse pos of scene/view
        cursor = QtGui.QCursor.pos()

        # DRAW VIEW / SCENE
        rect = self.nodegraph_widget.rect()
        left = self.nodegraph_widget.mapToGlobal(rect.topLeft()).x()
        top = self.nodegraph_widget.mapToGlobal(rect.topLeft()).y()
        width = self.nodegraph_widget.geometry().getRect()[2]
        height = self.nodegraph_widget.geometry().getRect()[3]
        self.setGeometry(left, top, width, height)
        self.setSceneRect(0, 0, width, height)

        # SET UP ITEM
        pos = self.mapFromGlobal(cursor)
        self.iron.setRect(0, 0, 50, 50)
        self.scene().addItem(self.iron)
        self.iron.setPos(pos)

        self.setTransparent()
        # self.iron.hide()
        # tab = UI4.App.Tabs.FindTopTab('Node Graph')._NodegraphPanel__nodegraphWidget

        # self.show()
        # self.setupMask()

    """ GET NODES """

    def getDownstreamNodes(self, node, node_list=None):
        output_ports = node.getOutputPorts()
        node_list.append(node)
        for output_port in output_ports:
            connected_ports = output_port.getConnectedPorts()
            for output_port in connected_ports:
                connected_node = output_port.getNode()
                self.getDownstreamNodes(
                    connected_node,
                    node_list=node_list
                )
        return list(set(node_list))

    def getUpstreamNodes(self, node, node_list=None):
        input_ports = node.getInputPorts()
        node_list.append(node)
        for input_port in input_ports:
            connected_ports = input_port.getConnectedPorts()
            for input_port in connected_ports:
                connected_node = input_port.getNode()
                self.getUpstreamNodes(
                    connected_node,
                    node_list=node_list
                )
        return list(set(node_list))

    """ SELECTION """
    def selectAllNodes(self, upstream=False, downstream=False):
        node_list = []
        for node in NodegraphAPI.GetAllSelectedNodes():
            if downstream is True:
                print('downstream')
                node_list += self.getDownstreamNodes(node, node_list=[])
            if upstream is True:
                print('upstream')
                node_list += self.getUpstreamNodes(node, node_list=[])
        NodegraphAPI.SetAllSelectedNodes(node_list)
        self.nodegraph.floatNodes(node_list)

    """  ALIGNMENT """
    def getNearestGridPoint(self, x, y):
        """
        @return: returns an offset of grid units (x, y)
        @x: <float> or <int>
        @y: <float> or <int>

        This should be in the Nodegraph Coordinate System,
        use self.mapToNodegraph() to convert to this sytem
        """
        # pos = NodegraphAPI.GetNodePosition(node)
        x = int(x)
        y = int(y)
        if x % self.x_grid > (self.x_grid * .5):
            x_offset = (x // self.x_grid)
        else:
            x_offset = (x // self.x_grid) - 1
        if y % self.y_grid > (self.y_grid * .5):
            y_offset = (y // self.y_grid)
        else:
            y_offset = (y // self.y_grid) - 1
        return (x_offset, y_offset)

    def snapSelectedNodesToGrid(self):
        """
        Gets all of the selected nodes by the user and snaps them
        the grid at the neareset point
        """
        node_list = NodegraphAPI.GetAllSelectedNodes()
        for node in node_list:
            pos = NodegraphAPI.GetNodePosition(node)
            offset = self.getNearestGridPoint(pos[0], pos[1])
            NodegraphAPI.SetNodePosition(
                node,
                (
                    (offset[0] * self.x_grid) + self.x_grid,
                    (offset[1] * self.y_grid) + self.y_grid
                )
            )

    def alignAllNodes(self, x=0, y=0):
        self.align_list = []
        node = NodegraphAPI.GetAllSelectedNodes()[0]
        root_node = View().getTreeRootNode(node)

        # if x and y:
        NodegraphAPI.SetNodePosition(
            root_node,
            (x * self.x_offset, y * self.y_offset)
        )
        self.alignDownstreamNodesRecurse(root_node, x, y)

    def alignDownstreamNodes(self):
        selected_nodes = NodegraphAPI.GetAllSelectedNodes()
        for selected_node in selected_nodes:
            pos = NodegraphAPI.GetNodePosition(selected_node)
            offset = View().getNearestGridPoint(pos[0], pos[1])
            xpos = (offset[0] * View().x_grid) + View().x_grid
            ypos = (offset[1] * View().y_grid) + View().y_grid

            NodegraphAPI.SetNodePosition(
                selected_node, (xpos, ypos)
            )

            node_list = View().alignDownstreamNodesRecurse(selected_node)
            for node in node_list:
                if node != selected_node:
                    orig_pos = NodegraphAPI.GetNodePosition(node)

                    offset_xpos = orig_pos[0] + xpos
                    offset_ypos = orig_pos[1] + ypos

                    NodegraphAPI.SetNodePosition(
                        node, (offset_xpos, offset_ypos)
                    )

    def alignDownstreamNodesRecurse(
            self,
            node,
            x=0,
            y=0,
            node_list=None
    ):
        """
        recursive function to look downstream of a specific node and align all of
        those nodes to the original node
        @node <node> origin node
        @x <int> x_offset
        @y <int> y_offset
        @node_list <list> list of all nodes that have been aligned
        """
        # init node list
        if not node_list:
            node_list = []

        output_ports = node.getOutputPorts()
        node_list.append(node)
        y += 1
        for count, output_port in enumerate(output_ports):
            if count > 0:
                x += 1
            connected_ports = output_port.getConnectedPorts()
            for index, input_port in enumerate(connected_ports):
                connected_node = input_port.getNode()
                if index > 0:
                    x += 1
                if connected_node not in node_list:
                    NodegraphAPI.SetNodePosition(
                        connected_node,
                        (self.x_offset * x, self.y_offset * y)
                    )

                    # recurse through nodes
                    self.alignDownstreamNodesRecurse(
                        connected_node,
                        x=x,
                        y=y,
                        node_list=node_list
                    )

                    # check upstream
                    input_ports = connected_node.getInputPorts()
                    if len(input_ports) > 1:
                        for input_port in input_ports[1:]:
                            self.alignUpstreamNodesRecurse(
                                connected_node,
                                x=x,
                                y=y,
                                node_list=node_list
                            )

        return list(set(node_list))

    def alignUpstreamNodes(self):
        selected_nodes = NodegraphAPI.GetAllSelectedNodes()
        for selected_node in selected_nodes:
            pos = NodegraphAPI.GetNodePosition(selected_node)
            offset = View().getNearestGridPoint(pos[0], pos[1])
            xpos = (offset[0] * View().x_grid) + View().x_grid
            ypos = (offset[1] * View().y_grid) + View().y_grid

            NodegraphAPI.SetNodePosition(
                selected_node, (xpos, ypos)
            )

            node_list = View().alignUpstreamNodesRecurse(selected_node)
            for node in node_list:
                if node != selected_node:
                    orig_pos = NodegraphAPI.GetNodePosition(node)

                    offset_xpos = orig_pos[0] + xpos
                    offset_ypos = orig_pos[1] + ypos

                    NodegraphAPI.SetNodePosition(
                        node, (offset_xpos, offset_ypos)
                    )

    def alignUpstreamNodesRecurse(
            self,
            node,
            x=0,
            y=0,
            node_list=None
    ):
        """ Recursive function to look upstream of a specific node and align all of
        those nodes to the original node
        @node <node> origin node
        @x <int> x_offset
        @y <int> y_offset
        @node_list <list> list of all nodes that have been aligned
        """
        # init node list
        if not node_list:
            node_list = []

        input_ports = node.getInputPorts()
        node_list.append(node)
        y -= 1
        for count, input_port in enumerate(input_ports):
            if count > 0:
                x += 1
            connected_ports = input_port.getConnectedPorts()
            for index, input_port in enumerate(connected_ports):
                connected_node = input_port.getNode()
                if 0 < index:
                    x += 1
                if connected_node not in node_list:
                    NodegraphAPI.SetNodePosition(
                        connected_node,
                        (self.x_offset * x, self.y_offset * y)
                    )

                    # check upstream
                    # upstream_x = x
                    self.alignUpstreamNodesRecurse(
                        connected_node,
                        x=x,
                        y=y,
                        node_list=node_list
                    )

                    # recurse through nodes
                    # check downstream
                    output_ports = connected_node.getOutputPorts()
                    if 1 < len(output_ports):
                        for output_port in output_ports[1:]:
                            self.alignDownstreamNodesRecurse(
                                connected_node,
                                x=x,
                                y=y,
                                node_list=node_list
                            )

        return list(set(node_list))

    def getAllUpstreamTerminalNodes(self, node, node_list=[]):
        """
        gets all nodes upstream of a specific node
        @returns a list of nodes
        """
        children = node.getInputPorts()
        if children > 0:
            for input_port in children:
                connected_ports = input_port.getConnectedPorts()
                for port in connected_ports:
                    node = port.getNode()

                    self.getAllUpstreamTerminalNodes(node, node_list=node_list)
                    terminal = True
                    for input_port in node.getInputPorts():
                        if len(input_port.getConnectedPorts()) > 0:
                            terminal = False
                    if terminal is True:
                        node_list.append(node)
        return list(set(node_list))

    def getTreeRootNode(self, node):
        """
        returns the Root Node of this specific Nodegraph Tree
        aka the upper left node
        """

        def getFirstNode(input_ports):
            """
            gets the first node connected to a node...
            @ports <port> getConnectedPorts()
            """
            for input_port in input_ports:
                connected_ports = input_port.getConnectedPorts()
                if len(connected_ports) > 0:
                    for port in connected_ports:
                        node = port.getNode()
                        if node:
                            return node

            return None

        input_ports = node.getInputPorts()
        if len(input_ports) > 0:
            # get first node
            first_node = getFirstNode(input_ports)
            if first_node:
                return self.getTreeRootNode(first_node)
            else:
                return node
        else:
            return node

    """
def alignDownstreamNodesRecurse(
        self,
        node,
        x=0,
        y=0,
        align_upstream=False,
        node_list=None
    ):
        # init node list
        if not node_list:
            node_list = []

        output_ports = node.getOutputPorts()
        node_list.append(node)
        y += 1
        for count, output_port in enumerate(output_ports):
            connected_ports = output_port.getConnectedPorts()
            for index, input_port in enumerate(connected_ports):
                connected_node = input_port.getNode()
                self.align_list.append(connected_node)
                NodegraphAPI.SetNodePosition(
                    connected_node,
                    (self.x_offset * self.x, self.y_offset * y)
                )

                # check if last node
                terminal = True
                for output_port in connected_node.getOutputPorts():
                    if len(output_port.getConnectedPorts()) > 0:
                        terminal = False
                if terminal is True:
                    self.x += 1

                # check upstream
                if align_upstream is True:
                    input_ports = connected_node.getInputPorts()
                    if len(input_ports) > 1:
                        for input_port in input_ports[1:]:

                            #===================================================
                            # upstream_nodes_list = self.getAllUpstreamTerminalNodes(connected_node)
                            # for upstream_node in upstream_nodes_list:
                            #     self.alignNode(upstream_node)
                            #===================================================

                            self.upstream_x = self.x
                            #print(connected_node, self.upstream_x)
                            self.alignUpstreamNodesRecurse(
                                connected_node,
                                x=self.upstream_x,
                                y=y-1,
                                node_list=node_list
                            )

                # recurse through nodes
                self.alignDownstreamNodesRecurse(
                    connected_node,
                    x=x,
                    y=y,
                    node_list=node_list
                )

        return list(set(node_list))
    def alignUpstreamNodesOld(self, node, x=0, y=0, node_list=None):
        input_ports = node.getInputPorts()
        y -= 1
        if not node_list:
            node_list = []
        node_list.append(node)
        for count, input_port in enumerate(input_ports):
            connected_ports = input_port.getConnectedPorts()
            for index, input_port in enumerate(connected_ports):
                connected_node = input_port.getNode()
                # check if is multi align?
                if hasattr(self, 'align_list'):
                    if connected_node in self.align_list:
                        break

                # alignt node
                NodegraphAPI.SetNodePosition(
                    connected_node,
                    (self.x_offset * self.upstream_x, self.y_offset * y)
                )

                # check if last node
                terminal = True
                for input_port in connected_node.getInputPorts():
                    if len(input_port.getConnectedPorts()) > 0:
                        terminal = False
                if terminal is True:
                    self.upstream_x += 1

                # recurse through nodes
                self.alignUpstreamNodesRecurse(
                    connected_node,
                    x=self.upstream_x,
                    y=y
                )

        return list(set(node_list))
    """


class Scene(QtWidgets.QGraphicsScene):
    def __init__(self, parent=None):
        super(Scene, self).__init__(parent)
        brush = QtGui.QBrush()
        brush_color = QtGui.QColor(128, 0, 128, 255)
        # brush_color.setRgb()
        brush.setColor(brush_color)
        # self.setBackgroundBrush(brush_color)
        # self.setForegroundBrush(brush)
        # self.setupGradient()

    """
    def drawBackground(self, *args, **kwargs):
        return QtWidgets.QGraphicsScene.drawBackground(self, *args, **kwargs)
    """


class IronTool(QtWidgets.QGraphicsRectItem):
    def __init__(self, parent=None):
        super(IronTool, self).__init__(parent)
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        brush = QtGui.QBrush()
        brush_color = QtGui.QColor()
        brush_color.setRgb(128, 255, 128, 255)
        brush.setColor(brush_color)
        brush.setStyle(QtCore.Qt.SolidPattern)
        self.setBrush(brush)

        # =======================================================================
        # hide border
        # =======================================================================

        pen = self.pen()
        no_color = QtGui.QColor()
        no_color.setRgb(0, 0, 0, 0)
        pen.setColor(no_color)
        self.setPen(pen)

    """ EVENTS """

    def itemChange(self, change, value):
        """
        Checks updates on if the IronTool has moved.
        If the iron is moving and it detects a node hit,
        then it will align that node.
        """
        self.prepareGeometryChange()
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            view = self.getView()
            if view:

                # view.setupMask()
                left, top, right, bottom = self.getIronToolPosition()
                node_list = view.getCollidingNodes(
                    left=left, top=top, right=right, bottom=bottom
                )
                # set initial trajectory
                if len(self.getNodeList()) < 1:
                    self.setTrajectory()
                elif (
                        len(self.getNodeList()) > 0
                        and len(self.getTrajectory()) < 5
                ):
                    self.setTrajectory()

                # add new nodes current selection list
                for node in node_list:
                    if node not in self.getNodeList():
                        self.appendToNodeList(node)

                # iron nodes
                if (
                        len(self.getNodeList()) > 0
                        and len(self.getTrajectory()) >= 5
                ):
                    self.ironSelectedNodes()

                view.update()
        return super(IronTool, self).itemChange(change, value)

    """ FUNCTIONS """

    def ironSelectedNodes(self):
        """
        aligns nodes to the nearest grid unit of the contact item
        """
        # Add selected nodes to list for ironing
        selected_nodes = self.getNodeList()
        view = self.getView()

        # Get Trajectory / Set Direction
        # Direction is the direction that the cursor is moving
        # This calculation is done between the first two node hits
        # after that the direction is locked
        trajectory = self.getTrajectory()
        if len(trajectory) > 2:
            p0 = trajectory[0]['pos']
            p1 = trajectory[-1]['pos']
            x = (p0.x() - p1.x())
            y = (p0.y() - p1.y())
            if math.fabs(x) > math.fabs(y):
                direction = 'posx'
                if x < 0:
                    direction = 'negx'
            else:
                direction = 'posy'
                if y < 0:
                    direction = 'negy'

            # Align Row
            if len(selected_nodes) > 0:
                init_pos = NodegraphAPI.GetNodePosition(selected_nodes[0])
                init_offset = view.getNearestGridPoint(init_pos[0], init_pos[1])
                for index, node in enumerate(selected_nodes):
                    if 'x' in direction:
                        if 'neg' in direction:
                            xpos = init_offset[0] + (index * view.x_space)
                        else:
                            xpos = init_offset[0] - (index * view.x_space)
                        ypos = init_offset[1]
                    elif 'y' in direction:
                        if 'neg' in direction:
                            ypos = init_offset[1] - (index * view.y_space)
                        else:
                            ypos = init_offset[1] + (index * view.y_space)
                        xpos = init_offset[0]
                    NodegraphAPI.SetNodePosition(
                        node,
                        ((xpos + 1) * view.x_grid, (ypos + 1) * view.y_grid)
                    )

    def getIronToolPosition(self):
        """
        returns the bumpers bounds in the Nodegraph's coordinate space
        left, top, right, bot
        """
        views = self.scene().views()
        if len(views) > 0:
            view = views[0]
            pos = view.mapFromScene(self.pos())
            pos = view.viewport().mapToGlobal(pos)
            top_left = view.mapToNodegraph(pos)

            bump_r = self.pos().x() + self.rect().width()
            bump_b = self.pos().y() + self.rect().height()
            bot_right = QtCore.QPoint(bump_r, bump_b)
            bot_right = view.mapFromScene(bot_right)
            bot_right = view.viewport().mapToGlobal(bot_right)
            bot_right = view.mapToNodegraph(bot_right)

            return top_left[0], top_left[1], bot_right[0], bot_right[1]

    """ PROPERTIES """
    """
    trajectory needs...
    position
    time
    """

    def getTrajectory(self):
        if not hasattr(self, 'trajectory'):
            self.trajectory = []
        return self.trajectory

    def setTrajectory(self):
        """
        stores the last time/pos coordinates of the mouse move
        prior to it hitting the first node.
        """
        trajectory_list = self.getTrajectory()
        new_dict = {}
        new_dict['time'] = time.time()
        new_dict['pos'] = self.pos()
        trajectory_list.append(new_dict)

        if len(trajectory_list) > 5:
            trajectory_list = trajectory_list[-5:]

        self.trajectory = trajectory_list

    def resetTrajectory(self):
        """
        resets the trajectory, adds default values in to ensure
        that a trajectory can be giving if the operation starts on a node
        """
        self.trajectory = []

    def getNodeList(self):
        if not hasattr(self, 'node_list'):
            self.node_list = []
        return self.node_list

    def setNodeList(self, node_list):
        self.node_list = node_list

    def appendToNodeList(self, node):
        node_list = self.getNodeList()
        node_list.append(node)
        self.node_list = node_list

    def setView(self):
        views = self.scene().views()
        if len(views) > 0:
            view = views[0]
            self.view = view

    def getView(self):
        if not hasattr(self, 'view'):
            self.setView()
        return self.view


class Bumper(QtWidgets.QGraphicsRectItem):
    def __init__(self, parent=None):
        super(Bumper, self).__init__(parent)
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        brush = QtGui.QBrush()
        brush_color = QtGui.QColor()
        brush_color.setRgb(128, 255, 128, 255)
        brush.setColor(brush_color)
        brush.setStyle(QtCore.Qt.SolidPattern)
        self.setBrush(brush)

        # =======================================================================
        # hide border
        # =======================================================================

        pen = self.pen()
        no_color = QtGui.QColor()
        no_color.setRgb(0, 0, 0, 0)
        pen.setColor(no_color)
        self.setPen(pen)

    def itemChange(self, change, value):
        self.prepareGeometryChange()
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            views = self.scene().views()
            if len(views) > 0:
                view = views[0]
                view.setupMask()
                left, top, right, bottom = self.getBumperPosition()
                node_list = view.getCollidingNodes(
                    left=left, top=top, right=right, bottom=bottom
                )
                self.setTrajectory()
                if len(node_list) > 0:
                    view.smackNodes(node_list)

                view.update()
        return super(Bumper, self).itemChange(change, value)

    def getBumperPosition(self):
        """
        returns the bumpers bounds in the Nodegraph's coordinate space
        left, top, right, bot
        """
        views = self.scene().views()
        if len(views) > 0:
            view = views[0]
            pos = view.mapFromScene(self.pos())
            pos = view.viewport().mapToGlobal(pos)
            top_left = view.mapToNodegraph(pos)

            bump_r = self.pos().x() + self.rect().width()
            bump_b = self.pos().y() + self.rect().height()
            bot_right = QtCore.QPoint(bump_r, bump_b)
            bot_right = view.mapFromScene(bot_right)
            bot_right = view.viewport().mapToGlobal(bot_right)
            bot_right = view.mapToNodegraph(bot_right)

            return top_left[0], top_left[1], bot_right[0], bot_right[1]

    """ PROPERTIES """
    """
    trajectory needs...
    position
    time
    """

    def getTrajectory(self):
        if not hasattr(self, 'trajectory'):
            self.trajectory = []
        return self.trajectory

    def setTrajectory(self):
        trajectory_list = self.getTrajectory()
        new_dict = {}
        new_dict['time'] = time.time()
        new_dict['pos'] = self.pos()
        trajectory_list.append(new_dict)
        if len(trajectory_list) > 5:
            trajectory_list = trajectory_list[-5:]

        self.trajectory = trajectory_list

    def mouseReleaseEvent(self, *args, **kwargs):
        views = self.scene().views()
        if len(views) > 0:
            view = views[0]
            view.setupMask()
        return QtWidgets.QGraphicsRectItem.mouseReleaseEvent(self, *args, **kwargs)


def ironNodes():
    nodegraph = UI4.App.Tabs.FindTopTab('Node Graph')
    nodegraph_widget = nodegraph.getNodeGraphWidget()
    view = View()
    view.show()
    nodegraph_widget.installEventFilter(view)


def snapNodeToGrid(node):
    """ Snaps the node provided to the nearest point on the grid"""
    x_grid = 32
    y_grid = 16
    pos = NodegraphAPI.GetNodePosition(node)

    if pos[0] % x_grid < 0.5 * x_grid:
        x = x_grid * (pos[0] // x_grid)
    else:
        x = x_grid * ((pos[0] // x_grid) + 1)

    if pos[1] % y_grid < 0.5 * y_grid:
        y = y_grid * (pos[1] // y_grid)
    else:
        y = y_grid * ((pos[1] // y_grid) + 1)

    NodegraphAPI.SetNodePosition(node, (x, y))