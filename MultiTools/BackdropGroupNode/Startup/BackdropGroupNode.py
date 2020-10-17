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
            # setup default attrs
            katana_main = UI4.App.MainWindow.GetMainWindow()
            if not hasattr(katana_main, '_selected_backdrop_group_registry'):
                katana_main._selected_backdrop_group_registry = []

            # do event stuff
            for arg in args:
                arg = arg[0]
                katana_main = UI4.App.MainWindow.GetMainWindow()
                # Convert backdrop to group
                if arg[0] == 'node_create':
                    node = arg[2]['node']
                    if node.getType() == 'Group':
                        for backdrop_arg in katana_main._selected_backdrop_group_registry:
                            # unzip attrs
                            backdrop_node = backdrop_arg['backdrop']
                            children = backdrop_arg['children']
                            group_node = node

                            # group
                            cls.convertBackdropToGroupNode(backdrop_node, group_node, children)

                # Convert from group to backdrop
                if arg[0] == 'node_delete':
                    node = arg[2]['node']
                    if node.getType() == 'Group':
                        if not cls.isBackdropGroupNode(node):
                            return

                # backdrop selected / deselected
                if arg[0] == 'node_setSelected':
                    """
                    Sets a hidden attr on the Katana main instance that will be a list
                    of all of the current selected Backdrop group nodes
                    """
                    cls.nodeSetSelected()
                    # check selection state


                if arg[0] == 'node_setPosition':
                    # get attrs
                    node = arg[2]['node']

                    # preflight
                    if not cls.isBackdropGroupNode(node): return
                    if node.getType() != "Group": return
                    if not node.getParameter("backdrop"): return

                    # update node positions
                    cls.moveNodes(node)

        @classmethod
        def nodeSetSelected(cls):
            """
            When a node is selected this will look through the selection list
            and repopulate a private attribute on the Katana main instance
            that stores a list of all of the selected backdrop groups.

            """
            katana_main = UI4.App.MainWindow.GetMainWindow()
            katana_main._selected_backdrop_group_registry = []

            for selected_node in NodegraphAPI.GetAllSelectedNodes():
                # preflight
                if selected_node.getType() != "Backdrop": return
                if not cls.isBackdropGroupNode(selected_node): return

                # set node as selected
                cls.__appendBackdropNodeToRegistry(selected_node)

        @classmethod
        def __appendBackdropNodeToRegistry(cls, node):
            from Katana import NodegraphAPI, UI4, DrawingModule
            katana_main = UI4.App.MainWindow.GetMainWindow()

            children = cls.getBackdropChildren(node)
            katana_main._selected_backdrop_group_registry.append(
                {'backdrop': node, 'parent': node.getParent(), 'children': children}
            )

        """ UTILS """
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
        def getBackdropChildren(cls, backdrop_node):
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
        def __addInputPortFromProxyNode(port_map, port_name, proxy_input_port_node):
            port = proxy_input_port_node.getInputPortByIndex(0)
            connect_port = port.getConnectedPorts()[0]
            port_map['input'][port_name] = connect_port

        @staticmethod
        def __createPortMap(input_ports, output_ports, group_node, backdrop_node):
            """
            Creates a dictionary of mappings between a port name and the
            port that it should be connected to.  This is for reconnecting
            the group node once it is created.
            Args:
                input_ports (list): of parameters that are referenced to the name
                    of the nodes being displayed as proxy ports
                output_ports (list): of parameters that are referenced to the name
                    of the nodes being displayed as proxy ports
                group_node (Node): group node that Katana has just created
                    and tried to auto connect stuff with.
                backdrop_node (Node): backdrop group node currently having the
                    port map created on it.
            Returns (dict)
                dict['name':port]
            """
            # create port mapping from custom inputs
            port_map = {}
            port_map['input'] = {}
            port_map['output'] = {}
            for input_port in input_ports:
                port_name = input_port.getValue(0)
                port_node = NodegraphAPI.GetNode(port_name)
                backdropGroup.__addInputPortFromProxyNode(port_map, port_name, port_node)

            for output_port in output_ports:
                name = output_port.getValue(0)
                node = NodegraphAPI.GetNode(name)
                port = node.getOutputPortByIndex(0)
                connect_port = port.getConnectedPorts()[0]
                port_map['output'][name] = connect_port

            # append katana auto created ports
            # needs to map from port node token to output node?
            for port in group_node.getInputPorts():
                # get port name
                for connected_port in group_node.getSendPort(port.getName()).getConnectedPorts():
                    name = connected_port.getNode().getName()
                    # port exists in BG Group
                    if name in [param.getValue(0) for param in input_ports]:
                        # get connected port
                        #connect_port = port.getConnectedPorts()[0]
                        port_map['input'][name] = connected_port
                    else:
                        createBackdropGroupNodeInputPort(backdrop_node)
                        # todo create custom port here
                        # create port
                        # append to port map
                        # position proxy port
                        #   # get backdrop position?
                        # connect proxy port

                        pass

            for port in group_node.getOutputPorts():
                # get port name
                name = port.getName()
                name = group_node.getReturnPort(name).getConnectedPorts()[0].getNode().getName()

                # get connected port
                connect_port = port.getConnectedPorts()[0]
                port_map['output'][name] = connect_port

            return port_map

        @staticmethod
        def __removeExistingPorts(node):
            for input_port in node.getInputPorts():
                node.removeInputPort(input_port.getName())
            for output_port in node.getOutputPorts():
                node.removeOutputPort(output_port.getName())

        def __addAndConnectPortMap(self, port_map):
            pass
        """ EVENTS """
        @classmethod
        def convertBackdropToGroupNode(cls, backdrop_node, group_node, children):
            """
            needs to copy parameters
            relink expressions
            append created ports to input port list
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
            port_map = backdropGroup.__createPortMap(input_ports, output_ports, group_node, backdrop_node)

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
        def moveNodes(cls, node):
            # get backdrop
            backdrop_name = node.getParameter("backdrop").getValue(0)
            backdrop_node = NodegraphAPI.GetNode(backdrop_name)

            # get offset
            old_pos = NodegraphAPI.GetNodePosition(backdrop_node)
            new_pos = NodegraphAPI.GetNodePosition(node)
            offset_x = new_pos[0] - old_pos[0]
            offset_y = new_pos[1] - old_pos[1]

            # get children
            child_node_list = cls.getBackdropChildren(backdrop_node)
            child_node_list.append(backdrop_node)

            # move children to new pos
            for child_node in child_node_list:
                child_pos = NodegraphAPI.GetNodePosition(child_node)
                x = child_pos[0] + offset_x
                y = child_pos[1] + offset_y
                NodegraphAPI.SetNodePosition(child_node, (x, y))

    backdropGroup.mainFunction(*args)

def createBackdropGroupNodeInputPort(backdrop_node):
    """
    Creates a new input port for the backdrop group node.

    Args:
        backdrop_node (Node): Backdrop Group Node to have the new port
            created on it.

    Returns (Node): returns a dot node that is a proxy port to be
        used as the display port
    """
    from Katana import NodegraphAPI, UI4, DrawingModule

    input_ports = backdrop_node.getParameter('user.input_ports')
    array_size = len(input_ports.getChildren())

    # create dot node to use as display for input port
    input_port_display = NodegraphAPI.CreateNode("Dot", backdrop_node.getParent())
    input_port_display.setName('i{i}'.format(i=array_size))
    new_attrs = input_port_display.getAttributes()
    new_attrs['ns_basicDisplay'] = 1
    input_port_display.setAttributes(new_attrs)

    # setup parameters on backdrop and link to dot node
    input_ports.resizeArray(array_size + 1)
    input_port_param = input_ports.getChildByIndex(array_size)
    input_port_param.setExpressionFlag(True)
    input_port_param.setExpression('@{port_name}'.format(port_name=input_port_display.getName()))

    # link dot node to backdrop
    backdrop_node_param = input_port_display.getParameters().createChildString("backdrop", '')
    backdrop_node_param.setExpressionFlag(True)
    backdrop_node_param.setExpression("@{backdrop_name}".format(backdrop_name=node.getName()))

    # float nodes
    UI4.App.Tabs.FindTopTab('Node Graph').floatNodes([input_port_display])

    # set node color
    DrawingModule.SetCustomNodeColor(input_port_display, 0.25, 0.25, 0.5)
    NodegraphAPI.SetNeedsRedraw(True)
    Utils.EventModule.ProcessAllEvents()

    return input_port_display

def installBackdropGroupNode():
    Utils.EventModule.RegisterCollapsedHandler(backdropGroupFunction, 'node_create')
    Utils.EventModule.RegisterCollapsedHandler(backdropGroupFunction, 'node_delete')
    Utils.EventModule.RegisterCollapsedHandler(backdropGroupFunction, 'node_setSelected')
    Utils.EventModule.RegisterCollapsedHandler(backdropGroupFunction, 'node_setPosition')