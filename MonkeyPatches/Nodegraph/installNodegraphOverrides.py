""" Overrides the hotkeys for the nodegraph

~
    Changed to detect near field detection
    Alt:
        Disable warnings for connected ports
    Shift:
        Continuous selection, will automatically select the port
        of the node connected to.

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

Q / D / Alt + D
    "Alt + D" moved to "D" and "Q"
    "D" has been removed.

W
    Set current resolve node

Shift + MMB
    Duplicate node selection, or nearest node


"""

from .nodeInteractionLayerOverrides import installNodegraphHotkeyOverrides
from .linkConnectionLayerOverrides import installLinkConnectionLayerOverrides
from .menuLayerOverride import installMenuLayerOverrides
# link connection mouse move
def installNodegraphOverrides(**kwargs):
    from Katana import Callbacks
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installNodegraphHotkeyOverrides)
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installLinkConnectionLayerOverrides)
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installMenuLayerOverrides)

