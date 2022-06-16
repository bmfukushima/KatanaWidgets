def getAttr(node, attr, scenegraph_location):
    """ Returns a Katana attribute from the given data

    If an attribute is not found, None is returned

    Args:
        node (Node): Node to resolve at to search for the attribute
        attribute (str): path to the attribute, this is the same path that is provided
            when you drag/drop an attribute into an AttributeSet node
                ie. path.to.some.attribute
        location (str): scenegraph location to search for the attribute on
    """
    runtime = FnGeolib.GetRegisteredRuntimeInstance()
    txn = runtime.createTransaction()
    client = txn.createClient()
    op = Nodes3DAPI.GetOp(txn, node)
    txn.setClientOp(client, op)
    runtime.commit(txn)

    location = client.cookLocation(scenegraph_location)
    attrs = location.getAttrs()
    if attrs:
        attrs.childList()
        attr = attrs.getChildByName(attr)

        if attr:
            return attr
        else:
            raise AttributeError("Invalid attribute location... ", attr)
    else:
        raise AttributeError("Invalid scenegraph location... ", scenegraph_location)

node = NodegraphAPI.GetNode('Transform3D1')
attr = "xform"
scenegraph_location = "/root/world/geo/primitive"

attr = getAttr(node, attr, scenegraph_location)
xform_names = [name for name, attr in attr.childList()]

xform_name = "group"
index = 0
while xform_name in xform_names:
    xform_name = xform_name + str(index)
    index += 1

print(xform_name)















