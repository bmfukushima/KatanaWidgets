""" Overrides the hotkeys for the nodegraph

def test(self, event):
    print("test")

print(layer)

E
Alt+E
Alt+Shift+E
D
Alt+D


"""
from cgwidgets.utils import getWidgetUnderCursor

def __installNodegraphHotkeyOverrides(**kwargs):
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

        return node_interaction_layer.__class__._orig__processKeyPress(self, event)

    # monkey patch
    node_interaction_layer.__class__._orig__processKeyPress = node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress
    node_interaction_layer.__class__._NodeInteractionLayer__processKeyPress = keyPressOverrides

    # cleanup
    nodegraph_widget.cleanup()

def installNodegraphHotkeyOverrides(**kwargs):
    from Katana import Callbacks
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, __installNodegraphHotkeyOverrides)
