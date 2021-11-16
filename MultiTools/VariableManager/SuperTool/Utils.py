import os

from .ItemTypes import (
    BLOCK_ITEM,
    PATTERN_ITEM,
    MASTER_ITEM
)

#from Utils2 import mkdirRecursive


def checkBesterestVersion(main_widget, item=None, item_types=[PATTERN_ITEM, BLOCK_ITEM], should_load=True):
    """
    Gets an items publish directories, and checks to determine if
    it should load a version, or create a new version.

    Args:
        main_widget (VariableManagerMainWidget): The getMainWidget widget...
        item (VariableManagerBrowserItem): item to check for besterest version
        item_types (list): list of ITEM_TYPES to check for besterest version
            by default this is set to all, but can be just a single
                [PATTERN_ITEM] or [BLOCK_ITEM]
        should_load (bool): If the publish loc is found, this determines if this should load or bypass.  The default
            value is true, which will enable loading.
    """
    publish_dir = main_widget.getBasePublishDir(include_node_type=True)
    if not item:
        item = main_widget.currentItem()

    for item_type in item_types:

        # publish dir hack...
        if item_type == MASTER_ITEM:
            item_type = BLOCK_ITEM

        # check default directories
        publish_loc = '{publish_dir}/{item_type}/{unique_hash}/{item_type}/v000'.format(
            publish_dir=publish_dir, item_type=item_type.TYPE, unique_hash=item.getHash()
        )
        resolveBesterestVersion(main_widget, publish_loc, item_type, item=item, should_load=should_load)

        # check patterns on block items
        if item_type in [MASTER_ITEM, BLOCK_ITEM]:
            publish_loc = '{publish_dir}/block/{unique_hash}/pattern/v000'.format(
                publish_dir=publish_dir, unique_hash=item.getHash()
            )
            resolveBesterestVersion(main_widget, publish_loc, PATTERN_ITEM, item=item, should_load=should_load)


def createNodeReference(node_ref, param_name, param=None, node=None, index=-1):
    """
    Creates a new string parameter whose expression value
    returns a reference to a node.

    Args:
        node_ref (node): the node to be referenced
        param_name (str): the name of the new parameter to create
    Kwargs:
        node (node): node to create parameter on if param kwarg
            param is not provided
        param (group param): the param to create the new parameter as
            a child of
    Returns (string param)
    """
    if not param:
        param = node.getParameters()
    new_param = param.createChildString(param_name, '', index)
    new_param.setExpressionFlag(True)
    new_param.setExpression('@%s' % node_ref.getName())
    return new_param


def getMainWidget(widget):
    try:
        name = widget.__name__()
        if name == 'VariableManagerMainWidget':
            return widget
        else:
            return getMainWidget(widget.parent())
    except AttributeError:
        return getMainWidget(widget.parent())


def getNextVersion(location):
    """
    Args:
        location (str): path on disk to to publish dir

    return (str): A string of the next version with the format of v000
    """
    # if it dir doesn't exist return init version
    if not os.path.exists(location): return 'v000'

    # find version
    versions = os.listdir(location)
    if 'live' in versions:
        versions.remove('live')

    if len(versions) == 0:
        next_version = 'v000'
    else:
        versions = [int(version[1:]) for version in versions]
        next_version = 'v'+str(sorted(versions)[-1] + 1).zfill(3)

    return next_version


def resolveBesterestVersion(main_widget, publish_loc, item_type, item, should_load=True):
    """
    Looks at an item and determines if there are versions available to load or not.
    If there are versions available, it will load the besterest version, if there are not
    versions available, it will create the new item.

    Args:
        main_widget (VariableManagerMainWidget): The getMainWidget widget...
        publish_loc (str)
        item_type (ITEM_TYPE)
        item (VariableManagerBrowserItem):
        should_load (bool): determines if this should load or bypass.  The default
            value is true.
    """
    # LOAD
    if os.path.exists(publish_loc) is True:
        # Load besterest version
        if should_load is True:
            main_widget.versions_display_widget.loadBesterestVersion(item, item_type=item_type)

    # CREATE
    else:
        # preflight checks...
        # can prob remove these from individual modules?
        if main_widget.getVariable() == '': return
        if main_widget.getNodeType() == '': return

        # # make live dir
        # live_directory = '/'.join(publish_loc.split('/')[:-1]) + '/live'
        # mkdirRecursive(live_directory)

        # create v000 item
        main_widget.publish_display_widget.publishNewItem(
            item_type=item_type, item=item
        )

        # print ('making dir == ', publish_loc, item_type)
        # make live directory


# HACK
def transferNodeReferences(xfer_from, xfer_to):
    """
    Transfer the node references from one node to another.

    xfer_from (param): the nodeReference param to transfer FROM
    xfer_to  (param): the nodeReference param to transfer TO

    """
    import NodegraphAPI
    # transfer node refs
    for param in xfer_from.getChildren():
        param_name = param.getName()
        node_ref = NodegraphAPI.GetNode(param.getValue(0))
        createNodeReference(
            node_ref, param_name, param=xfer_to
        )


def updateNodeName(node, name=None):
    """
    updates the nodes name.  If a name is provided
    then this will update it to that name.  If not, it will
    merely check to ensure that no funky digits have
    been automatically added to this nodes name...

    Kwarg:
        name (str): name to update to
    """
    # set name
    if name:
        node.setName(str(name))
        node.getParameter('name').setValue(str(name), 0)
    else:
        # update name
        node.setName(node.getName())
        node.getParameter('name').setValue(node.getName(), 0)

# TODO what have I done here...
'''from Katana import Utils
Utils.EventModule.RegisterEventHandler(updateNodeName, '_update_node_name')'''