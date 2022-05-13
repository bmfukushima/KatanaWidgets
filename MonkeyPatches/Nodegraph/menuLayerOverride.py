import collections
from qtpy.QtCore import QEvent
from Katana import LayeredMenuAPI, Utils, NodegraphAPI
from UI4.Tabs.NodeGraphTab.Layers.CustomMenuLayer import CustomMenuLayer
from UI4.Tabs.NodeGraphTab.Layers.NodeCreationMenuLayer import NodeCreationMenuLayer
from UI4.Tabs.NodeGraphTab.Layers.LinkConnectionLayer import LinkConnectionLayer
from UI4.App import Tabs

from Utils2 import widgetutils, nodegraphutils

def menuLayerActionOverride(func):
    def __menuLayerActionOverride(self):
        """ Blocks processing of events if a Custom Layered Menu is not the
        last active layer

        For some reason the same code doesn't work... but when I provide the original function it does
        """
        # run default
        if self.layerStack():
            try:
                func(self)
            except:
                pass
        # block doubled layered menu events
        else:
            if self._MenuLayer__matchedEntries:
                entry = self._MenuLayer__matchedEntries[self._MenuLayer__indexOfSelectedEntry]
                Utils.UndoStack.OpenGroup('Layered Menu option: %s' % entry.getText())
                try:
                    prevFloating = set(NodegraphAPI.GetAllFloatingNodes())
                    newNodes = self.onEntryChosen(entry.getValue())

                    #### START INJECTION ####
                    if hasattr(widgetutils.katanaMainWindow(), "_is_recursive_layered_menu_event"):
                        if not widgetutils.katanaMainWindow()._is_recursive_layered_menu_event:
                            #### END INJECTION ####
                            if isinstance(newNodes, NodegraphAPI.Node):
                                newNodes = (
                                 newNodes,)
                            else:
                                if newNodes is None:
                                    nowFloating = set(NodegraphAPI.GetAllFloatingNodes())
                                    newNodes = nowFloating.difference(prevFloating)
                                    newNodes = sorted(newNodes,
                                      key=(lambda node: NodegraphAPI.GetNodePosition(node)[0]))
                                    for newNode in newNodes:
                                        NodegraphAPI.SetNodeFloating(newNode, False)

                                if isinstance(newNodes, collections.abc.Sequence):
                                    notReplacing = self._MenuLayer__replacedNode is None
                                    self._MenuLayer__createdNodes = tuple((n for n in newNodes if isinstance(n, NodegraphAPI.Node)))
                                    self.layerStack().placeNodes((self._MenuLayer__createdNodes), shouldFloat=notReplacing,
                                      autoPlaceAllowed=notReplacing)
                                else:
                                    self._MenuLayer__createdNodes = tuple()

                finally:
                    widgetutils.katanaMainWindow()._is_recursive_layered_menu_event = False
                    Utils.UndoStack.CloseGroup()

            self._MenuLayer__close()
        return

    return __menuLayerActionOverride


def menuLayerCloseOverride(func):
    def __menuLayerCloseOverride(self):
        if not self.layerStack(): return
        return func(self)

    return __menuLayerCloseOverride


def menuLayerProcessEventOverride(func):
    def __menuLayerProcessEventOverride(self, event):
        """ Blocking key release events, to stop release events from triggering different
        parts of the UX.  Specifically on the Node Interaction Layer, for the
        Swipe Gestures vs Key Release Events
        """
        if event.type() == QEvent.KeyRelease:
            return True
        return func(self, event)

    return __menuLayerProcessEventOverride


def nodeEntryChosen(func):
    def __nodeEntryChosen(self, value):
        node = func(self, value)
        #### START INJECTION ####
        """ Inject code to connect nodes when creating nodes via the Tab menu on the LinkConnectionLayer """
        # preflight
        from .linkConnectionLayerOverrides import removeLastActiveNode, lastActiveNode
        if not hasattr(widgetutils.katanaMainWindow(), "_is_link_creation_active"): return node
        if not widgetutils.katanaMainWindow()._is_link_creation_active: return node
        if not hasattr(widgetutils.katanaMainWindow(), "_link_connection_active_node"): return node

        # connect node
        last_active_node = lastActiveNode()

        # connect nodes
        input_port = None
        if len(node.getInputPorts()) == 0:
            if node.getType() in nodegraphutils.dynamicInputPortNodes():
                input_port = node.addInputPort("i0")
        else:
            input_port = node.getInputPortByIndex(0)
        if input_port:
            last_active_node.getOutputPortByIndex(0).connect(input_port)

        # disable attrs

        removeLastActiveNode()

        widgetutils.katanaMainWindow()._is_link_creation_active = False

        #### END INJECTION ####
        return node

    return __nodeEntryChosen


def installMenuLayerOverrides(**kwargs):
    """ Installs the custom menu layer event

    Creates a fake nodegraph widget, and then creates a fake layered menu.
    This fake layered menu can then be called to get the base class for the override
    """

    # create proxy nodegraph / layered menu
    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()

    # create proxy layered menu
    proxy_layered_menu = LayeredMenuAPI.LayeredMenu(lambda _: _, lambda _: _, '')
    nodegraph_widget.showLayeredMenu(proxy_layered_menu)

    # create proxy node create menu
    interaction_layer = nodegraph_widget.getLayerByName("NodeInteractions")
    interaction_layer._NodeInteractionLayer__launchNodeCreationMenuLayer()

    # get node interaction layer
    for layer in nodegraph_widget.getLayers():
        layer_name = layer.__module__.split(".")[-1]
        if layer_name == "CustomMenuLayer":
            custom_menu_layer = layer
        if layer_name == "NodeCreationMenuLayer":
            node_creation_menu_layer = layer

    # install overrides
    custom_menu_layer.__class__._MenuLayer__action = menuLayerActionOverride(custom_menu_layer.__class__._MenuLayer__action)
    custom_menu_layer.__class__.processEvent = menuLayerProcessEventOverride(custom_menu_layer.__class__.processEvent)

    node_creation_menu_layer.__class__._MenuLayer__action = menuLayerActionOverride(node_creation_menu_layer.__class__._MenuLayer__action)
    node_creation_menu_layer.__class__.processEvent = menuLayerProcessEventOverride(node_creation_menu_layer.__class__.processEvent)

    node_creation_menu_layer.__class__.onEntryChosen = nodeEntryChosen(NodeCreationMenuLayer.onEntryChosen)
    # cleanup
    nodegraph_widget.cleanup()