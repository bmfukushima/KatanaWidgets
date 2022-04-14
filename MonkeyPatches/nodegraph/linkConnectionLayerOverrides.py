from qtpy.QtCore import QTimer, Qt

from Utils2 import nodeutils

from Katana import NodegraphAPI, Utils
from UI4.Tabs.NodeGraphTab.Layers.LinkConnectionLayer import LinkConnectionLayer


# link connection mouse move
def linkConnectionLayerMouseMove(func):
    """ Changes the color of the nearest node """
    def __linkConnectionLayerMouseMove(self, event):
        def colorNearestNode():
            base_ports = self.getBasePorts()
            exclude_nodes = [base_ports[0].getNode()]
            closest_node = nodeutils.getClosestNode(has_input_ports=True, include_dynamic_port_nodes=True,
                                                    exclude_nodes=exclude_nodes)

            # remove old color
            if hasattr(LinkConnectionLayer, "_closest_node"):
                # if closest_node == getattr(LinkConnectionLayer, "_closest_node"): return
                nodeutils.removeGlowColor(LinkConnectionLayer._closest_node)

            # set new color
            if closest_node:
                NodegraphAPI.SetNodeShapeAttr(closest_node, "glowColorR", 0.5)
                NodegraphAPI.SetNodeShapeAttr(closest_node, "glowColorG", 0.5)
                NodegraphAPI.SetNodeShapeAttr(closest_node, "glowColorB", 1)
                Utils.EventModule.QueueEvent('node_setShapeAttributes', hash(closest_node), node=closest_node)

                # update closest node
                LinkConnectionLayer._closest_node = closest_node

        def unfreeze():
            LinkConnectionLayer._is_frozen = False

        delay_amount = 100
        # setup frozen attr
        if not hasattr(LinkConnectionLayer, "_is_frozen"):
            LinkConnectionLayer._is_frozen = False

        # run events on timer
        if not LinkConnectionLayer._is_frozen:
            # setup timer
            timer = QTimer()
            timer.start(delay_amount)
            timer.timeout.connect(unfreeze)
            colorNearestNode()
            # LinkConnectionLayer._is_frozen = True
        # print(event.pos())
        return func(self, event)

    return __linkConnectionLayerMouseMove


def linkConnectionLayerKeyPress(func):
    def __linkConnectionLayerKeyPress(self, event):
        if event.key() == Qt.Key_D:
            if not event.isAutoRepeat():
                self._LinkConnectionLayer__create_dot_node()
                return

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