def hasAttr(node, location, attr_name):
    """ Checks a node/location for a specific attribute name

    Args:
        node (Node): Katana node to search at
        location (str): SceneGraph location to check for attribute
        attr_name (str): Name of attribute to look for
    """
    from Katana import FnGeolib, Nodes3DAPI

    runtime = FnGeolib.GetRegisteredRuntimeInstance()
    txn = runtime.createTransaction()
    client = txn.createClient()
    op = Nodes3DAPI.GetOp(txn, node)
    txn.setClientOp(client, op)
    runtime.commit(txn)
    location = client.cookLocation(location)

    attrs = location.getAttrs()
    attr = attrs.getChildByName(attr_name)

    if attr:
        return True
    return False