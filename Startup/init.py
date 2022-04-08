from qtpy.QtCore import Qt
from Katana import Utils, Callbacks

# initialize Bebop Parameter
from Utils2 import paramutils
Callbacks.addCallback(Callbacks.Type.onStartupComplete, paramutils.createKatanaBebopParameter)

# Init Bebop Menu
from ParameterMenu import installCustomParametersMenu
installCustomParametersMenu()


# Need to do this like this... because I'm importing the actual modules over
# these ones =\

# Simple Tools
from MultiTools.SimpleTool import installSimpleTools
installSimpleTools()


# Global Events
from MultiTools.GlobalEventsTab import installGlobalEvents
installGlobalEvents()


# Popup Hotkeys
from MultiTools.ScriptEditorTab import installPopupHotkeysEventFilter
Callbacks.addCallback(Callbacks.Type.onStartupComplete, installPopupHotkeysEventFilter)


# Node Color Registry
from MultiTools.NodeColorRegistryTab import installDefaultNodeColorsEventFilter
installDefaultNodeColorsEventFilter()
# Callbacks.addCallback(Callbacks.Type.onStartupComplete, installDefaultNodeColorsEventFilter)


# GSV Manager
from MultiTools.StateManagerTabs.GSVManagerTab import installGSVManagerEvents
installGSVManagerEvents()
#Callbacks.addCallback(Callbacks.Type.onStartupComplete, installGSVManagerEvents)


# State Manager
from MultiTools.StateManagerTabs import installStateManagerDefaultParam
installStateManagerDefaultParam()


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
from MonkeyPatches import (
    changeFullscreenHotkey,
    changeMinTabSize,
    saveLastActiveBookmark,
    installUserParametersPolicyOverride,
    installNodegraphHotkeyOverrides)

changeFullscreenHotkey(Qt.Key_B)
changeMinTabSize(50)
saveLastActiveBookmark()
installUserParametersPolicyOverride()
installNodegraphHotkeyOverrides()


# update NMC node
def createNMCUtilNodes(*args):
    """
    NMC Hierarchy
    merge
        |-*

    Args:
        *args:

    Returns:

    nmc = NodegraphAPI.GetNode('NetworkMaterialCreate')
    for node in nmc.getChildren():
        if node.getType() == "NetworkMaterial":
            node.getParameters().createChildString("test", "")


    b = NodegraphAPI.GetNode('Material').getParameter('shaders.parameters')
    b.createChildString("test", "")

    def recurseUpNodegraph(node, nodes=None):
        if not nodes:
            nodes = {}

        nodes[node.getType()] = node.getName()
        port = node.getInputPortByIndex(0)

        if len(port.getConnectedPorts()) == 0:
            return nodes

        elif node.getInputPortByIndex(0):
            node = port.getConnectedPorts()[0].getNode()
            return recurseUpNodegraph(node, nodes=nodes)
        else:
            return nodes

    nmc = NodegraphAPI.GetNode('NetworkMaterialCreate')
    merge_node = nmc.getReturnPort("out").getConnectedPorts()[0].getNode()

    for port in merge_node.getInputPorts():
        node = port.getConnectedPorts()[0].getNode()
        nodes = recurseUpNodegraph(node)

        material_node = nodes["Material"]
        network_material_node = nodes["NetworkMaterial"]
        group_stack_node = nodes["GroupStack"]

        print(material_node, network_material_node, group_stack_node)


    """
    from Katana import NodegraphAPI

    def recurseUpNodegraph(node, nodes=None):
        """ Searches up the Nodegraph from a specific node,
        and returns all of the nodes until the connection is broken

        Returns (dict): {node.getType(): node}"""
        if not nodes:
            nodes = {}

        nodes[node.getType()] = node
        port = node.getInputPortByIndex(0)

        if len(port.getConnectedPorts()) == 0:
            return nodes

        elif node.getInputPortByIndex(0):
            node = port.getConnectedPorts()[0].getNode()
            return recurseUpNodegraph(node, nodes=nodes)
        else:
            return nodes

    def createMaterialAssign(network_material_create_node):
        merge_node = network_material_create_node.getReturnPort("out").getConnectedPorts()[0].getNode()

        for input_port in merge_node.getInputPorts():
            output_port = input_port.getConnectedPorts()[0]
            node = output_port.getNode()
            nodes = recurseUpNodegraph(node)

            material_node = nodes["Material"]
            network_material_node = nodes["NetworkMaterial"]
            group_stack_node = nodes["GroupStack"]

            # preflight
            if material_node.getParameter('shaders.parameters.CEL'): continue

            # create material assign
            material_assign_node = NodegraphAPI.CreateNode("MaterialAssign", network_material_create_node)

            # connect
            material_assign_node.getOutputPortByIndex(0).connect(input_port)
            material_assign_node.getInputPortByIndex(0).connect(output_port)

            # setup parameters
            assign_expr = "scenegraphLocationFromNode(getNode(\'{NMC_NODE_NAME}\'))".format(
                NMC_NODE_NAME=network_material_node.getName())
            ma_param = material_assign_node.getParameter("args.materialAssign.value")
            ma_param.setExpressionFlag(True)
            ma_param.setExpression(assign_expr)

            cel_param = material_assign_node.getParameter("CEL")
            cel_param.setExpressionFlag(True)
            cel_param.setExpression(
                "={MATERIAL_NODE_NAME}/shaders.parameters.CEL".format(MATERIAL_NODE_NAME=material_node.getName()))
            #
            material_param = material_node.getParameter('shaders.parameters')
            material_cel_param = material_param.createChildString("CEL", "")
            material_cel_param.setHintString(repr({'widget': 'cel'}))

    def addNMCInputPort(nmc_node):

        # get merge node
        for child in nmc_node.getChildren():
            if child.getType() == "Merge":
                merge_node = child

        # create input port
        input_port = nmc_node.addInputPort("in")

        # get original merge
        # create input port
        # rewire

    for arg in args:
        node = arg[0][2]["node"]
        if "NetworkMaterial" in node.getType():
            # get NMC node
            if node.getType() == "NetworkMaterial":
                if node.getParent().getType() == "NetworkMaterialCreate":
                    network_material_create_node = node.getParent()

            elif node.getType() == "NetworkMaterialCreate":
                network_material_create_node = node

            # create material assign / display param
            createMaterialAssign(network_material_create_node)

