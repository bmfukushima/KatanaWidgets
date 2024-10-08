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

Ctrl + LMB
    Duplicate node selection, or nearest node

- `Alt + LMB` Move all nodes above closest node
- `Alt + Shift + LMB` Move all nodes below closest node
- `A` Alignment Menu
- `S` GSV Popup Menu
- Back/Forward buttons
  - `Back Button` show previous node as view node
  - `Forward Button` show next node view node
  - `Alt + Back Button` show root node as view node
  - `Alt + Forward Button` show parent node as view node
- `Control + G` Show Grid
- `B` Create new backdrop
  - `LMB` Select backdrop and children
  - `Alt + LMB` Select and float backdrop and selected children
  - `Alt + Shift + LMB` Select and float backdrop and all children
  - `Ctrl + LMB` Select / Deselect backdrop
  - `Ctrl + Alt + LMB` Select and float backdrop
  - `Shift + LMB` Append/Remove backdrop and children to current selection
  - `Alt + RMB` Resize backdrop
"""

from .Layers.backdropLayer import installBackdropLayer
from .nodeInteractionLayerOverrides import installNodeInteractionLayerOverrides
from .linkConnectionLayerOverrides import installLinkConnectionLayerOverrides
from .menuLayerOverride import installMenuLayerOverrides
from .zoomInteractionLayerOverrides import installZoomLayerOverrides
from .Layers.gridLayer import installGridLayer
from .Layers.nodeIronLayer import installNodeIronLayer
from .Layers.linkCuttingLayer import installLinkCuttingLayer
from .Layers.swipeConnectionLayer import installSwipeConnectionLayer
from .Layers.selectionLayer import installSelectionLayer
from .Layers.linkSelectionLayer import installLinkSelectionLayer

from Utils2.nodeutils import clearNodePreviewColors

# link connection mouse move
def installNodegraphOverrides(**kwargs):
    from Katana import Callbacks
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installNodeInteractionLayerOverrides)
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installLinkConnectionLayerOverrides)
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installMenuLayerOverrides)
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installZoomLayerOverrides)
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installGridLayer)
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installBackdropLayer)
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installNodeIronLayer)
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installLinkCuttingLayer)
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installSwipeConnectionLayer)
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installSelectionLayer)
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, installLinkSelectionLayer)
    Callbacks.addCallback(Callbacks.Type.onStartupComplete, clearNodePreviewColors)
