import os, json

from Katana import NodegraphAPI, Utils

try:
    from Widgets2 import TwoFaceSuperToolNode
except:
    pass


class SimpleToolNode(TwoFaceSuperToolNode):
    def __init__(self):
        super(SimpleToolNode, self).__init__()
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

    def eventsData(self):
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

        # wire
        group_node.addOutputPort('out')
        group_node.addInputPort('in')
        group_node.getReturnPort('out').connect(group_node.getSendPort('in'))

        return group_node

    def installEvents(self, *args):
        """
        In charge of installing / uninstalling events.

        This should be called everytime the user hits the update button
        todo
            * should this be a user input?  Or dynamically updating?
            * uninstall event filters
            * items need enabled / disabled flag to call
        """
        events_dict = self.eventsData()
        for key in events_dict:
            event_data = events_dict[key]
            enabled = event_data['enabled']
            event_type = event_data["name"]

            #if event_type in self.eventsData():
            # TODO If already registered creates warning
            try:
                Utils.EventModule.RegisterCollapsedHandler(
                    self.eventHandler, event_type, enabled=enabled
                )
            except ValueError:
                # pass if the handler exists
                pass

    def eventHandler(self, *args, **kwargs):
        """
        This is run every time Katana does an event that is registered with this
        node.  This will filter through the current events dict, and run a script
        based off of the parameters provided.  The event data is provided to this
        script so that all of the variables that are seen can be used inside of the
        script as local variables.

        Duplicate code to EventsWidget --> GlobalEventsWidget --> Event Handler
        TODO: preflight for args...
            do I even need this?  You could do preflight in the script?
        """
        for arg in args:
            arg = arg[0]
            event_type = arg[0]
            event_data = arg[2]

            user_event_data = self.eventsData()
            if event_type in list(user_event_data.keys()):
                user_data = user_event_data[str(event_type)]
                filepath = user_data["filepath"]

                # check params
                if not self.__checkUserData(event_data, user_data): return
                #event_data["self"] = self.node().parent()
                # run script
                if user_data["is_script"]:
                    script = self.paramScripts().getChild(user_data["script"]).getValue(0)
                    exec(script, globals(), event_data)
                # run as filepath
                elif not user_data["is_script"]:
                    if os.path.exists(filepath):
                        with open(filepath) as script_descriptor:
                            event_data['self'] = self.node().getParent()
                            exec(script_descriptor.read(), event_data)

    def __checkUserData(self, event_data, user_data):
        """
        Checks the user data against the event data to determine
        if the the script should be running during an event

        Args:
            event_data (dict):
            user_data (dict):

        Returns (bool):
        """
        # Get Node
        try:
            node_name = user_data["node"]
            node = NodegraphAPI.GetNode(node_name)
        except KeyError:
            node = None

        for key in event_data.keys():
            event_arg_data = event_data[key]
            try:
                user_arg_data = user_data[key]
                #print(key, type(event_data[key]), event_data[key], user_arg_data)

                # Port
                # if isinstance(event_arg_data, "Port"):
                if type(event_arg_data) == "Port":
                    # output = 0
                    # input = 1
                    port_type = event_arg_data.getType()
                    if port_type == 0:
                        port = NodegraphAPI.GetOutputPort(user_arg_data)
                    else:
                        port = NodegraphAPI.GetInputPort(user_arg_data)
                    if port != event_arg_data:
                        return False

                # Param
                # if isinstance(event_arg_data, "Parameter"):
                elif type(event_arg_data) == "Parameter":
                    param = node.getParameter(user_arg_data)
                    if param != event_arg_data:
                        return False
                    pass

                # Node
                elif key == "node":
                    if node:
                        if node != event_arg_data:
                            return False
                    else:
                        return False

                # PyXmlIO

                # default data types
                else:
                    if event_arg_data != user_arg_data:
                        return False

            except KeyError:
                pass

        # passed all checks
        return True

    def disableAllEvents(self, events_dict=None):
        """
        Disables all of the events associated with this EventsWidget.

        If an events_dict is provided, it will disable all of the events in that
        dict, if none is provided it will use the default call to eventsData()

        Args:
            events_dict (dict): associated with eventsData call.
        """
        if not events_dict:
            events_dict = self.eventsData()

        for key in events_dict:
            event_data = events_dict[key]
            event_type = event_data["name"]
            if event_type in self.eventsData():
                Utils.EventModule.RegisterCollapsedHandler(
                    self.eventHandler, event_type, enabled=False
                )

        # update events?
        Utils.EventModule.ProcessAllEvents()