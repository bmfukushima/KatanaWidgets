import PyFnAttribute

GROUP = "group"
STRING = "string"
FLOAT = "float"
DOUBLE = "double"
INT = "int"

node = NodegraphAPI.GetNode('NetworkMaterialCreate')
location = '/root/materials/NetworkMaterial'
attr_name = "material.layout.PxrTee"

# create client
runtime = FnGeolib.GetRegisteredRuntimeInstance()
txn = runtime.createTransaction()
client = txn.createClient()
op = Nodes3DAPI.GetOp(txn, node)
txn.setClientOp(client, op)
runtime.commit(txn)
location = client.cookLocation(location)

# get output ports
attrs = location.getAttrs()
group_attr = attrs.getChildByName(attr_name)

def getAttrType(attr):
    if type(attr) == PyFnAttribute.GroupAttribute:
        return GROUP
    if type(attr) == PyFnAttribute.StringAttribute:
        return STRING
    if type(attr) == PyFnAttribute.FloatAttribute:
        return FLOAT
    if type(attr) == PyFnAttribute.DoubleAttribute:
        return DOUBLE
    if type(attr) == PyFnAttribute.IntAttribute:
        return INT


def recursiveSearchChild(attr, parent="", attrs_list=None):
    """ Recursively searches the location provided, and returns a map that can
    reproduce the attrs in an OpScript

    Args:
        attr (str)
        parent (str): current location being searched from
        values (list): of the current attrs
            [{"path":"", "type":"", "value":"", {...}]
    """
    if not attrs_list:
        attrs_list = []
    for child in attr.childList():
        child_name = child[0]
        child_attr = child[1]
        attr_type = getAttrType(child_attr)
        attr_path = f"{parent}.{child_name}"
        if attr_type != GROUP:
            attrs_list.append({
                "path":attr_path,
                "type":attr_type,
                "value":child_attr.getValue()
            })
            print(attr_path, attr_type, child_attr.getValue())
        if hasattr(child[1], "childList"):
            print('============'*5)
            #print(values)
            attrs_list += recursiveSearchChild(child[1], f"{parent}.{child_name}")

    return attrs_list

# create OpScript
attr_list = recursiveSearchChild(group_attr, parent=attr_name)
op_script_lua = ""
print('============'*5)
for attr in attr_list:
    path = attr["path"]
    value = attr["value"]
    if attr["type"] == STRING:
        op_script_lua += f"\nInterface.SetAttr(\"{path}\", StringAttribute(\"{value}\"))"
    if attr["type"] == FLOAT:
        op_script_lua += f"\nInterface.SetAttr(\"{path}\", FloatAttribute({value}))"
    if attr["type"] == DOUBLE:
        op_script_lua += f"\nInterface.SetAttr(\"{path}\", DoubleAttribute({value}))"
    if attr["type"] == INT:
        op_script_lua += f"\nInterface.SetAttr(\"{path}\", IntAttribute({value}))"

print (op_script_lua)









