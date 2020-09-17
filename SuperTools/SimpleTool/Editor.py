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
        *   SimpleTool --> Live Group --> Contents of group
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
    QLabel, QVBoxLayout, QWidget
)

from PyQt5.QtCore import Qt, QEvent

from Widgets2 import (
    AbstractNodegraphWidget,
    AbstractParametersDisplayWidget,
    TwoFacedSuperToolWidget
)

from cgwidgets.widgets import BaseTansuWidget

from Katana import UI4


class SimpleToolEditor(TwoFacedSuperToolWidget):
    """
    The top level widget for the editor.  This is here to encapsulate
    the main widget with a stretch box...

    Attributes:
        should_update (bool): determines if this tool should have
            its GUI updated or not during the next event idle process.

    """
    def __init__(self, parent, node):
        super(SimpleToolEditor, self).__init__(parent, node)
        # set up attrs
        self.node = node
        self.main_node = node.getChildByIndex(0)

        self.node_editor = NodeEditor(self, self.node, self.main_node)

        self.getDesignWidget().insertTab(0, 'Params', self.node_editor)
        self.getDesignWidget().insertTab(1, 'Events', QLabel('Events'))
        self.getDesignWidget().insertTab(2, 'GUI Designer', QLabel('GUI Designer'))
        self.getDesignWidget().insertTab(3, 'User Params', QLabel('User Params'))

        self.getDesignWidget().setTabLabelBarToDefaultSize()
        #self.getDesignWidget().show()

    def getEventTypes(self):
        """
        Right now this is just printing out all the different args and what not...
        """
        import json

        with open('args.json', 'r') as args:
            args_dict = json.load(args)
            for event_type in args_dict.keys():
                print('')
                print(event_type, args_dict[event_type]['note'])
                for arg in args_dict[event_type]['args']:
                    arg_name = arg['arg']
                    arg_note = arg['note']
                    print('-----|', arg_name, arg_note)

    def showEvent(self, event):
        self.getDesignWidget().show()
        return TwoFacedSuperToolWidget.showEvent(self, event)


class NodeEditor(BaseTansuWidget):
    def __init__(self, parent, node, main_node):
        super(NodeEditor, self).__init__(parent)
        self.setOrientation(Qt.Vertical)
        self.node = node
        self.main_node = main_node

        # create gui
        self.nodegraph_widget = NodegraphWidget(self, node=node)
        self.parameters_widget = ParametersDisplayWidget(self, node=self.main_node)

        self.addWidget(QLabel("klasjdfklsajflasfklja"))
        self.addWidget(self.nodegraph_widget)
        self.addWidget(self.parameters_widget)

        self.setFocusPolicy(Qt.WheelFocus)


class NodegraphWidget(AbstractNodegraphWidget):
    def __init__(self, parent=None, node=None):
        super(NodegraphWidget, self).__init__(parent)
        # setup attrs
        self.setNode(node)

        AbstractNodegraphWidget.displayMenus(False, self.getPanel())
        self.enableScrollWheel(False)
        self.goToNode(node.getChildByIndex(0))
        self.setupDestroyNodegraphEvent()


class ParametersDisplayWidget(AbstractParametersDisplayWidget):
    """
    The widget that will display all of the parameters to the user.
    """
    def __init__(self, parent=None, node=None):
        super(ParametersDisplayWidget, self).__init__(parent)
        self.node = node
        self.setNodeFilter(self.nodeFilter)
        self.enableSelectionDisplay(True)

    def nodeFilter(self, node):
        """
        Filter for the node list to ensure that the selected nodes are a child of this one

        Args:
            node (Node): The node that is being filtered
        """
        if not node: return False
        if node.getParent() != self.node: return False

        return True
