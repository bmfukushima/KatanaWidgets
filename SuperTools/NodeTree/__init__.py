"""
ToDo:
    Scripts
        Move to network paths
    Event Registry
        Set up global/local handlers
            - toggle on event widget
            - init script to enable
    Params
        - Input types?
"""
from Node import NodeTreeNode as NODE
def EDITOR():
    from Editor import NodeTreeEditor
    return NodeTreeEditor
NAME = 'NodeTree'