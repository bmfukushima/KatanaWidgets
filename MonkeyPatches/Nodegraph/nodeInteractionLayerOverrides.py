import os
import inspect

from qtpy.QtCore import Qt, QSize, QPoint, QTimer
from qtpy.QtGui import QCursor

from Katana import NodegraphAPI, Utils, UI4, DrawingModule, KatanaFile, LayeredMenuAPI, PrefNames, KatanaPrefs
from UI4.App import Tabs
from UI4.Tabs.NodeGraphTab.Layers.NodeInteractionLayer import NodeInteractionLayer
from UI4.Tabs.NodeGraphTab.Layers.NodeGraphViewInteractionLayer import NodeGraphViewInteractionLayer
from UI4.Tabs.NodeGraphTab.Layers.StickyNoteInteractionLayer import EditBackdropNodeDialog

from cgwidgets.utils import scaleResolution
from cgwidgets.settings import iColor
from cgwidgets.widgets import PopupHotkeyMenu

from Widgets2 import PopupWidget, AbstractParametersDisplayWidget
from Utils2 import nodeutils, widgetutils, nodegraphutils
from Utils2.nodealignutils import AlignUtils

from .gridLayer import GridGUIWidget
from .portConnector import PortConnector
from .backdropLayer import BackdropPreviewLayer

UP = 0
DOWN = 1
BACK = 2
FORWARD = 4
HOME = 8

""" UTILS """
def createBackdropNode(is_floating=False):
    """ Creates a backdrop node around the current selection"""
    Utils.UndoStack.OpenGroup("Create Backdrop")

    # get nodegraph
    nodegraph_widget = widgetutils.isCursorOverNodeGraphWidget()
    if not nodegraph_widget:
        nodegraph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()

    # create backdrop and fit around selection
    current_group = nodegraph_widget.getCurrentNodeView()
    backdrop_node = NodegraphAPI.CreateNode("Backdrop", current_group)
    NodegraphAPI.SetNodeSelected(backdrop_node, True)
    nodegraph_widget.fitBackdropNode()

    # float if no nodes selected
    if len(NodegraphAPI.GetAllSelectedNodes()) == 1 or is_floating:
        nodegraph_widget.parent().floatNodes(NodegraphAPI.GetAllSelectedNodes())

    # prompt user for setting the node color
    def previewCallback(node, attr_dict):
        """ Callback run when the user updates a parameter in the backdrop node

        Args:
            node (Node): backdrop node to be updated
            attr_dict (dict): attributes to be updated
            """
        # get nodegraph
        nodegraph_widget = widgetutils.isCursorOverNodeGraphWidget()
        if not nodegraph_widget:
            nodegraph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()

        for attrName, attrValue in attr_dict.items():
            DrawingModule.nodeWorld_setShapeAttr(node, attrName, attrValue)
            DrawingModule.nodeWorld_setShapeAttr(node, "update", 1)

            for layerStack in nodegraph_widget.getAllNodeGraphWidgets():
                layerStack.setNGVShapeAttrs(node, attr_dict)
            # this gives us live updates
            nodegraph_widget.idleUpdate()

    d = EditBackdropNodeDialog(backdrop_node, previewCallback=previewCallback)
    d.exec_()
    d.close()
    d.move(QCursor.pos())
    Utils.UndoStack.CloseGroup()


def disableNodes():
    selected_nodes = NodegraphAPI.GetAllSelectedNodes()
    for node in selected_nodes:
        node.isBypassed()
        node.setBypassed(not node.isBypassed())


def displayParameters():
    """ Sets all of the currently selected nodes to being edited """
    Utils.UndoStack.OpenGroup('Edit Nodes')
    try:
        for current_nodes in NodegraphAPI.GetAllEditedNodes():
            NodegraphAPI.SetNodeEdited(current_nodes, False)

        for selected_nodes in NodegraphAPI.GetAllSelectedNodes():
            NodegraphAPI.SetNodeEdited(selected_nodes, not NodegraphAPI.IsNodeEdited(selected_nodes))

    finally:
        Utils.UndoStack.CloseGroup()


def displayPopupParameters(hide_on_leave=False):
    """ Popups up a parameters view of all of the currently selected nodes

    Args:
        hide_on_leave (bool): determines if this should should be hidden on leave
    """

    # preflight
    selected_nodes = NodegraphAPI.GetAllSelectedNodes()
    if len(selected_nodes) == 0:
        selected_nodes = list(filter(None, [nodeutils.getClosestNode()]))

    if len(selected_nodes) == 0: return

    # construct popup parameters window if it doesn't exist
    if not PopupWidget.doesPopupWidgetExist("popupParameters"):
        # create popup widget
        widget = AbstractParametersDisplayWidget()
        size = scaleResolution(QSize(800, 1060))
        popup_widget = PopupWidget.constructPopupWidget(
            "popupParameters", widget, size=size, hide_hotkey=Qt.Key_E, hide_modifiers=Qt.AltModifier)
        # setup style
        rgba_border = iColor["rgba_selected"]
        popup_widget.setStyleSheet(f"""
            QWidget#PopupWidget{{
                border-top: 1px solid rgba{rgba_border};
                border-bottom: 1px solid rgba{rgba_border};
            }}
        """)

        # set popup widget style
        popup_widget.setIsMaskEnabled(True)
        popup_widget.setMaskSize(scaleResolution(QSize(800, 2000)))
        popup_widget.setContentsMargins(0, 0, 0, 0)
        popup_widget.layout().setContentsMargins(0, 0, 0, 0)
        offset_x = scaleResolution(70)
        offset_y = scaleResolution(15)
        popup_widget.centralWidget().setContentsMargins(offset_x, offset_y, offset_x, offset_y)

    # hide/show popup parameters
    widget = PopupWidget.getPopupWidget("popupParameters")
    widget.setHideOnLeave(hide_on_leave)
    widget.mainWidget().populateParameters(selected_nodes, hide_title=False)
    pos = QPoint(
        QCursor.pos().x(),
        QCursor.pos().y() + widget.height() * 0.25

    )
    PopupWidget.togglePopupWidgetVisibility("popupParameters", pos=pos)


def displayGridSettings(hide_on_leave=True):
    """ Popups up a parameters view of all of the currently selected nodes

    Args:
        hide_on_leave (bool): determines if this should should be hidden on leave
    """
    # construct popup parameters window if it doesn't exist
    if not PopupWidget.doesPopupWidgetExist("gridSettings"):
        # create popup widget
        widget = GridGUIWidget()
        size = scaleResolution(QSize(600, 375))
        popup_widget = PopupWidget.constructPopupWidget(
            "gridSettings", widget, size=size, hide_hotkey=Qt.Key_E, hide_modifiers=Qt.AltModifier)
        # setup style
        rgba_border = iColor["rgba_selected"]
        popup_widget.setStyleSheet(f"""
            QWidget#PopupWidget{{
                border-top: 1px solid rgba{rgba_border};
                border-bottom: 1px solid rgba{rgba_border};
            }}
        """)

        # set popup widget style
        popup_widget.setIsMaskEnabled(True)
        popup_widget.setMaskSize(scaleResolution(QSize(600, 750)))
        popup_widget.setContentsMargins(0, 0, 0, 0)
        popup_widget.layout().setContentsMargins(0, 0, 0, 0)
        offset_x = scaleResolution(70)
        offset_y = scaleResolution(30)
        popup_widget.centralWidget().setContentsMargins(offset_x, offset_y, offset_x, offset_y)

    # hide/show popup parameters
    widget = PopupWidget.getPopupWidget("gridSettings")
    widget.setHideOnLeave(hide_on_leave)
    pos = QPoint(
        QCursor.pos().x(),
        QCursor.pos().y() + widget.height() * 0.25

    )
    PopupWidget.togglePopupWidgetVisibility("gridSettings", pos=pos)


def duplicateNodes(nodegraph_layer, nodes_to_duplicate=None):
    """ Duplicate selected nodes, or closest node to cursor

    Args:
        nodegraph_layer (NodeGraphLayer): Current layer of the Nodegraph.
            Most likely the NodeInteractionLayer
        """
    selected_nodes = NodegraphAPI.GetAllSelectedNodes()

    # check selected nodes
    if not nodes_to_duplicate:
        nodes_to_duplicate = [node for node in selected_nodes if not NodegraphAPI.IsNodeLockedByParents(node)]

    # no selected nodes, get closest node
    if not nodes_to_duplicate:
        nodes_to_duplicate = [nodeutils.getClosestNode()]

    duplicated_nodes = NodegraphAPI.Util.DuplicateNodes(nodes_to_duplicate)
    nodeutils.selectNodes(duplicated_nodes, is_exclusive=True)

    if duplicated_nodes:
        nodegraph_layer.layerStack().parent().prepareFloatingLayerWithPasteBounds(duplicated_nodes)
        nodegraph_layer.layerStack().parent()._NodegraphPanel__nodegraphWidget.enableFloatingLayer()


def glowNodes(event):
    """ Glows the nodes of the next selection possible selection

    If a combination of Alt | Alt+Shift is used, then it will
    color the upstream/downstream nodes for selection aswell

    note that this also happens in the "nodeInteractionKeyPressEvent"
    """

    """ Need to by pass for special functionality for backdrops"""
    if event.modifiers() == Qt.NoModifier:
        nodeutils.colorClosestNode(has_output_ports=True)
    backdrop_node = nodegraphutils.getBackdropNodeUnderCursor()
    if backdrop_node:
        # move backdrop
        if event.modifiers() == (Qt.ControlModifier):
            nodeutils.colorClosestNode([backdrop_node])

        # duplicate backdrop and children
        if event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            backdrop_node_children = nodegraphutils.getBackdropChildren(backdrop_node)
            nodeutils.colorClosestNode(backdrop_node_children)

        # move backdrop and children
        if event.modifiers() == (Qt.AltModifier):
            backdrop_node_children = nodegraphutils.getBackdropChildren(backdrop_node)
            nodeutils.colorClosestNode(backdrop_node_children)

    else:
        # move upstream nodes
        if event.modifiers() == Qt.AltModifier:
            closest_node = nodeutils.getClosestNode(has_input_ports=True)
            if closest_node:
                upstream_nodes = AlignUtils.getUpstreamNodes(closest_node)
                nodeutils.colorClosestNode(upstream_nodes)

        # move downstream nodes
        if event.modifiers() == (Qt.AltModifier | Qt.ShiftModifier):
            closest_node = nodeutils.getClosestNode(has_output_ports=True)
            if closest_node:
                downstream_nodes = AlignUtils.getDownstreamNodes(closest_node)
                nodeutils.colorClosestNode(downstream_nodes)


def moveNodes(direction=UP):
    """ Selects and moves the nodes upstream or downstream of the selected node """

    node_list = None
    if direction == UP:
        closest_node = nodeutils.getClosestNode(has_input_ports=True)
        if closest_node:
            node_list = AlignUtils.getUpstreamNodes(closest_node)
    if direction == DOWN:
        closest_node = nodeutils.getClosestNode(has_output_ports=True)
        if closest_node:
            node_list = AlignUtils.getDownstreamNodes(closest_node)

    if node_list:
        nodeutils.selectNodes(node_list)
        nodeutils.floatNodes(node_list)


def navigateNodegraph(direction):
    """ Goes back/forward the node hierarchy history

    Args:
        direction (BACK | FORWARD): Determines which way
    """
    nodegraph_widget = widgetutils.getActiveNodegraphWidget()
    navigation_toolbar = nodegraph_widget.parent()._NodegraphPanel__navigationToolbar
    if direction == FORWARD:
        navigation_toolbar._NavigationToolbar__forwardButtonClicked()
    if direction == BACK:
        navigation_toolbar._NavigationToolbar__backButtonClicked()
    if direction == HOME:
        nodegraph_widget.setCurrentNodeView(NodegraphAPI.GetRootNode())
    if direction == UP:
        if nodegraph_widget.getCurrentNodeView() != NodegraphAPI.GetRootNode():
            nodegraph_widget.setCurrentNodeView(nodegraph_widget.getCurrentNodeView().getParent())


def resizeBackdropNode():
    """ Resizes the backdrop node when the user has done an Alt+RMB """
    # get attrs
    curr_cursor_pos, _ = nodegraphutils.getNodegraphCursorPos()
    orig_attrs = widgetutils.katanaMainWindow()._backdrop_orig_attrs
    if "name" not in orig_attrs: return

    node = NodegraphAPI.GetNode(orig_attrs["name"])
    orig_node_pos = (orig_attrs["x"], orig_attrs["y"])
    orig_cursor_pos = orig_attrs["orig_cursor_pos"]
    quadrant = orig_attrs["quadrant"]
    min_size = 100
    if "ns_sizeX" not in orig_attrs:
        orig_attrs["ns_sizeX"] = 128
    if "ns_sizeY" not in orig_attrs:
        orig_attrs["ns_sizeY"] = 64

    # setup attrs
    new_attrs = {}
    for attr_name, attr_value in orig_attrs.items():
        if attr_name not in ["quadrant", "orig_cursor_pos", "selected"]:
            new_attrs[attr_name.replace("ns_", "")] = attr_value

    # Get offset
    offset_x, offset_y = 0, 0
    if KatanaPrefs[PrefNames.NODEGRAPH_GRIDSNAP]:
        grid_pos = nodegraphutils.getNearestGridPoint(curr_cursor_pos.x(), curr_cursor_pos.y())
        if quadrant == nodegraphutils.TOPRIGHT:
            offset_x = grid_pos.x() - (orig_node_pos[0] + new_attrs["sizeX"] * 0.5)
            offset_y = grid_pos.y() - (orig_node_pos[1] + new_attrs["sizeY"] * 0.5)
        elif quadrant == nodegraphutils.TOP:
            offset_x = 0
            offset_y = grid_pos.y() - (orig_node_pos[1] + new_attrs["sizeY"] * 0.5)
        elif quadrant == nodegraphutils.TOPLEFT:
            offset_x = grid_pos.x() - (orig_node_pos[0] - new_attrs["sizeX"] * 0.5)
            offset_y = grid_pos.y() - (orig_node_pos[1] + new_attrs["sizeY"] * 0.5)
        elif quadrant == nodegraphutils.LEFT:
            offset_x = grid_pos.x() - (orig_node_pos[0] - new_attrs["sizeX"] * 0.5)
            offset_y = 0
        elif quadrant == nodegraphutils.BOTLEFT:
            offset_x = grid_pos.x() - (orig_node_pos[0] - new_attrs["sizeX"] * 0.5)
            offset_y = grid_pos.y() - (orig_node_pos[1] - new_attrs["sizeY"] * 0.5)
        elif quadrant == nodegraphutils.BOT:
            offset_x = 0
            offset_y = grid_pos.y() - (orig_node_pos[1] - new_attrs["sizeY"] * 0.5)
        elif quadrant == nodegraphutils.BOTRIGHT:
            offset_x = grid_pos.x() - (orig_node_pos[0] + new_attrs["sizeX"] * 0.5)
            offset_y = grid_pos.y() - (orig_node_pos[1] - new_attrs["sizeY"] * 0.5)
        elif quadrant == nodegraphutils.RIGHT:
            offset_x = grid_pos.x() - (orig_node_pos[0] + new_attrs["sizeX"] * 0.5)
            offset_y = 0
        elif quadrant == nodegraphutils.CENTER:
            # Todo update offset
            offset_x = grid_pos.x() - (orig_node_pos[0] + new_attrs["sizeX"] * 0.5)
            offset_y = grid_pos.y() - (orig_node_pos[1] + new_attrs["sizeY"] * 0.5)
    else:
        offset_x = curr_cursor_pos.x() - orig_cursor_pos.x()
        offset_y = curr_cursor_pos.y() - orig_cursor_pos.y()

    # update size
    if quadrant == nodegraphutils.TOPRIGHT:
        new_attrs["sizeX"] += offset_x
        new_attrs["sizeY"] += offset_y

    elif quadrant == nodegraphutils.TOP:
        new_attrs["sizeY"] += offset_y
        offset_x = 0

    elif quadrant == nodegraphutils.TOPLEFT:
        new_attrs["sizeX"] -= offset_x
        new_attrs["sizeY"] += offset_y

    elif quadrant == nodegraphutils.LEFT:
        new_attrs["sizeX"] -= offset_x
        offset_y = 0

    elif quadrant == nodegraphutils.BOTLEFT:
        new_attrs["sizeX"] -= offset_x
        new_attrs["sizeY"] -= offset_y

    elif quadrant == nodegraphutils.BOT:
        new_attrs["sizeY"] -= offset_y
        offset_x = 0

    elif quadrant == nodegraphutils.BOTRIGHT:
        new_attrs["sizeX"] += offset_x
        new_attrs["sizeY"] -= offset_y

    elif quadrant == nodegraphutils.RIGHT:
        new_attrs["sizeX"] += offset_x
        offset_y = 0

    elif quadrant == nodegraphutils.CENTER:
        new_attrs["sizeX"] += offset_x
        new_attrs["sizeY"] += offset_y

    # set min size
    if new_attrs["sizeX"] < min_size:
        new_attrs["sizeX"] = min_size
    if new_attrs["sizeY"] < min_size:
        new_attrs["sizeY"] = min_size

    # node pos
    if quadrant != nodegraphutils.CENTER:
        new_node_pos_x = orig_node_pos[0] + offset_x * 0.5
        new_node_pos_y = orig_node_pos[1] + offset_y * 0.5

        # check min size
        if new_attrs["sizeX"] == min_size:
            new_node_pos_x = NodegraphAPI.GetNodePosition(node)[0]
        if new_attrs["sizeY"] == min_size:
            new_node_pos_y = NodegraphAPI.GetNodePosition(node)[1]
        NodegraphAPI.SetNodePosition(node, (new_node_pos_x, new_node_pos_y))
    else:
        # todo setup node positioning for center
        # really only might need it for snapping?
        pass


    new_attrs["zDepth"] = 1 / (new_attrs["sizeX"] * new_attrs["sizeY"])

    nodegraphutils.updateBackdropDisplay(node, attrs=new_attrs)


""" EVENTS"""
def nodeInteractionLayerMouseMoveEvent(func):
    """ Changes the color of the nearest node """
    def __nodeInteractionLayerMouseMoveEvent(self, event):
        # run functions
        glowNodes(event)

        # resize backdrop
        if event.modifiers() == Qt.AltModifier and event.buttons() == Qt.RightButton:
            resizeBackdropNode()

        return func(self, event)

    return __nodeInteractionLayerMouseMoveEvent


def nodeInteractionMousePressEvent(func):
    """ DUPLICATE NODES """
    def __nodeInteractionMousePressEvent(self, event):
        # Nodegraph Navigation
        if event.button() == Qt.ForwardButton and event.modifiers() == Qt.NoModifier:
            navigateNodegraph(FORWARD)
        if event.button() == Qt.BackButton and event.modifiers() == Qt.NoModifier:
            navigateNodegraph(BACK)
        if event.button() == Qt.ForwardButton and event.modifiers() == Qt.AltModifier:
            navigateNodegraph(HOME)
        if event.button() == Qt.BackButton and event.modifiers() == Qt.AltModifier:
            navigateNodegraph(UP)

        """ Need to by pass for special functionality for backdrops"""
        backdrop_node = nodegraphutils.getBackdropNodeUnderCursor()
        if backdrop_node:
            # Bypass if user has clicked on a node

            # move backdrop
            if event.modifiers() == (Qt.ControlModifier) and event.button() == Qt.LeftButton:
                nodeutils.selectNodes([backdrop_node], is_exclusive=True)
                nodeutils.floatNodes([backdrop_node])
                return True

            # duplicate backdrop and children
            if event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier) and event.button() == Qt.LeftButton:
                nodes_to_duplicate = nodegraphutils.getBackdropChildren(backdrop_node)
                duplicateNodes(self, nodes_to_duplicate=nodes_to_duplicate)
                return True

            # move backdrop and children
            if event.modifiers() == Qt.AltModifier and event.button() == Qt.LeftButton:
                nodes_to_move = nodegraphutils.getBackdropChildren(backdrop_node)
                nodeutils.selectNodes(nodes_to_move, is_exclusive=True)
                nodeutils.floatNodes(nodes_to_move)
                return True

            # initialize backdrop resize event
            if event.modifiers() == Qt.AltModifier and event.button() == Qt.RightButton:
                quadrant = nodegraphutils.getBackdropQuadrantSelected(backdrop_node)
                attrs = backdrop_node.getAttributes()
                attrs["quadrant"] = quadrant
                attrs["orig_cursor_pos"] = nodegraphutils.getNodegraphCursorPos()[0]
                widgetutils.katanaMainWindow()._backdrop_orig_attrs = attrs
                widgetutils.katanaMainWindow()._backdrop_resize_active = True
                return True

            # Select backdrop and children
            if event.modifiers() == Qt.NoModifier and event.button() == Qt.LeftButton:
                # If node clicked, bypass
                if nodegraphutils.nodeClicked(self.layerStack()): return func(self, event)

                # # If backdrop clicked, select and pickup
                if backdrop_node in NodegraphAPI.GetAllSelectedNodes():
                    nodes_to_float = nodegraphutils.getBackdropChildren(backdrop_node)
                    nodeutils.floatNodes(nodes_to_float)
                else:
                    nodes_to_select = nodegraphutils.getBackdropChildren(backdrop_node)
                    nodeutils.selectNodes(nodes_to_select, is_exclusive=True)
                return True

            # Append backdrop and children to current selection
            if event.modifiers() == Qt.ShiftModifier and event.button() == Qt.LeftButton:
                nodes_to_select = nodegraphutils.getBackdropChildren(backdrop_node)
                nodeutils.selectNodes(nodes_to_select)
                return True
        else:
            # Duplicate nodes
            if event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier) and event.button() == Qt.LeftButton:
                duplicateNodes(self)
                return True

            # Move nodes
            if event.modifiers() == Qt.AltModifier and event.button() in [Qt.LeftButton]:
                moveNodes(UP)
                return True
            if event.modifiers() == (Qt.AltModifier | Qt.ShiftModifier) and event.button() in [Qt.LeftButton]:
                moveNodes(DOWN)
                return True

        return func(self, event)

    return __nodeInteractionMousePressEvent


def nodeInteractionMouseReleaseEvent(func):
    """ DUPLICATE NODES """
    def __nodeInteractionMouseReleaseEvent(self, event):
        widgetutils.katanaMainWindow()._backdrop_resize_active = False
        return func(self, event)

    return __nodeInteractionMouseReleaseEvent


def nodeInteractionKeyPressEvent(func):
    def __nodeInteractionKeyPressEvent(self, event):
        """ This needs to go here to keep the variable in scope"""
        # color node selection
        nodegraph_widget = widgetutils.getActiveNodegraphWidget()
        is_floating = nodegraph_widget.getLayerByName("Floating Nodes").enabled()

        if not is_floating:
            glowNodes(event)

        # Process Key Presses
        if event.key() == 96:
            # Shift+~ and Alt+Shift+~ are handled by the script manager
            PortConnector.actuateSelection()
            return True

        # updating disable handler
        if event.key() in [Qt.Key_D, Qt.Key_Q] and event.modifiers() == Qt.NoModifier:
            disableNodes()
            return True

        # updating parameter view handler
        if event.key() == Qt.Key_E:
            if event.modifiers() == (Qt.AltModifier | Qt.ShiftModifier):
                displayPopupParameters(hide_on_leave=False)
                return True
            elif event.modifiers() == Qt.AltModifier:
                displayPopupParameters(hide_on_leave=True)
                return True
            elif event.modifiers() == Qt.NoModifier:
                displayParameters()
            return True

        if event.key() == Qt.Key_F and event.modifiers() == Qt.NoModifier:
            current_group = self.layerStack().getCurrentNodeView()
            selected_nodes = [x for x in NodegraphAPI.GetAllSelectedNodes() if x.getParent() == current_group]
            if selected_nodes:
                self.frameSelection()
            else:
                self.layerStack().getLayerByName('Frame All').frameAll()
            return True

        if event.key() == Qt.Key_A and event.modifiers() == Qt.NoModifier:
            current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
            file_path = f"{current_dir}/NodeAlignment/AlignNodes.json"
            popup_widget = PopupHotkeyMenu(parent=widgetutils.katanaMainWindow(), file_path=file_path)
            popup_widget.show()
            return True

        if event.key() == Qt.Key_B and event.modifiers() == Qt.NoModifier:
            createBackdropNode(is_floating=False)
            return True

        if event.key() == Qt.Key_B and event.modifiers() == Qt.NoModifier:
            createBackdropNode(is_floating=True)
            return True

        if event.key() == Qt.Key_G and event.modifiers() == (Qt.ControlModifier):
            displayGridSettings()
            return True

        if event.key() == Qt.Key_N and event.modifiers() == Qt.NoModifier:
            nodegraph_widget = widgetutils.getActiveNodegraphWidget()
            from UIPlugins.NMXMenu import NMXMenuPopulateCallback, NMXMenuActionCallback
            NMXMenu = LayeredMenuAPI.LayeredMenu(
                    NMXMenuPopulateCallback,
                    NMXMenuActionCallback,
                    'N',
                    alwaysPopulate=True,
                    onlyMatchWordStart=False
                )
            nodegraph_widget.showLayeredMenu(NMXMenu)
            return True

        if event.key() == Qt.Key_W and event.modifiers() == Qt.NoModifier:
            selected_nodes = NodegraphAPI.GetAllSelectedNodes()
            if selected_nodes:
                view_node = selected_nodes[0]
            else:
                view_node = nodeutils.getClosestNode()

            if view_node:
                NodegraphAPI.SetNodeViewed(view_node, True, exclusive=True)

            return True

        return func(self, event)

    return __nodeInteractionKeyPressEvent


def showEvent(func):
    def __showEvent(self, event):
        # disable floating layer, as it for some reason inits as True...
        self.getLayerByName("Floating Nodes").setEnabled(False)

        # setup grid layer
        backdrop_preview_layer = self.getLayerByName("Backdrop Preview Layer")
        if not backdrop_preview_layer:
            self._backdrop_preview_layer = BackdropPreviewLayer("Backdrop Preview Layer", enabled=True)

            self.appendLayer(self._backdrop_preview_layer)
        return func(self, event)

    return __showEvent


def installNodegraphHotkeyOverrides(**kwargs):
    """ Installs the hotkey overrides """
    # Node interaction key press

    # create proxy nodegraph
    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()
    nodegraph_widget.__class__.showEvent = showEvent(nodegraph_widget.__class__.showEvent)

    # NORMAL NODEGRAPH
    node_interaction_layer = nodegraph_widget.getLayerByName("NodeInteractions")

    node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress = nodeInteractionKeyPressEvent(
        NodeInteractionLayer._NodeInteractionLayer__processKeyPress)
    node_interaction_layer.__class__._NodeInteractionLayer__processMouseButtonPress = nodeInteractionMousePressEvent(
        NodeInteractionLayer._NodeInteractionLayer__processMouseButtonPress)
    node_interaction_layer.__class__._NodeInteractionLayer__processMouseButtonRelease = nodeInteractionMouseReleaseEvent(
        NodeInteractionLayer._NodeInteractionLayer__processMouseButtonRelease)
    node_interaction_layer.__class__._NodeInteractionLayer__processMouseMove = nodeInteractionLayerMouseMoveEvent(
        NodeInteractionLayer._NodeInteractionLayer__processMouseMove)

    # NETWORK MATERIAL
    nodegraph_view_interaction_layer = nodegraph_widget.getLayerByName("NodeGraphViewInteraction")
    nodegraph_view_interaction_layer.__class__._NodeGraphViewInteractionLayer__processKeyPress = nodeInteractionKeyPressEvent(
        NodeGraphViewInteractionLayer._NodeGraphViewInteractionLayer__processKeyPress)
    nodegraph_view_interaction_layer.__class__._NodeGraphViewInteractionLayer__processMouseButtonDown = nodeInteractionMousePressEvent(
        NodeGraphViewInteractionLayer._NodeGraphViewInteractionLayer__processMouseButtonDown)
    # has no release...
    # doesn't matter as this is only setting the backdrop release attr, which won't even work on this layer =\
    # nodegraph_view_interaction_layer.__class__._NodeGraphViewInteractionLayer__processMouseButtonRelease = nodeInteractionMouseReleaseEvent(
    #     NodeGraphViewInteractionLayer._NodeGraphViewInteractionLayer__processMouseButtonRelease)
    nodegraph_view_interaction_layer.__class__._NodeGraphViewInteractionLayer__processMouseMove = nodeInteractionLayerMouseMoveEvent(
        NodeGraphViewInteractionLayer._NodeGraphViewInteractionLayer__processMouseMove)

    # cleanup
    nodegraph_widget.cleanup()