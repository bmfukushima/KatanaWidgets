from Katana import Callbacks, Utils

""" BACK DROP"""


def backdropGroupFunction(*args):
    from Katana import NodegraphAPI, UI4, DrawingModule

    class backdropGroup(object):
        def __init__(self):
            pass

        @classmethod
        def mainFunction(cls, *args):
            from Katana import NodegraphAPI, UI4, DrawingModule
            katana_main = UI4.App.MainWindow.GetMainWindow()
            if not hasattr(katana_main, 'selected_backdrop_group_list'):
                katana_main.selected_backdrop_group_list = []
            print ('agogo')
            for arg in args:
                arg = arg[0]
                katana_main = UI4.App.MainWindow.GetMainWindow()
                # Convert backdrop to group
                if arg[0] == 'node_create':
                    node = arg[2]['node']
                    if node.getType() == 'Group':
                        for backdrop_arg in katana_main.selected_backdrop_group_list:
                            backdrop_node = backdrop_arg['backdrop']
                            children = backdrop_arg['children']
                            group_node = node

                            # group
                            cls.convertBackdropToGroupNode(backdrop_node, group_node, children)

                # Convert from group to backdrop
                if arg[0] == 'node_delete':
                    node = arg[2]['node']
                    if node.getType() == 'Group':
                        pos = NodegraphAPI.GetNodePosition(node)

                # backdrop selected / deselected
                if arg[0] == 'node_setSelected':
                    """
                    Sets a hidden attr on the Katana main instance that will be a list
                    of all of the current selected Backdrop group nodes
                    """

                    # check selection state
                    katana_main.selected_backdrop_group_list = []
                    for selected_node in NodegraphAPI.GetAllSelectedNodes():
                        # preflight
                        if selected_node.getType() != "Backdrop": return
                        if not cls.isBackdropGroupNode(selected_node): return

                        # set node as selected
                        cls.selectBackdropNode(selected_node)

                    # node = arg[2]['node']
                    # is_backdrop_node = cls.isBackdropGroupNode(node)
                    # if is_backdrop_node:
                    #     if node.getType() == "Backdrop":
                    #         # selected
                    #         if node in NodegraphAPI.GetAllSelectedNodes():
                    #             cls.selectBackdropNode(node)
                    #
                    #         # deselected
                    #         else:
                    #             cls.deselectBackdropNode(node)

                if arg[0] == 'node_setPosition':
                    node = arg[2]['node']
                    is_backdrop_node = cls.isBackdropGroupNode(node)
                    if is_backdrop_node:
                        if node.getType() == "Group":
                            if node.getParameter("backdrop"):
                                # TODO Update internal nodes positions
                                backdrop_name = node.getParameter("backdrop").getValue(0)
                                backdrop_node = NodegraphAPI.GetNode(backdrop_name)
                                pos = NodegraphAPI.GetNodePosition(node)
                                NodegraphAPI.SetNodePosition(backdrop_node, pos)
                    # is group
                    # set backdrop?
                    # if is_backdrop_node:

        @classmethod
        def isBackdropGroupNode(cls, node):
            """
            Determines if the node is flagged as a backdrop group node.

            Args:
                node (Node): node to check to see if it is a backdrop group
            """
            # if node.getType() == "Backdrop":
            if node.getParameter("is_backdrop_group"):
                return True
            return False

        @classmethod
        def get_backdrop_children(cls, backdrop_node):
            """
            Gets all of the children that a full encompassed by the backdrop node.

            Args:
                backdrop_node (Node): a node of type "Backdrop"

            Returns (list): of nodes
            """
            from Katana import NodegraphAPI, UI4, DrawingModule

            # get nodegraph
            ng = UI4.App.Tabs.FindTopTab('Node Graph')
            widget = ng.getNodeGraphWidget()

            l, b, r, t = DrawingModule.nodeWorld_getBoundsOfListOfNodes([backdrop_node])
            children = widget.hitTestBox(
                (l, b),
                (r, t),
                viewNode=backdrop_node.getParent()
            )

            # remove backdrop
            children.remove(backdrop_node)
            return children

        @staticmethod
        def __createPortMap(input_ports, output_ports):
            """
            Creates a dictionary of mappings between a port name and the
            port that it should be connected to.  This is for reconnecting
            the group node once it is created.
            Args:
                input_ports (list): of parameters that are referenced to the name
                    of the nodes being displayed as proxy ports
                output_ports (list): of parameters that are referenced to the name
                    of the nodes being displayed as proxy ports

            Returns (dict)
                dict['name':port]
            """
            # create port mapping
            port_map = {}
            port_map['input'] = {}
            port_map['output'] = {}
            for input_port in input_ports:
                name = input_port.getValue(0)
                node = NodegraphAPI.GetNode(name)
                port = node.getInputPortByIndex(0)
                connect_port = port.getConnectedPorts()[0]
                port_map['input'][name] = connect_port

            for output_port in output_ports:
                name = output_port.getValue(0)
                node = NodegraphAPI.GetNode(name)
                port = node.getOutputPortByIndex(0)
                connect_port = port.getConnectedPorts()[0]
                port_map['output'][name] = connect_port

            return port_map

        @staticmethod
        def __removeExistingPorts(node):
            for input_port in node.getInputPorts():
                node.removeInputPort(input_port.getName())
            for output_port in node.getOutputPorts():
                node.removeOutputPort(output_port.getName())

        @classmethod
        def convertBackdropToGroupNode(cls, backdrop_node, group_node, children):
            """
            """
            # setup reference to backdrop node
            node_ref = group_node.getParameters().createChildString('backdrop', '')
            node_ref.setExpressionFlag(True)
            node_ref.setExpression('@{backdrop}'.format(backdrop=backdrop_node.getName()))

            # set is backdrop group flag
            group_node.getParameters().createChildString('is_backdrop_group', 'Yeapppppppppppp')

            # create map from backdrop node of connected ports
            """
            If all the nodes are selected, you'll need to find the port mapping list from the
            group node, before all the ports are deleted.

            If only the backdrop is selected, then the port mapping will be done from the back
            drop nodes list of ports

            Ideally you will query both, but this example is getting pretty long...
            """
            output_ports = backdrop_node.getParameter('user.output_ports').getChildren()
            input_ports = backdrop_node.getParameter('user.input_ports').getChildren()

            # create port map
            port_map = backdropGroup.__createPortMap(input_ports, output_ports)

            # remove existing ports ( katana will auto create these for us )
            backdropGroup.__removeExistingPorts(group_node)

            # this is kinda lazy
            # create output ports
            for output_port in output_ports:
                name = output_port.getValue(0)

                proxy_port_node = NodegraphAPI.GetNode(name)

                group_node.addOutputPort(name)

                group_node.getReturnPort(name).connect(proxy_port_node.getOutputPortByIndex(0))

                group_node.getOutputPort(name).connect(port_map['output'][name])

            # create input ports
            for input_port in input_ports:
                name = input_port.getValue(0)
                proxy_port_node = NodegraphAPI.GetNode(name)

                group_node.addInputPort(name)
                group_node.getSendPort(name).connect(proxy_port_node.getInputPortByIndex(0))

                group_node.getInputPort(name).connect(port_map['input'][name])

            # reparent all children
            for child_node in children:
                child_node.setParent(group_node)

        @classmethod
        def selectBackdropNode(cls, node):
            from Katana import NodegraphAPI, UI4, DrawingModule
            katana_main = UI4.App.MainWindow.GetMainWindow()

            children = cls.get_backdrop_children(node)
            katana_main.selected_backdrop_group_list.append(
                {'backdrop': node, 'parent': node.getParent(), 'children': children}
            )

        # @classmethod
        # def deselectBackdropNode(cls, node):
        #     katana_main = UI4.App.MainWindow.GetMainWindow()
        #     node_list = katana_main.selected_backdrop_group_list
        #     for index, backdrop_arg in enumerate(node_list):
        #         if backdrop_arg['backdrop'] == node:
        #             if node.getParent() == backdrop_arg['backdrop'].getParent():
        #                 katana_main.selected_backdrop_group_list.pop(index)
        #
        #                 print('removing %s'%backdrop_arg['backdrop'])

    backdropGroup.mainFunction(*args)


def installBackdropGroupNode():
    print('1')
    Utils.EventModule.RegisterCollapsedHandler(backdropGroupFunction, 'node_create')
    Utils.EventModule.RegisterCollapsedHandler(backdropGroupFunction, 'node_delete')
    Utils.EventModule.RegisterCollapsedHandler(backdropGroupFunction, 'node_setSelected')
    Utils.EventModule.RegisterCollapsedHandler(backdropGroupFunction, 'node_setPosition')