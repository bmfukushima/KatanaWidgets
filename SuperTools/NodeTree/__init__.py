"""
ToDo:
    NodeTree Base:
        - How to modify delegate?
            SuperToolEditor --> editor --> main_widget
            The ShojiWidget needs to be set as an attr on the class above


"""
from .Node import NodeTreeNode as NODE
def EDITOR():
    from .Editor import NodeTreeEditor
    return NodeTreeEditor
NAME = 'GroupTree'