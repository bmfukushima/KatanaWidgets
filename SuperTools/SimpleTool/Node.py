from Katana import NodegraphAPI

try:
    from Widgets2 import (
        TwoFaceSuperToolNode
    )
except (ImportError, ModuleNotFoundError) as e:
    pass


class SimpleToolNode(TwoFaceSuperToolNode):
    def __init__(self):
        super(SimpleToolNode, self).__init__()
        self.setGroupDisplay(False)

        # add input ports...
        # self.createIOPorts()

        # create main node
        self.main_node = self.createGroupNode(self, 'Basic')

        self.main_node.getInputPortByIndex(0).connect(self.getSendPort('in'))
        self.main_node.getOutputPortByIndex(0).connect(self.getReturnPort('out'))


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

        # wire
        group_node.addOutputPort('out')
        group_node.addInputPort('in')
        group_node.getReturnPort('out').connect(group_node.getSendPort('in'))

        return group_node