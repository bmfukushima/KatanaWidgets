""" Overrides the hotkeys for the nodegraph

def test(self, event):
    print("test")

print(layer)

E
    Changed from
        Show parameters of nodes the cursor is currently over
            to
        Show parameters of all currently selected nodes

Alt+E / Alt+Shift+E
    Changed from
        Show parameters of selected nodes
            to
        Popup parameter display

D
Alt+D


"""
from qtpy.QtCore import Qt
from Widgets2 import PopupWidget, AbstractParametersDisplayWidget


def displayParameters():
    """ Sets all of the currently selected nodes to being edited """
    from Katana import NodegraphAPI, Utils
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
    from Katana import NodegraphAPI

    # preflight
    selected_nodes = NodegraphAPI.GetAllSelectedNodes()
    if len(selected_nodes) == 0: return

    # construct popup parameters window if it doesn't exist
    if not PopupWidget.doesPopupWidgetExist("popupParameters"):
        widget = AbstractParametersDisplayWidget()
        PopupWidget.constructPopupWidget(
            "popupParameters", widget, size=(0.5, 0.85), hide_hotkey=Qt.Key_E, hide_modifiers=Qt.AltModifier)

    # hide/show popup parameters
    widget = PopupWidget.getPopupWidget("popupParameters")
    widget.setHideOnLeave(hide_on_leave)
    widget.mainWidget().populateParameters(selected_nodes, hide_title=False)
    PopupWidget.togglePopupWidgetVisibility("popupParameters")

def __installNodegraphHotkeyOverrides(**kwargs):
    import UI4
    from UI4.App import Tabs
    # create proxy nodegraph
    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()

    # get node interaction layer
    for layer in nodegraph_widget.getLayers():
        if layer.__module__.split(".")[-1] == "NodeInteractionLayer":
            node_interaction_layer = layer

    def keyPressOverrides(self, event):
        # Suppress ~ key press
        # This is now handled by the script manager
        # Nodes --> PortSelector
        if event.key() == 96: return
        if event.key() == Qt.Key_E:
            if event.modifiers() == (Qt.AltModifier | Qt.ShiftModifier):
                displayPopupParameters(hide_on_leave=False)
                print("alt + shift + E")
                return True
            elif event.modifiers() == Qt.AltModifier:
                displayPopupParameters(hide_on_leave=True)
                print("alt + E")
                return True

            displayParameters()
            return True

        return node_interaction_layer.__class__._orig__processKeyPress(self, event)

    # monkey patch
    node_interaction_layer.__class__._orig__processKeyPress = node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress
    node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress = keyPressOverrides

    # cleanup
    nodegraph_widget.cleanup()

def installNodegraphHotkeyOverrides(**kwargs):
    from Katana import Callbacks
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, __installNodegraphHotkeyOverrides)
