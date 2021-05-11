try:
    import NodegraphAPI
except ModuleNotFoundError:
    pass

# return as
STRING = 0
PARAMETER = 1

# display modes
VARIABLES = 0
OPTIONS = 1

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


# def createNewGSV(gsv):
#     """
#     Creates a new GSV in the project settings.
#
#     Args:
#         gsv (str) the name of the GSV to add
#     """
#     all_variables = getAllGSV()
#     if gsv not in all_variables:
#         variables_group = NodegraphAPI.GetRootNode().getParameter('variables')
#         variable_param = variables_group.createChildGroup(gsv)
#         variable_param.createChildNumber('enable', 1)
#         variable_param.createChildString('value', '')
#         variable_param.createChildStringArray('options', 0)


def addGSVOption(gsv, new_option, row=None):
    """Adds an option to an already existing GSV

    Args:
        gsv (str):
        new_option (str):

    """
    # get gsv param
    gsv_param = getGSVParameter(gsv)

    # get options param
    if 'options' not in [child.getName() for child in gsv_param.getChildren()]:
        options = gsv_param.createChildStringArray('options', 0)
    else:
        options = gsv_param.getChild("options")

    # get all options
    options_list = [gsv_param.getValue(0) for gsv_param in options.getChildren()]

    # create new GSV option
    if new_option not in options_list:
        if not row:
            row = options.getNumChildren()

        new_option_param = options.insertArrayElement(row)
        new_option_param.setValue(str(new_option), 0)

        return new_option_param


def isGSVEvent(arg):
    """Checks an arg from the Katana events/callbacks to determine if a GSV Event change is happening"""
    root_node = NodegraphAPI.GetRootNode()
    if arg[2]['node'] != root_node: return False
    if "param" not in list(arg[2].keys()): return False
    if not arg[2]['param'].getParent(): return False
    if not arg[2]['param'].getParent().getParent(): return False
    if arg[2]['param'].getParent().getParent() != getVariablesParameter(): return False

    return True


def createNewGSV(gsv):
    """
    Creates a new GSV

    Args:
        gsv (str): name of GSV to create

    Returns (str): name of gsv
    """
    # all_variables = getAllGSV()
    # if gsv not in all_variables:
    variables_param = getVariablesParameter()
    gsv_param = variables_param.createChildGroup(gsv)
    gsv_param.createChildNumber('enable', 1)
    gsv_param.createChildString('value', '')
    gsv_param.createChildStringArray('options', 0)
    return gsv_param


def deleteGSVOption(gsv, option):
    # update Katana GSV params
    """note that in the Project Settings tab, the variables has to be
    expanded/collapsed to refresh teh new list"""

    # get attrs
    gsv_options = getGSVOptions(gsv)
    gsv_param = getGSVParameter(gsv)
    gsv_value_param = gsv_param.getChild("value")
    options_param = gsv_param.getChild("options")
    current_gsv = gsv_value_param.getValue(0)

    # if option remove is current, set to first option available
    if current_gsv == option:
        if len(gsv_options) > 0:
            value = gsv_options[0]
        else:
            value = ''
    else:
        value = ''
    gsv_value_param.setValue(value, 0)

    # remove option
    """ No delete function, so need to remove from array and reset"""
    gsv_options.remove(option)
    options_param.resizeArray(len(gsv_options))
    for options_param, optionValue in zip(options_param.getChildren(), gsv_options):
        options_param.setValue(optionValue, 0)


def deleteGSV(gsv):
    gsv_param = getGSVParameter(gsv)
    getVariablesParameter().deleteChild(gsv_param)


def getAllGSV(return_as=STRING):
    """Returns a list of all the possible GSVs in the scene

    Args:
        return_as (TYPE): what type to return the values in the list as

    Returns (list): of strings or parameters depending on the input type provided.  Default is String
    """
    gsv_list = getVariablesParameter().getChildren()
    if return_as == STRING:
        gsv_keys_list = [gsv.getName() for gsv in gsv_list]
    elif return_as == PARAMETER:
        gsv_keys_list = gsv_list
    return gsv_keys_list


def getGSVOptions(gsv, return_as=STRING):
    """Returns a list of all of the options available for the specified GSV

    Args:
        gsv (str): name of GSV to get options for
        return_as (TYPE): what type of list this should return
    Returns (list): of strings or parameters, depending on value given to "return_as" arg
    """
    gsv_param = getGSVParameter(gsv)
    options_list = []
    if gsv_param:
        for child in gsv_param.getChildren():
            if child.getName() == 'options':
                options = gsv_param.getChild("options").getChildren()
                if return_as == STRING:
                    options_list = [child.getValue(0) for child in options]
                elif return_as == PARAMETER:
                    options_list = options
                """
                options_list = []
                    for index in range(options_param.getNumChildren()):
                        option = options_param.getChildByIndex(index).getValue(0)
                        options_list.append(option)
                """

    return options_list


def getVariablesParameter():
    """
    Gets the GSV Variables parameter on the Root Node

    Returns (Parameter):
    """
    return NodegraphAPI.GetRootNode().getParameter('variables')


def getGSVParameter(gsv):
    """
    Gets the GSV parameter from the string provided
    Args:
        gsv (str): name of GSV to get

    Returns (Parameter):

    """
    return getVariablesParameter().getChild(gsv)


def getGSVOptionParameter(gsv, option):
    """
    Gets the parameter that the GSV Option is held on
    Args:
        gsv (str):
        option (str):

    Returns (Parameter):

    """
    gsv_options = getGSVOptions(gsv, return_as=PARAMETER)
    for gsv_option in gsv_options:
        if gsv_option.getValue(0) == option:
            return gsv_option

    return None


def moveGSVtoNewIndex(gsv, index):
    """
    moves the GSV to the index provided

    Args:
        gsv (str):
        index (int):

    Returns:

    """
    variables_param = getVariablesParameter()
    gsv_param = getGSVParameter(gsv)
    variables_param.reorderChild(gsv_param, index)


def moveGSVOptionToNewIndex(gsv, option, index):
    """
    Moves the GSV option parameter provided to a new index

    Args:
        gsv (str): GSV to manipulate
        option (str): Option to move
        index  (int): new index to place the option at

    """

    option_param = getGSVOptionParameter(gsv, option)
    gsv_options_param = getGSVParameter(gsv).getChild("options")
    gsv_options_param.reorderChild(option_param, index)


def renameGSV(gsv_name, new_name):
    """
    Changes the name of a GSV.

    Args:
        gsv_name (gsv): name of GSV to be changed
        new_name (gsv): name to be changed to
    """
    gsv_param = getGSVParameter(gsv_name)
    gsv_param.setName(new_name)


def renameGSVOption(gsv, old_name, new_name):
    """
    Changes the name of a GSV Option
    Args:
        gsv (str): GSV to change option name on
        old_name (str): option name to be changed
        new_name (str): name to be changed to
    """
    option_param = getGSVOptionParameter(gsv, old_name)
    old_index = option_param.getIndex()
    # add new option
    new_option_param = addGSVOption(gsv, new_name)
    moveGSVOptionToNewIndex(gsv, new_name, old_index)

    # delete old option
    deleteGSVOption(gsv, old_name)


def setGSVOption(gsv, option):
    """
    Sets the GSV to the option provided

    Args:
        gsv (str): gsv to set
        option (str): option to set the GSV to
    """
    gsv_param = getGSVParameter(gsv)
    value_param = gsv_param.getChild('value')
    value_param.setValue(str(option), 0)

