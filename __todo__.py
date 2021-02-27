"""
TODO: BUGS
    Wtf is this?
        - QBasicTimer::start: QBasicTimer can only be used with threads started with QThread
        - Systematically disable plugins...
    NodeTree: Auto Create Ports
        - Ask on drop...
        -
        [ERROR python.root]: A TypeError occurred in "nodeutils.py": connect() argument 1 must be Port, not None
            Traceback (most recent call last):
              File "/media/ssd01/dev/katana/KatanaWidgets/SuperTools/NodeTree/Editor.py", line 301, in dropEvent
                nodeutils.connectInsideGroup(node_list, parent_node)
              File "/media/ssd01/dev/katana/KatanaWidgets/Utils2/nodeutils.py", line 68, in connectInsideGroup
                node_list[0].getOutputPortByIndex(0).connect(node_list[1].getInputPortByIndex(0))
            TypeError: connect() argument 1 must be Port, not None
    Desired Nodes
        Nodegraph...
            callback not deleting reference?

TODO: WISHLIST
    Shoji
        - Hotkeys | Don't seem to register correctly with Katana...
            might need wrapper for delegates?
    GSV / IRFs
        - GSV Utils
    Variable Manager New?
        Move this over to Shoji API
    Popup Hotkey Editor
        Move this over to Shoji API
        Beginning of TansuAPI

"""