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

from .Node import SuperToolBasicNode as NODE
def EDITOR():
    from .Editor import SuperToolBasicEditor
    return SuperToolBasicEditor
NAME = 'SuperToolBasicExample'
