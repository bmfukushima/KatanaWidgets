""" Todo:
        * remove private function
            - keyPress
                - how to suppress menu hotkey events
            - navigation menu
        * navigation menu
            - Fix up button
            - Add alt + button for menu...
        * add cutting widget

Notes:
    In order to create a key + lmb event, you'll need to
        1.) Register key in keypress event with
            nodegraphutils.setCurrentKeyPressed(Qt.Key)
        2.) Register mouse press in nodeInteractionMousePressEvent
        3.) Release key in nodeInteractionMouseReleaseEvent
            Note: you should probably use a timer here, to ensure
                the user actually picks the key up, and a release event doesn't trigger.

Attributes:
    _nodegraph_key_press (Qt.KEY): Currently pressed key (last key if multiple are pressed)
    _node_iron_active (bool): Determines if an ironing event is currently happening
    _node_iron_finishing (bool): Determines if the ironing event is currently finishing
        This will suppress the align menu from being able to be shown for 1 second after
        an ironing event has finished.
"""

import os
import inspect

from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt, QSize, QPoint, QEvent, QTimer
from qtpy.QtGui import QCursor


from Katana import NodegraphAPI, Utils, UI4, DrawingModule, KatanaFile, LayeredMenuAPI, PrefNames, KatanaPrefs
from UI4.App import Tabs

from cgwidgets.utils import scaleResolution
from cgwidgets.settings import iColor
from cgwidgets.widgets import PopupHotkeyMenu

from Widgets2 import PopupWidget, AbstractParametersDisplayWidget
from Utils2 import nodeutils, widgetutils, nodegraphutils

from .gridLayer import GridGUIWidget
from .portConnector import PortConnector
from .backdropLayer import createBackdropNode


""" UTILS """
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
        selected_nodes = list(filter(None, [nodegraphutils.getClosestNode()]))

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
        size = scaleResolution(QSize(600, 425))
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
        popup_widget.setMaskSize(scaleResolution(QSize(600, 850)))
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


def glowNodes(event):
    """ Glows the nodes of the next selection possible selection

    If a combination of Alt | Alt+Shift is used, then it will
    color the upstream/downstream nodes for selection aswell

    note that this also happens in the "nodeInteractionKeyPressEvent"
    """

    """ Need to by pass for special functionality for backdrops"""
    if widgetutils.katanaMainWindow()._node_iron_active: return
    if widgetutils.katanaMainWindow()._link_cutting_active: return
    if widgetutils.katanaMainWindow()._backdrop_resize_active: return

    if event.modifiers() == Qt.NoModifier:
        nodeutils.colorClosestNode(has_output_ports=True)
    backdrop_node = nodegraphutils.getBackdropNodeUnderCursor()
    if backdrop_node:
        # move backdrop
        # if event.modifiers() == (Qt.ControlModifier):
        #     nodeutils.colorClosestNode([backdrop_node])

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
            closest_node = nodegraphutils.getClosestNode(has_input_ports=True)
            if closest_node:
                upstream_nodes = nodegraphutils.getAllUpstreamNodes(closest_node)
                nodeutils.colorClosestNode(upstream_nodes)

        # move downstream nodes
        if event.modifiers() == (Qt.AltModifier | Qt.ShiftModifier):
            closest_node = nodegraphutils.getClosestNode(has_output_ports=True)
            if closest_node:
                downstream_nodes = nodegraphutils.getAllDownstreamNodes(closest_node)
                nodeutils.colorClosestNode(downstream_nodes)


def moveNodes(direction=nodegraphutils.UP):
    """ Selects and moves the nodes upstream or downstream of the selected node """

    node_list = None
    if direction == nodegraphutils.UP:
        closest_node = nodegraphutils.getClosestNode(has_input_ports=True)
        if closest_node:
            node_list = nodegraphutils.getAllUpstreamNodes(closest_node)
    if direction == nodegraphutils.DOWN:
        closest_node = nodegraphutils.getClosestNode(has_output_ports=True)
        if closest_node:
            node_list = nodegraphutils.getAllDownstreamNodes(closest_node)

    if node_list:
        nodegraphutils.selectNodes(node_list)
        nodegraphutils.floatNodes(node_list)


def navigateNodegraph(direction):
    """ Goes back/forward the node hierarchy history

    Args:
        direction (BACK | FORWARD): Determines which way
    """
    nodegraph_widget = widgetutils.getActiveNodegraphWidget()
    navigation_toolbar = nodegraph_widget.parent()._NodegraphPanel__navigationToolbar
    if direction == nodegraphutils.FORWARD:
        navigation_toolbar._NavigationToolbar__forwardButtonClicked()
    elif direction == nodegraphutils.BACK:
        navigation_toolbar._NavigationToolbar__backButtonClicked()
    elif direction == nodegraphutils.HOME:
        nodegraph_widget.setCurrentNodeView(NodegraphAPI.GetRootNode())
    elif direction == nodegraphutils.UP:
        # if nodegraph_widget.getCurrentNodeView() != NodegraphAPI.GetRootNode():
        nodegraph_widget.setCurrentNodeView(nodegraph_widget.getCurrentNodeView().getParent())


""" EVENTS"""
def nodeInteractionEvent(func):
    """ Each event type requires calling its own private methods
    Doing this will probably just obfuscate the shit out of the code...
    """
    def __nodeInteractionEvent(self, event):
        if event.type() == QEvent.MouseButtonPress:
            if nodeInteractionMousePressEvent(self, event): return True
        if event.type() == QEvent.MouseMove:
            if nodeInteractionMouseMoveEvent(self, event): return True
        if event.type() == QEvent.KeyRelease:
            if nodeInteractionKeyReleaseEvent(self, event): return True
        # if event.type() == QEvent.KeyPress:
        #     if nodeInteractionKeyPressEvent(self, event): return True

        return func(self, event)

    return __nodeInteractionEvent


def nodeInteractionMouseMoveEvent(self, event):
    # run functions
    glowNodes(event)

    return False


def nodeInteractionMousePressEvent(self, event):
    # Nodegraph Navigation
    if event.button() == Qt.ForwardButton and event.modifiers() == Qt.NoModifier:
        navigateNodegraph(nodegraphutils.FORWARD)
        return True
    elif event.button() == Qt.BackButton and event.modifiers() == Qt.NoModifier:
        navigateNodegraph(nodegraphutils.BACK)
        return True
    elif event.button() == Qt.ForwardButton and event.modifiers() == Qt.AltModifier:
        print('home')
        navigateNodegraph(nodegraphutils.HOME)
        return True
    elif event.button() == Qt.BackButton and event.modifiers() == Qt.AltModifier:
        navigateNodegraph(nodegraphutils.UP)
        return True

    """ Need to by pass for special functionality for backdrops"""
    backdrop_node = nodegraphutils.getBackdropNodeUnderCursor()
    if not backdrop_node:
        # Duplicate nodes
        if event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier) and event.button() == Qt.LeftButton:
            nodegraphutils.duplicateNodes(self)
            return True

        # select/move nodes above current node
        if event.modifiers() == Qt.AltModifier and event.button() in [Qt.LeftButton]:
            moveNodes(nodegraphutils.UP)
            return True

        # select nodes below current node
        if event.modifiers() == (Qt.AltModifier | Qt.ShiftModifier) and event.button() in [Qt.LeftButton]:
            moveNodes(nodegraphutils.DOWN)
            return True

    return False


def nodeInteractionKeyPressEvent(func):
    def __nodeInteractionKeyPressEvent(self, event):
        """ This needs to go here to keep the variable in scope"""
        if event.isAutoRepeat(): return True
        nodegraphutils.setCurrentKeyPressed(event.key())

        # color node selection
        nodegraph_widget = widgetutils.getActiveNodegraphWidget()
        is_floating = nodegraph_widget.getLayerByName("Floating Nodes").enabled()

        if not is_floating:
            glowNodes(event)

        # Todo: alt/shift ~ modifiers are suppressed somehow this is
        # being handle in the script manager
        # if event.key() == 96 and event.modifiers() == Qt.AltModifier:
        #     print("alt")
        #     return True
        # if event.modifiers() == (Qt.AltModifier | Qt.ShiftModifier):
        #     print("alt + shift")
        #     if event.key() == 96:
        #         print("and press?")
        #         return True
        # if event.modifiers() == (Qt.ShiftModifier):
        #     print("shift")
        #     if event.key() == Qt.Key_A:
        #         print("a")
        #     if event.key() == 96:
        #         print("and press?")
        #         return True

        # # Process Key Presses
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

        if event.key() == Qt.Key_B and event.modifiers() == Qt.NoModifier:
            selected_nodes = NodegraphAPI.GetAllSelectedNodes()
            if len(selected_nodes) == 0:
                createBackdropNode(is_floating=True)
            else:
                createBackdropNode(is_floating=False)
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
                view_node = nodegraphutils.getClosestNode()

            if view_node:
                NodegraphAPI.SetNodeViewed(view_node, True, exclusive=True)

            return True

        return func(self, event)

    return __nodeInteractionKeyPressEvent


def nodeInteractionKeyReleaseEvent(self, event):
    if event.isAutoRepeat(): return True
    if event.key() == Qt.Key_A:
        # display align menu
        if not widgetutils.katanaMainWindow()._node_iron_finishing and not widgetutils.katanaMainWindow()._node_iron_active:
            current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
            file_path = f"{current_dir}/NodeAlignment/AlignNodes.json"
            popup_widget = PopupHotkeyMenu(parent=widgetutils.katanaMainWindow(), file_path=file_path)
            popup_widget.show()

            # need to make sure this releases
            nodegraphutils.setCurrentKeyPressed(None)
            return True

    nodegraphutils.setCurrentKeyPressed(None)

    return False


def showEvent(func):
    def __showEvent(self, event):
        nodegraphutils.setCurrentKeyPressed(None)
        return func(self, event)

    return __showEvent



def installNodeInteractionLayerOverrides(**kwargs):
    """ Installs the hotkey overrides """
    # Node interaction key press

    # create proxy nodegraph
    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()
    nodegraph_widget.__class__.showEvent = showEvent(nodegraph_widget.__class__.showEvent)

    # NORMAL NODEGRAPH
    node_interaction_layer = nodegraph_widget.getLayerByName("NodeInteractions")
    node_interaction_layer.__class__.processEvent = nodeInteractionEvent(node_interaction_layer.__class__.processEvent)
    node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress = nodeInteractionKeyPressEvent(node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress)
    # NETWORK MATERIAL
    nodegraph_view_interaction_layer = nodegraph_widget.getLayerByName("NodeGraphViewInteraction")
    nodegraph_view_interaction_layer.__class__.processEvent = nodeInteractionEvent(nodegraph_view_interaction_layer.__class__.processEvent)

    # cleanup
    nodegraph_widget.cleanup()