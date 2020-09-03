import NodegraphAPI


def createNewPattern(pattern, variable, set=False):
    """
    Creates a new variable pattern.  If that pattern
    does not exist for that variable.

    Args:
        pattern (str): the name of the new pattern to be created
        variable (str): the name of the variable to create the pattern under
    Kwargs:
        set (bool): if True will set the new variable to this value.
    """
    variable_param = NodegraphAPI.GetRootNode().getParameter(
        'variables.{variable}'.format(variable=variable)
    )
    # get variables list
    variables_options_param = variable_param.getChild('options')
    variables_list = [child.getValue(0) for child in variables_options_param.getChildren()]

    # create new variable if doesn't exist
    if pattern not in variables_list:
        num_children = variables_options_param.getNumChildren()
        variables_options_param.resizeArray(num_children + 1)
        variables_options_param.getChildByIndex(num_children).setValue(pattern, 0)

    # set pattern
    if set is True:
        variable_param.getChild('value').setValue(pattern, 0)


def createNewGSV(gsv):
    """
    Creates a new GSV in the project settings.

    Args:
        gsv (str) the name of the GSV to add
    """
    all_variables = getAllVariables()
    if gsv not in all_variables:
        variables_group = NodegraphAPI.GetRootNode().getParameter('variables')
        variable_param = variables_group.createChildGroup(gsv)
        variable_param.createChildNumber('enable', 1)
        variable_param.createChildString('value', '')
        variable_param.createChildStringArray('options', 0)


def getAllVariables():
    """
    Gets all of the current graph state variables available

    returns (list): list of variable names as strings
    """
    variables = NodegraphAPI.GetNode('rootNode').getParameter('variables').getChildren()
    variable_list = [x.getName() for x in variables]
    return variable_list
