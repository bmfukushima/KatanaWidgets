"""
TODO:
    Extract:
        Variable Manager:
            *   Nodegraph Widget
            *   Params display system
            *   Publish System (optional)
        HUD:
            *   UI Create
    Node:
        *   SimpleTools --> Live Group --> Contents of group
        *   Can I just completely overwrite group node/ live group functionality?
    Trigger:
        *   Script Editor
                - Need to refactor this, and make it work with this...
        *   Event Types
                -
        *   --------- Get all args... ---------
                - Hard coded?
            Event Dict {
                event_type: { 'args': [{'arg': argName, 'note': 'description'] , 'note': 'description'},
                event_type: { 'args': [] , 'description': 'note'},
            }
                    [{event_type: {**kwargs}}]
                - Dynamic?
                    - Register dummy, get values, destroy dummy?
                    - Something smarter?
                    - Ask?
        *   Register all Event Types?
                - setupEventHandlers
                    event_types = Utils.EventModule.GetAllRegisteredEventTypes()
                    Utils.EventModule.RegisterCollapsedHandler(
                        self.__undoEventUpdate, 'event_idle', enabled=enabled
                    )
        *   Triggered Function
                - check conditions on args
                - if condition is empty/blank don't count it
                - run python file
                    --------- Pass args to Python file ---------
        *   Args use of Katana Parameters
                - Args need to have a syntax to read parameters on the node
                    so that users can use custom parameters.
                - Can potentially add functionality to Abstract?
                    iParameter interface...
"""

from PyQt5.QtWidgets import (
    QLineEdit, QVBoxLayout
)

from Widgets2 import (
    AbstractSuperToolEditor
)


class SimpleToolsEditor(AbstractSuperToolEditor):
    """
    The top level widget for the editor.  This is here to encapsulate
    the main widget with a stretch box...

    Attributes:
        should_update (bool): determines if this tool should have
            its GUI updated or not during the next event idle process.
    """
    def __init__(self, parent, node):
        super(SimpleToolsEditor, self).__init__(parent, node)
        layout = QVBoxLayout(self)
        test = QLineEdit('test')
        layout.addWidget(test)
