def createKatanaBebopParameter(*args, **kwargs):
    from Katana import NodegraphAPI
    root_node = NodegraphAPI.GetRootNode()
    if not root_node.getParameter("KatanaBebop"):
        root_node.getParameters().createChildGroup("KatanaBebop")

STRING = 0
NUMBER = 1
GROUP = 2
NUMBER_ARRAY = 3
STRING_ARRAY = 4
TELEPARAM = 5

def createParamAtLocation(param_location, node, param_type, param=None, initial_value=0):
    """Creates a parameter of the supplied type at the location provided.

    This will create also create all additional groups/locations required
    to create the parameter.

    This will not override an existing parameter.  Could potentially add this option.

    Args:
        initial_value (str/int): what the initial value should be, if the param type is
            set to an ARRAY, then this will be the length of the array
        node (node): node to create param on
        param (param): to start creating param from
        param_location (str): location to parameter with '.' used as separators
            param.group.location.param
        param_type (TYPE): type of parameter to create, valid options are
            STRING | NUMBER | GROUP | NUMBER_ARRAY | STRING_ARRAY

    Returns (param):

    """
    # get initial param
    if param:
        current_param = param
        orig_param = param
    else:
        current_param = node.getParameters()
        orig_param = node.getParameters()

    try:
        # create group parameters
        current_location = []
        for group_name in param_location.split('.')[:-1]:

            # create param
            if not current_param.getChild(group_name):
                current_param.createChildGroup(group_name)

            # set current param
            current_location.append(group_name)
            current_param = orig_param.getChild(".".join(current_location))

        # create parameter
        param_name = param_location.split('.')[-1]
        if not current_param.getChild(param_name):
            if param_type == STRING:
                param = current_param.createChildString(param_name, str(initial_value))
            if param_type == NUMBER:
                param = current_param.createChildNumber(param_name, float(initial_value))
            if param_type == GROUP:
                param = current_param.createChildGroup(param_name)
            if param_type == NUMBER_ARRAY:
                param = current_param.createChildNumberArray(param_name, 0)
            if param_type == STRING_ARRAY:
                param = current_param.createChildStringArray(param_name, 0)
            if param_type == TELEPARAM:
                param = current_param.createChildString(param_name, str(initial_value))
                param.setHintString(repr({"widget": "teleparam"}))
            return param

    except TypeError:
        print(current_param.getFullName(), "already exists")

def createTeleparamWidget(node_name, hide_title=False):
    """
    Creates a teledrop parameter widget

    Args:
        *   node_name (str): name of node to be referenced
        **  hide_title (bool): Determines if the title of the parameter will be hidden.
                If there is more than one parameter, the title will not be hidden,
                if there is only 1 then it will be hidden.

    Returns:
        teledropparam
    """
    from Katana import UI4, QT4FormWidgets
    policyData = dict(displayNode="")
    rootPolicy = QT4FormWidgets.PythonValuePolicy("cels", policyData)
    params_policy = rootPolicy.getChildByName("displayNode")
    params_policy.getWidgetHints().update(
        widget='teleparam',
        open="True",
        hideTitle=repr(hide_title)
    )
    param_widget = UI4.FormMaster.KatanaWidgetFactory.buildWidget(None, params_policy)
    params_policy.setValue(node_name, 0)
    return param_widget

def createNodeReference(name, node, parent):
    """ Creates a parameter reference to the node provided

    Args:
        name (str): name of parameter
        node (Node): node to reference
        parent (param): Group param to parent children under

    Returns (param): newly created String Parameter"""
    param = parent.createChildString(name, "")
    param.setExpressionFlag(True)
    param.setExpression("@{node}".format(node=node.getName()))
    return param

def getParameterMapFromNode(node):
        """ Returns a dictionary of the parameter map for each parameter on the node

        Args:
            node (Node):

        Returns (dict):
            str(param_name): (value)"""
        column_data = {"node": node.getName()}
        for param in node.getParameters().getChildren():
            column_data[param.getName()] = param.getValue(0)

        return column_data