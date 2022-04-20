from qtpy.QtCore import QTimer, Qt

from Utils2 import nodeutils

from Katana import NodegraphAPI, Utils
from UI4.Tabs.NodeGraphTab.Layers.LinkConnectionLayer import LinkConnectionLayer

from .portConnector import PortConnector
from Utils2 import widgetutils


# link connection mouse move
def linkConnectionLayerMouseMove(func):
    """ Changes the color of the nearest node """
    def __linkConnectionLayerMouseMove(self, event):
        def colorNearestNode():
            base_ports = self.getBasePorts()
            exclude_nodes = [base_ports[0].getNode()]
            nodeutils.colorClosestNode(exclude_nodes=exclude_nodes, has_input_ports=True)

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

    return __linkConnectionLayerMouseMove


def linkConnectionLayerKeyPress(func):
    def __linkConnectionLayerKeyPress(self, event):
        if event.key() == Qt.Key_D:
            if not event.isAutoRepeat():
                self._LinkConnectionLayer__create_dot_node()
                return True

        if event.key() == 96:
            """ Note: Recursive selection is handled through the ScriptManager, as for some reason
            ShiftModifier events are not recognized here"""
            # get warning status
            display_warning = True

            if (event.modifiers() & Qt.AltModifier) == Qt.AltModifier:
                display_warning = False

            # actuate
            PortConnector.actuateSelection(display_warning=display_warning, is_recursive_selection=False)

            return True

        if event.key() == Qt.Key_Tab:
            """ Connect last active node/port (dot, or first node selected) to first node created """
            widgetutils.katanaMainWindow()._is_link_creation_active = True
            interaction_layer = self.layerStack().getLayerByName("NodeInteractions")
            interaction_layer._NodeInteractionLayer__launchNodeCreationMenuLayer()
            return True

        func(self, event)
    return __linkConnectionLayerKeyPress


def exitLink(func):
    def removeGlowColor(self, *args):
        if hasattr(LinkConnectionLayer, "_closest_node"):
            nodeutils.removeGlowColor(LinkConnectionLayer._closest_node)
            delattr(LinkConnectionLayer, "_closest_node")
        func(self, *args)
    return removeGlowColor


def installLinkConnectionLayerOverrides(**kwargs):
    """ Installs the overrides for the link connection layer"""

    # link interaction monkey patch
    LinkConnectionLayer._LinkConnectionLayer__processMouseMove = linkConnectionLayerMouseMove(LinkConnectionLayer._LinkConnectionLayer__processMouseMove)
    LinkConnectionLayer._LinkConnectionLayer__processKeyPress = linkConnectionLayerKeyPress(LinkConnectionLayer._LinkConnectionLayer__processKeyPress)

    LinkConnectionLayer._LinkConnectionLayer__connectLinks = exitLink(LinkConnectionLayer._LinkConnectionLayer__connectLinks)
    LinkConnectionLayer._LinkConnectionLayer__dropLinks = exitLink(LinkConnectionLayer._LinkConnectionLayer__dropLinks)
    LinkConnectionLayer._LinkConnectionLayer__exitNoChange = exitLink(LinkConnectionLayer._LinkConnectionLayer__exitNoChange)