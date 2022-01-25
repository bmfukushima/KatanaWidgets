node = NodegraphAPI.GetNode('GafferThree')

# We first need to get a hold of the runtime the UI is using
runtime = FnGeolib.GetRegisteredRuntimeInstance()
 
# Transactions are used to batch together actions
txn = runtime.createTransaction()
 
# Make a client, and attach it to an Op in the tree,
# We get the Op from a reference to a Node. 'node' is
# available automatically in a script attached to a button,
# otherwise you would need to use NodegraphAPI.GetNode('MyNodeName')
# or similar to get the node you're interested in.
# The client will see the Scenegraph as it *leaves* this node.
client = txn.createClient()
op = Nodes3DAPI.GetOp(txn, node)
txn.setClientOp(client, op)
runtime.commit(txn)

location = client.cookLocation('/root/world')
location.getAttrs()
location.getPotentialChildren()
# ['geo', 'cam', 'lgt']

def walk(client, path, light_list=None):
    if not light_list:
        light_list = []

    location = client.cookLocation(path)
    location_type = location.getAttrs().getChildByName("type").getValue()
    if location_type == "light":
        light_list.append(path)
    for child in location.getPotentialChildren():
        light_list += walk(client, "{path}/{child}".format(path=path, child=child), light_list)

    return list(set(light_list))
light_list = walk(client, '/root/world')
print(light_list)
# Collect Material assignments




