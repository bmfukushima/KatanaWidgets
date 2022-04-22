import os
import inspect

from qtpy.QtCore import Qt, QSize, QPoint, QTimer
from qtpy.QtGui import QCursor

from cgwidgets.utils import scaleResolution
from cgwidgets.settings import iColor
from cgwidgets.widgets import PopupHotkeyMenu

from Widgets2 import PopupWidget, AbstractParametersDisplayWidget
from Utils2 import nodeutils, widgetutils

from Katana import NodegraphAPI, Utils, UI4, DrawingModule, KatanaFile
from UI4.App import Tabs

from UI4.Tabs.NodeGraphTab.Layers.NodeInteractionLayer import NodeInteractionLayer
from UI4.Tabs.NodeGraphTab.Layers.NodeGraphViewInteractionLayer import NodeGraphViewInteractionLayer
from UI4.Tabs.NodeGraphTab.Layers.StickyNoteInteractionLayer import EditBackdropNodeDialog

from .portConnector import PortConnector

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
        popup_widget.setMaskSize(QSize(800, 2000))
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


def duplicateNodes(nodegraph_layer):
    """ Duplicate selected nodes, or closest node to cursor

    Args:
        nodegraph_layer (NodeGraphLayer): Current layer of the Nodegraph.
            Most likely the NodeInteractionLayer
        """
    selected_nodes = NodegraphAPI.GetAllSelectedNodes()
    nodes_to_duplicate = [node for node in selected_nodes if not NodegraphAPI.IsNodeLockedByParents(node)]

    if not nodes_to_duplicate:
        nodes_to_duplicate = [nodeutils.getClosestNode()]

    duplicated_nodes = NodegraphAPI.Util.DuplicateNodes(nodes_to_duplicate)
    nodeutils.selectNodes(duplicated_nodes, is_exclusive=True)

    if duplicated_nodes:
        nodegraph_layer.layerStack().parent().prepareFloatingLayerWithPasteBounds(duplicated_nodes)
        nodegraph_layer.layerStack().parent()._NodegraphPanel__nodegraphWidget.enableFloatingLayer()


def moveNodes(direction=UP):
    """ Selects and moves the nodes upstream or downstream of the selected node """
    from Utils2 import nodeutils, nodealignutils

    closest_node = nodeutils.getClosestNode()
    if direction == UP:
        node_list = nodealignutils.getUpstreamNodes(closest_node)
    if direction == DOWN:
        node_list = nodealignutils.getDownstreamNodes(closest_node)

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


""" EVENTS"""
def nodeInteractionLayerMouseMoveEvent(func):
    """ Changes the color of the nearest node """
    def __nodeInteractionLayerMouseMoveEvent(self, event):
        def colorNearestNode():
            nodeutils.colorClosestNode(has_output_ports=True)

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

    return __nodeInteractionLayerMouseMoveEvent


def nodeInteractionMouseEvent(func):
    """ DUPLICATE NODES """
    def __nodeInteractionMouseEvent(self, event):
        # Nodegraph Navigation
        if event.button() == Qt.ForwardButton and event.modifiers() == Qt.NoModifier:
            navigateNodegraph(FORWARD)
        if event.button() == Qt.BackButton and event.modifiers() == Qt.NoModifier:
            navigateNodegraph(BACK)
        if event.button() == Qt.ForwardButton and event.modifiers() == Qt.ControlModifier:
            navigateNodegraph(UP)
        if event.button() == Qt.BackButton and event.modifiers() == Qt.ControlModifier:
            navigateNodegraph(HOME)

        if event.modifiers() == Qt.AltModifier:
            print("alt??!?")
        # Duplicate nodes
        if event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier) and event.button() in [Qt.MidButton, Qt.MiddleButton]:
            duplicateNodes(self)
            return True

        # Move nodes
        if event.modifiers() == Qt.ControlModifier and event.button() in [Qt.LeftButton]:
            moveNodes(UP)
            return True
        if event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier) and event.button() in [Qt.LeftButton]:
            moveNodes(DOWN)
            return True
        return func(self, event)

    return __nodeInteractionMouseEvent


def nodeInteractionKeyPressEvent(func):
    def __nodeInteractionKeyPressEvent(self, event):
        """ This needs to go here to keep the variable in scope"""
        # Suppress ~ key press
        # This is now handled by the script manager
        # Nodes --> PortSelector
        if event.key() == 96:
            PortConnector.actuateSelection()
            return True

        # updating disable handler
        if event.key() in [Qt.Key_D, Qt.Key_Q] and event.modifiers() == Qt.NoModifier:
            disableNodes()
            return True

        # updating parameter view handler
        if event.key() == Qt.Key_E and event.modifiers() == Qt.NoModifier:
            if event.modifiers() == (Qt.AltModifier | Qt.ShiftModifier):
                displayPopupParameters(hide_on_leave=False)
                return True
            elif event.modifiers() == Qt.AltModifier:
                displayPopupParameters(hide_on_leave=True)
                return True

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

        if event.key() == Qt.Key_N and event.modifiers() == Qt.NoModifier:
            nodegraph_widget = widgetutils.getActiveNodegraphWidget()
            from UIPlugins.NMXMenu import NMXMenuPopulateCallback, NMXMenuActionCallback
            from Katana import LayeredMenuAPI
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


def installNodegraphHotkeyOverrides(**kwargs):
    """ Installs the hotkey overrides """
    # Node interaction key press

    # create proxy nodegraph
    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()

    # NORMAL NODEGRAPH
    node_interaction_layer = nodegraph_widget.getLayerByName("NodeInteractions")

    node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress = nodeInteractionKeyPressEvent(
        NodeInteractionLayer._NodeInteractionLayer__processKeyPress)
    node_interaction_layer.__class__._NodeInteractionLayer__processMouseButtonPress = nodeInteractionMouseEvent(
        NodeInteractionLayer._NodeInteractionLayer__processMouseButtonPress)
    node_interaction_layer.__class__._NodeInteractionLayer__processMouseMove = nodeInteractionLayerMouseMoveEvent(
        NodeInteractionLayer._NodeInteractionLayer__processMouseMove)

    # NETWORK MATERIAL
    nodegraph_view_interaction_layer = nodegraph_widget.getLayerByName("NodeGraphViewInteraction")
    nodegraph_view_interaction_layer.__class__._NodeGraphViewInteractionLayer__processKeyPress = nodeInteractionKeyPressEvent(
        NodeGraphViewInteractionLayer._NodeGraphViewInteractionLayer__processKeyPress)
    nodegraph_view_interaction_layer.__class__._NodeGraphViewInteractionLayer__processMouseButtonDown = nodeInteractionMouseEvent(
        NodeGraphViewInteractionLayer._NodeGraphViewInteractionLayer__processMouseButtonDown)
    nodegraph_view_interaction_layer.__class__._NodeGraphViewInteractionLayer__processMouseMove = nodeInteractionLayerMouseMoveEvent(
        NodeGraphViewInteractionLayer._NodeGraphViewInteractionLayer__processMouseMove)

    # cleanup
    nodegraph_widget.cleanup()