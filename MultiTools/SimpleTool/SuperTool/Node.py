import os, json
from qtpy import API_NAME

from Katana import NodegraphAPI, Utils

try:
    from Widgets2 import TwoFaceSuperToolNode, EventInterface
    from Utils2 import paramutils
except:
    pass

PARAM_LOCATION = "events_data"


class SimpleToolNode(TwoFaceSuperToolNode, EventInterface):
    def __init__(self):
        super(SimpleToolNode, self).__init__()
        if API_NAME == "PySide2":
            EventInterface.__init__(self)
        self.setGroupDisplay(False)

        # add input ports...
        # nodeutils.createIOPorts()

        # create main node
        self._main_node = self.createGroupNode(self, 'Basic')
        param = self.getParameters().createChildString("node", "")
        param.setExpressionFlag(True)
        param.setExpression("@{node}".format(node=self._main_node.getName()))

        self._main_node.getInputPortByIndex(0).connect(self.getSendPort('in'))
        self._main_node.getOutputPortByIndex(0).connect(self.getReturnPort('out'))

        self.installEvents()

    def paramScripts(self):
        return self.mainNode().getParameter("events_data.scripts")

    def eventsData(self, **kwargs):
        return json.loads(self.mainNode().getParameter("events_data.data").getValue(0))

    def mainNode(self):
        return NodegraphAPI.GetNode(self.getParameter("node").getValue(0))

    @staticmethod
    def createGroupNode(parent_node, name=''):
        """
        Creates an empty group node to be used as a container for other things...

        Args:
            parent_node (node)
            name (str)

        Returns:
            node (Group Node)
        """
        # create node
        group_node = NodegraphAPI.CreateNode('Group', parent_node)

        # set params
        group_node.setName(name)
        paramutils.createParamAtLocation(PARAM_LOCATION+".data", group_node, paramutils.STRING, initial_value="{}")
        paramutils.createParamAtLocation(PARAM_LOCATION+".scripts", group_node, paramutils.GROUP)

        # wire
        group_node.addOutputPort('out')
        group_node.addInputPort('in')
        group_node.getReturnPort('out').connect(group_node.getSendPort('in'))

        return group_node

    def saveEventsData(self):
        # dummy function to please the interface
        pass

