from qtpy.QtCore import Qt, QSize, QPoint, QTimer
from qtpy.QtGui import QCursor

from cgwidgets.utils import scaleResolution
from cgwidgets.settings import iColor

from Widgets2 import PopupWidget, AbstractParametersDisplayWidget
from Utils2 import nodeutils

from Katana import NodegraphAPI, Utils
from UI4.App import Tabs
# from UI4.Tabs.NodeGraphTab.Layers.LinkConnectionLayer import LinkConnectionLayer
from UI4.Tabs.NodeGraphTab.Layers.NodeInteractionLayer import NodeInteractionLayer

from .portConnector import PortConnector

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


def nodeInteractionLayerMouseMove(func):
    """ Changes the color of the nearest node """
    def __nodeInteractionLayerMouseMove(self, event):
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

    return __nodeInteractionLayerMouseMove


def installNodegraphHotkeyOverrides(**kwargs):
    """ Installs the hotkey overrides """
    # Node interaction key press
    def nodeInteractionKeyPress(self, event):
        """ This needs to go here to keep the variable in scope"""
        # Suppress ~ key press
        # This is now handled by the script manager
        # Nodes --> PortSelector
        if event.key() == 96:
            PortConnector.actuateSelection()
            return True

        # updating disable handler
        if event.key() == Qt.Key_D:
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

            displayParameters()
            return True

        if event.key() == Qt.Key_F:
            current_group = self.layerStack().getCurrentNodeView()
            selected_nodes = [x for x in NodegraphAPI.GetAllSelectedNodes() if x.getParent() == current_group]
            if selected_nodes:
                self.frameSelection()
            else:
                self.layerStack().getLayerByName('Frame All').frameAll()
            return True

        if event.key() == Qt.Key_A:
            print('a')
            return True
        if event.key() == Qt.Key_B:
            print("b")
            return True
        return self.__class__._orig__processKeyPress(self, event)
        # return node_interaction_layer.__class__._orig__processKeyPress(self, event)

    # create proxy nodegraph
    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()

    # get node interaction layer
    for layer in nodegraph_widget.getLayers():
        layer_name = layer.__module__.split(".")[-1]
        if layer_name == "NodeInteractionLayer":
            node_interaction_layer = layer
        # if layer_name == "GroupInteractionLayer":
        #     group_interaction_layer = layer


    # key press
    node_interaction_layer.__class__._orig__processKeyPress = node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress
    node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress = nodeInteractionKeyPress

    # mouse move
    node_interaction_layer.__class__._NodeInteractionLayer__processMouseMove = nodeInteractionLayerMouseMove(NodeInteractionLayer._NodeInteractionLayer__processMouseMove)


    # cleanup
    nodegraph_widget.cleanup()