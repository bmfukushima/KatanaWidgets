from Katana import Utils, Callbacks
from qtpy.QtCore import Qt
# initialize bebop menu
from ParameterMenu import installCustomParametersMenu
installCustomParametersMenu()

# Simple Tools
from MultiTools.SimpleTool import installBebopGlobalEvents
installBebopGlobalEvents()


# Variable Switch | Populate
def contextMenu(**kwargs):
    from Katana import NodegraphAPI
    from UI4.FormMaster.NodeActionDelegate import (BaseNodeActionDelegate, RegisterActionDelegate)
    from UI4.Manifest import QtWidgets

    class UpdateGSVOptions(BaseNodeActionDelegate.BaseNodeActionDelegate):
        class _addAllGSVOptions(QtWidgets.QAction):
            def __init__(self, parent, node):
                # set node to private attribute
                self.__node = node

                # set menu display text
                var_name = self.__node.getParameter('variableName').getValue(0)
                QtWidgets.QAction.__init__(self, 'Add all GSV options for %s'%var_name, parent)

                # connect signal
                if node:
                    self.triggered.connect(self.__triggered)

                self.setEnabled(self.__node is not None
                                and not self.__node.isLocked(True))

            def __triggered(self):
                # get node data
                variable_switch = self.__node
                variable_name = variable_switch.getParameter('variableName').getValue(0)
                variable_patterns_parm = variable_switch.getParameter('patterns')
                gsv_parm = NodegraphAPI.GetNode('rootNode').getParameter('variables.%s'%variable_name)

                if gsv_parm:
                    # delete previous ports and patterns
                    # remove all input ports
                    for port in variable_switch.getInputPorts():
                        variable_switch.removeInputPort(port.getName())
                    # remove all child parameters
                    for child in variable_patterns_parm.getChildren():
                        variable_patterns_parm.deleteChild(child)

                    for child in gsv_parm.getChild('options').getChildren():
                        # create new port with pattern
                        name = child.getValue(0)
                        # mechanic on the variable switch will automagically create the
                        # parameters when you create the port
                        variable_switch.addInputPort(name)

        def addToContextMenu(self, menu, node):
            menu.addAction(self._addAllGSVOptions(menu, node))

    RegisterActionDelegate("VariableSwitch", UpdateGSVOptions())


Callbacks.addCallback(Callbacks.Type.onStartupComplete, contextMenu)

# change full screen hotkey
from MonkeyPatches import changeFullscreenHotkey
changeFullscreenHotkey(Qt.Key_B)

