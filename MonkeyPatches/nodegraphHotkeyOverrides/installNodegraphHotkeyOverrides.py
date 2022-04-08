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
    PopupTabWidget API
        - leave event
        - toggle hotkey
        - need popup only nodes selected...

D
Alt+D


"""
from qtpy.QtCore import Qt

from Widgets2 import PopupTabWidget


def displayParameters():
    from Katana import NodegraphAPI, Utils
    Utils.UndoStack.OpenGroup('Edit Nodes')
    try:
        for current_nodes in NodegraphAPI.GetAllEditedNodes():
            NodegraphAPI.SetNodeEdited(current_nodes, False)

        for selected_nodes in NodegraphAPI.GetAllSelectedNodes():
            NodegraphAPI.SetNodeEdited(selected_nodes, not NodegraphAPI.IsNodeEdited(selected_nodes))

    finally:
        Utils.UndoStack.CloseGroup()


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
                print("alt + shift + E")
                return True
            elif event.modifiers() == Qt.AltModifier:
                main_window = UI4.App.MainWindow.CurrentMainWindow()
                PopupTabWidget.toggleVisibility("Parameters", size=(750, 1000))
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
