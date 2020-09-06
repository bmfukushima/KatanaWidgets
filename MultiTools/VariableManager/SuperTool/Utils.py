import os

from .ItemTypes import (
    BLOCK_ITEM,
    PATTERN_ITEM
)

from Utils2 import mkdirRecursive


def checkBesterestVersion(main_widget, item=None, item_types=[PATTERN_ITEM, BLOCK_ITEM]):
    """
    Gets an items publish directories, and checks to determine if
    it should load a version, or create a new version.

    main_widget (VariableManagerMainWidget): The getMainWidget widget...
    item (VariableManagerBrowserItem): item to check for besterest version
    item_types (list): list of ITEM_TYPES to check for besterest version
        by default this is set to all, but can be just a single
            [PATTERN_ITEM] or [BLOCK_ITEM]
    """

    publish_dir = main_widget.getBasePublishDir(include_node_type=True)
    if not item:
        item = main_widget.getWorkingItem()

    for item_type in item_types:
        # check default directories
        publish_loc = '{publish_dir}/{item_type}/{unique_hash}/{item_type}/v000'.format(
            publish_dir=publish_dir, item_type=item_type.TYPE, unique_hash=item.getHash()
        )
        resolveBesterestVersion(main_widget, publish_loc, item_type, item=item)

        # check patterns on block items
        if item_type == BLOCK_ITEM:
            publish_loc = '{publish_dir}/{item_type}/{unique_hash}/pattern/v000'.format(
                publish_dir=publish_dir, item_type=item_type.TYPE, unique_hash=item.getHash()
            )
            resolveBesterestVersion(main_widget, publish_loc, PATTERN_ITEM, item=item)


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


def goToNode(node, frame=False, nodegraph_panel=None):
    """
    Changes the nodegraph to the selected items node,
    if it is not a group node, then it goes to its parent
    as the parent must be a group... (hopefully)

    Args:
        node (node): node to go to

    Kwargs:
        frame (bool): if True will frame all of the nodes inside of the "node" arg
        nodegraph_panel (nodegraph_panel): if exists, will frame in this node graph, if there is no
            node graph tab.  Then it will search for the default node graph.
    """
    from Katana import UI4
    if not nodegraph_panel:
        nodegraph_panel = UI4.App.Tabs.FindTopTab('Node Graph')
    nodegraph_panel._NodegraphPanel__navigationToolbarCallback(node.getName(), 'useless')

    if frame is True:
        nodegraph_widget = nodegraph_panel.getNodeGraphWidget()
        nodegraph_widget.frameNodes(nodegraph_panel.getEnteredGroupNode().getChildren())


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


def resolveBesterestVersion(main_widget, publish_loc, item_type, item):
    """
    Looks at an item and determines if there are versions available to load or not.
    If there are versions available, it will load the besterest version, if there are not
    versions available, it will create the new item.
    """
    # LOAD
    if os.path.exists(publish_loc) is True:
        # Load besterest version
        main_widget.versions_display_widget.loadBesterestVersion(item, item_type=item_type)

    # CREATE
    else:
        # preflight checks...
        # can prob remove these from individual modules?
        if main_widget.getVariable() == '': return
        if main_widget.getNodeType() == '': return
        main_widget.publish_display_widget.publishNewItem(
            item_type=item_type, item=item
        )
        print ('making dir == ', publish_loc)
        # make live directory
        live_directory = '/'.join(publish_loc.split('/')[:-1]) + '/live'
        mkdirRecursive(live_directory)


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