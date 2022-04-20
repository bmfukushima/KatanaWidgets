import collections

from Katana import LayeredMenuAPI, Utils, NodegraphAPI
from UI4.Tabs.NodeGraphTab.Layers.CustomMenuLayer import CustomMenuLayer
from UI4.App import Tabs

from Utils2 import nodeutils, widgetutils

def menuLayerActionOverride(func):
    def __menuLayerActionOverride(self):
        """ Blocks processing of events if a Custom Layered Menu is not the
        last active layer"""

        # block doubled layered menu events
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
                                    if widgetutils.katanaMainWindow()._is_link_creation_active:
                                        pass
                                        """ Connect here... """

                            if isinstance(newNodes, collections.abc.Sequence):
                                notReplacing = self._MenuLayer__replacedNode is None
                                self._MenuLayer__createdNodes = tuple((n for n in newNodes if isinstance(n, NodegraphAPI.Node)))
                                self.layerStack().placeNodes((self._MenuLayer__createdNodes), shouldFloat=notReplacing,
                                  autoPlaceAllowed=notReplacing)
                            else:
                                self._MenuLayer__createdNodes = tuple()

            finally:
                widgetutils.katanaMainWindow()._is_recursive_layered_menu_event = False
                widgetutils.katanaMainWindow()._is_link_creation_active = False
                Utils.UndoStack.CloseGroup()

        self._MenuLayer__close()
        return

    return __menuLayerActionOverride


def menuLayerCloseOverride(func):
    def __menuLayerCloseOverride(self):
        if not self.layerStack(): return
        return func(self)

    return __menuLayerCloseOverride


def installMenuLayerOverrides(**kwargs):
    """ Installs the custom menu layer event

    Creates a fake nodegraph widget, and then creates a fake layered menu.
    This fake layered menu can then be called to get the base class for the override
    """

    # create proxy nodegraph / layered menu
    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()
    proxy_layered_menu = LayeredMenuAPI.LayeredMenu(lambda _: _, lambda _: _, '')
    nodegraph_widget.showLayeredMenu(proxy_layered_menu)

    # get node interaction layer
    for layer in nodegraph_widget.getLayers():
        layer_name = layer.__module__.split(".")[-1]
        if layer_name == "CustomMenuLayer":
            custom_menu_layer = layer

    # install overrides
    custom_menu_layer.__class__._MenuLayer__action = menuLayerActionOverride(CustomMenuLayer._MenuLayer__action)
    custom_menu_layer.__class__._MenuLayer__close = menuLayerCloseOverride(CustomMenuLayer._MenuLayer__close)

    # cleanup
    nodegraph_widget.cleanup()