""" TODO
        * LinkConnectionLayer
            - Exit remove color
            - How to actually select the compiled class, instead of the default one
        * Refactor
            - folder name --> nodegraphOverrides
            - PortConnection
            - hotkey overrides
"""
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

D / Alt + D
    "Alt + D" moved to "D".
    "D" has been removed.


"""

from qtpy.QtCore import QTimer

from Utils2 import nodeutils

from Katana import NodegraphAPI, Utils
from UI4.Tabs.NodeGraphTab.Layers.LinkConnectionLayer import LinkConnectionLayer

from .nodegraphHotkeyOverrides import installNodegraphHotkeyOverrides
from .linkConnectionLayerOverrides import installLinkConnectionLayerOverrides
# link connection mouse move
def linkConnectionMouseMove(self, event):
    def colorNearestNode():

        closest_node = nodeutils.getClosestNode(has_input_ports=True, include_dynamic_port_nodes=True)
        print(closest_node)
        # remove old color
        if hasattr(LinkConnectionLayer, "_closest_node"):
            # if closest_node == getattr(LinkConnectionLayer, "_closest_node"): return
            NodegraphAPI.SetNodeShapeAttr(LinkConnectionLayer._closest_node, "glowColorR", 0)
            NodegraphAPI.SetNodeShapeAttr(LinkConnectionLayer._closest_node, "glowColorG", 0)
            NodegraphAPI.SetNodeShapeAttr(LinkConnectionLayer._closest_node, "glowColorB", 0)
            Utils.EventModule.QueueEvent('node_setShapeAttributes', hash(LinkConnectionLayer._closest_node), node=LinkConnectionLayer._closest_node)
        # set new color
        NodegraphAPI.SetNodeShapeAttr(closest_node, "glowColorR", 0.5)
        NodegraphAPI.SetNodeShapeAttr(closest_node, "glowColorG", 0.5)
        NodegraphAPI.SetNodeShapeAttr(closest_node, "glowColorB", 1)

        Utils.EventModule.QueueEvent('node_setShapeAttributes', hash(closest_node), node=closest_node)

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

    return LinkConnectionLayer._orig__processMouseMove(self, event)


def installNodegraphOverrides(**kwargs):
    from Katana import Callbacks
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installNodegraphHotkeyOverrides)
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installLinkConnectionLayerOverrides)

