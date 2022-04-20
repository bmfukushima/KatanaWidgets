import os
import inspect

from qtpy.QtCore import Qt, QSize, QPoint, QTimer
from qtpy.QtGui import QCursor

from cgwidgets.utils import scaleResolution
from cgwidgets.settings import iColor
from cgwidgets.widgets import PopupHotkeyMenu

from Widgets2 import PopupWidget, AbstractParametersDisplayWidget
from Utils2 import nodeutils, widgetutils

from Katana import NodegraphAPI, Utils, UI4, DrawingModule
from UI4.App import Tabs

from UI4.Tabs.NodeGraphTab.Layers.NodeInteractionLayer import NodeInteractionLayer
from UI4.Tabs.NodeGraphTab.Layers.StickyNoteInteractionLayer import EditBackdropNodeDialog

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
        if event.key() in [Qt.Key_D, Qt.Key_Q]:
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
            current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
            file_path = f"{current_dir}/NodeAlignment/AlignNodes.json"
            popup_widget = PopupHotkeyMenu(parent=widgetutils.katanaMainWindow(), file_path=file_path)
            popup_widget.show()
            return True

        if event.key() == Qt.Key_B:
            # Todo: popup backdrop dialogue at cursor
            """ For some reason, the preview won't update, and the backdrop needs to be selected to
            toggle an update.  This kinda works for now... and I don't feel like putting any more effort
            into it as it's clearly a not my problem bug.
            """
            Utils.UndoStack.OpenGroup("Create Backdrop")


            # create backdrop and fit around selection
            current_group = self.layerStack().getCurrentNodeView()
            backdrop_node = NodegraphAPI.CreateNode("Backdrop", current_group)
            NodegraphAPI.SetNodeSelected(backdrop_node, True)
            self.layerStack().fitBackdropNode()

            # prompt user for setting the node color
            def previewCallback(node, attrDict):
                for attrName, attrValue in attrDict.items():
                    nodegraph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()

                    DrawingModule.nodeWorld_setShapeAttr(node, attrName, attrValue)
                    DrawingModule.nodeWorld_setShapeAttr(node, "update", 1)
                    # this gives us live updates
                    nodegraph_widget.idleUpdate()

            d = EditBackdropNodeDialog(backdrop_node, previewCallback=previewCallback)
            d.exec_()
            d.close()
            d.move(QCursor.pos())
            Utils.UndoStack.CloseGroup()

            return True

        if event.key() == Qt.Key_W:
            selected_nodes = NodegraphAPI.GetAllSelectedNodes()
            view_node = None
            if selected_nodes:
                view_node = selected_nodes[0]
            else:
                view_node = nodeutils.getClosestNode()

            if view_node:
                NodegraphAPI.SetNodeViewed(view_node, True, exclusive=True)

            return True

        return self.__class__._orig__processKeyPress(self, event)

    # create proxy nodegraph
    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()

    # get node interaction layer
    for layer in nodegraph_widget.getLayers():
        layer_name = layer.__module__.split(".")[-1]
        if layer_name == "NodeInteractionLayer":
            node_interaction_layer = layer

    # key press
    node_interaction_layer.__class__._orig__processKeyPress = node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress
    node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress = nodeInteractionKeyPress

    # mouse move
    node_interaction_layer.__class__._NodeInteractionLayer__processMouseMove = nodeInteractionLayerMouseMove(NodeInteractionLayer._NodeInteractionLayer__processMouseMove)


    # cleanup
    nodegraph_widget.cleanup()