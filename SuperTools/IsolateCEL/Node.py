"""
TODO:
    *   Prioritize which order the isolation will work
            - The safe locations/attribute set nodes order will determine
                how the isolate works.
                    IF the attribute set is first, this will prioritize stuff
                        that is lower in the hierachy...
                    IF th
"""

from Katana import NodegraphAPI, Widgets, PyXmlIO, Utils

try:
    from Widgets2 import AbstractSuperToolNode
    from Utils2 import nodeutils
except:
    pass


class IsolateCELNode(AbstractSuperToolNode):
    """ The IsoleCELNode creates an Isolate node which accepts CEL inputs

    This works by creating an arbitrary attribute under the nodes name
    which will have all of the CEL locations the user provides in it.  Each location
    the user inputs will have the attribute set as 0, while the parent locations
    reaching up to "isolateFrom" will have a value of 1.  The OpScript can then go in
    and remove all the locations that don't have this attribute.

    Nodes:
        attribute_set_node (AttributeSet):
        safe_locations_node (AttributeSet):
        opscript_node (OpScript):
        cleanup_attrs_node (AttributeSet):"""
    def __init__(self):
        super(IsolateCELNode, self).__init__()

        # initialize base node
        self.setGroupDisplay(False)
        nodeutils.createIOPorts(self)
        self.__initParams()
        self.__initNodes()
        Utils.EventModule.RegisterCollapsedHandler(self.celChanged, "parameter_finalizeValue", enabled=True)

    def __initParams(self):
        # create user parameters
        self._cel_param = self.getParameters().createChildString("CEL", "")
        self._cel_param.setHintString(repr({"widget": "cel"}))

        self._isolate_from_param = self.getParameters().createChildString("isolateFrom", "/root/world")
        self._isolate_from_param.setHintString(repr({"widget": "scenegraphLocation"}))

        node_name = self.getParameters().createChildString("nodeName", "")
        node_name.setExpressionFlag(True)
        node_name.setExpression("@{name}".format(name=self.getName()))

    def __initNodes(self):
        # create nodes
        self._attribute_set_node = NodegraphAPI.CreateNode("AttributeSet", self)
        self._safe_locations_node = NodegraphAPI.CreateNode("AttributeSet", self)
        self._opscript_node = self.__createOpScriptNode()
        self._cleanup_attrs_node = NodegraphAPI.CreateNode("AttributeSet", self)

        # set node names
        self._attribute_set_node.setName("SetIsolateAttr")
        self._safe_locations_node.setName("SetSafeLocationsAttr")
        self._opscript_node.setName("IsolateCEL")
        self._cleanup_attrs_node.setName("DeleteIsolateAttr")

        # connect nodes
        self._safe_locations_node.getInputPortByIndex(0).connect(self.getSendPort("in"))
        self._safe_locations_node.getOutputPortByIndex(0).connect(self._attribute_set_node.getInputPortByIndex(0))
        self._attribute_set_node.getOutputPortByIndex(0).connect(self._opscript_node.getInputPortByIndex(0))
        self._opscript_node.getOutputPortByIndex(0).connect(self._cleanup_attrs_node.getInputPortByIndex(0))
        self._cleanup_attrs_node.getOutputPortByIndex(0).connect(self.getReturnPort("out"))

        # position nodes
        NodegraphAPI.SetNodePosition(self._safe_locations_node, (0, 0))
        NodegraphAPI.SetNodePosition(self._attribute_set_node, (0, -100))
        NodegraphAPI.SetNodePosition(self._opscript_node, (0, -200))
        NodegraphAPI.SetNodePosition(self._cleanup_attrs_node, (0, -300))

        # link parameters
        # attr set node
        name_param = self._attribute_set_node.getParameter('attributeName')
        name_param.setExpressionFlag(True)
        name_param.setExpression("@{name}".format(name=self.getName()))
        self._attribute_set_node.getParameter('attributeType').setValue("integer", 0)
        self._attribute_set_node.getParameter('numberValue.i0').setValue(0, 0)

        # attr cleanup node
        name_param = self._cleanup_attrs_node.getParameter('attributeName')
        self._cleanup_attrs_node.getParameter('action').setValue("Delete", 0)
        name_param.setExpressionFlag(True)
        name_param.setExpression("@{name}".format(name=self.getName()))
        self._cleanup_attrs_node.getParameter('attributeType').setValue("integer", 0)

        # safe attrs node
        name_param = self._safe_locations_node.getParameter('attributeName')
        name_param.setExpressionFlag(True)
        name_param.setExpression("@{name}".format(name=self.getName()))
        self._safe_locations_node.getParameter('attributeType').setValue("integer", 0)
        self._safe_locations_node.getParameter('numberValue.i0').setValue(1, 0)

    def __createOpScriptNode(self):
        """ Helper function to create the OpScript node."""
        opscript_node = NodegraphAPI.CreateNode("OpScript", self)
        opscript_node.setBypassed(True)
        cel_param = opscript_node.getParameter("CEL")
        cel_param.setExpressionFlag(True)
        cel_param.setExpression("=^/isolateFrom + \"//*\"")

        opscript_node.getParameters().createChildGroup("user")
        isolate_name_param = opscript_node.getParameter("user").createChildString("isolateName", "")
        isolate_name_param.setExpressionFlag(True)
        isolate_name_param.setExpression("@{name}".format(name=self.getName()))

        script = """
location = Interface.GetInputLocationPath()
attribute_name = Interface.GetOpArg("user.isolateName"):getValue()
attr = Interface.GetAttr(attribute_name, location)

if attr == nil then
    Interface.DeleteSelf()
else
    if attr:getValue() == 0 then
        Interface.StopChildTraversal()
    end
end
        """
        opscript_node.getParameter('script.lua').setValue(script, 0)

        return opscript_node

    """ UTILS """
    def celChanged(self, args):
        """ Check for user updates to the CEL or isolateFrom params """
        for arg in args:
            # preflight
            # get param
            param = arg[2]["param"]
            node = arg[2]["node"]
            if node == self and (param == self._cel_param or param == self._isolate_from_param):
                isolate_locations = self.resolveCELPaths()
                upstream_locations = self.getAllUpstreamLocations()
                self.updateAttributeLocations(isolate_locations, upstream_locations)

                # enable/disable opscript node depending on selection count
                if len(isolate_locations) == 0:
                    self.opScriptNode().setBypassed(True)
                else:
                    self.opScriptNode().setBypassed(False)

    def updateAttributeLocations(self, isolate_locations, upstream_locations):
        """ Updates all of the paths in all of the AttributeSet nodes

        Args:
            isolate_locations (list): of user defined scenegraph locations
            upstream_locations (list): of scenegraph locations that are ancestors
                of the user defined locations which goes up to the isolateFrom location
        """
        # update safe groups attr
        param = self.safeLocationsNode().getParameter("paths")
        element = param.buildXmlIO(True)
        element.removeAllChildren()
        for path in upstream_locations:
            child = element.addChild(PyXmlIO.Element("string_parameter"))
            child.setAttr("name", "i%i" % (len(element) - 1))
            child.setAttr("value", path)
        element.setAttr("size", len(element))
        param.parseXmlIO(element)

        # attr set node
        param = self.attributeSetNode().getParameter("paths")
        element = param.buildXmlIO(True)
        element.removeAllChildren()
        for path in isolate_locations:
            child = element.addChild(PyXmlIO.Element("string_parameter"))
            child.setAttr("name", "i%i" % (len(element) - 1))
            child.setAttr("value", path)
        element.setAttr("size", len(element))
        param.parseXmlIO(element)

        # cleanup attrs node
        param = self.cleanupAttrsNode().getParameter("paths")
        element = param.buildXmlIO(True)
        element.removeAllChildren()
        for path in (isolate_locations + upstream_locations):
            child = element.addChild(PyXmlIO.Element("string_parameter"))
            child.setAttr("name", "i%i" % (len(element) - 1))
            child.setAttr("value", path)
        element.setAttr("size", len(element))
        param.parseXmlIO(element)

    def resolveCELPaths(self):
        """ Resolves the users CEL statement to absolute paths

        Returns (list): of strings"""
        # resolve cel statements
        node = self.attributeSetNode()

        cel_statement = self._cel_param.getValue(0)
        isolate_from = self._isolate_from_param.getValue(0)

        collector = Widgets.CollectAndSelectInScenegraph(cel_statement, isolate_from)
        resolved_cel_locations = collector.collectAndSelect(select=False, node=node)
        return resolved_cel_locations

    def getAllUpstreamLocations(self):
        """ Gets all of the upstream locations from the resolved CEL

        Adding the attribute to these locations is needed to ensure that
        they're not pruned out during the resolve"""
        # get attrs
        resolved_cel_locations = self.resolveCELPaths()
        isolate_from = self._isolate_from_param.getValue(0)

        # search up cel list to get all parents
        ancestors_list = []
        for path in resolved_cel_locations:
            parents = path.replace(isolate_from, "")
            parents = parents.split("/")[:-1]
            parents = filter(None, parents)
            current_location = isolate_from
            for location in parents:
                current_location += "/" + location
                ancestors_list.append(current_location)

        return list(set(ancestors_list))

    """ NODES """
    def cleanupAttrsNode(self):
        return self._cleanup_attrs_node

    def attributeSetNode(self):
        return self._attribute_set_node

    def opScriptNode(self):
        return self._opscript_node

    def safeLocationsNode(self):
        return self._safe_locations_node